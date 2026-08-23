"""Carga e limpeza dos dados brutos do Olist.

Fluxo:
    CSVs brutos (dados/)  ->  limpeza  ->  tabela analítica única (1 linha = 1 item)
                                       ->  cache em Parquet (data_processed/)

A tabela analítica é o "coração" do projeto: todas as análises partem dela,
garantindo que faturamento, prazos e notas sejam sempre calculados do mesmo jeito.
"""

from __future__ import annotations

import pandas as pd

from src import config

# --------------------------------------------------------------------------- #
# Leitura bruta
# --------------------------------------------------------------------------- #
DATE_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "reviews": ["review_creation_date", "review_answer_timestamp"],
}


def load_raw(name: str) -> pd.DataFrame:
    """Lê um CSV bruto pelo apelido definido em ``config.RAW_FILES``."""
    if name not in config.RAW_FILES:
        raise KeyError(f"Dataset desconhecido: {name!r}. Opções: {list(config.RAW_FILES)}")

    path = config.RAW_DATA_DIR / config.RAW_FILES[name]
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {path}\n"
            "Baixe o dataset do Kaggle (Brazilian E-Commerce Public Dataset by Olist) "
            "e coloque os CSVs na pasta dados/."
        )

    return pd.read_csv(path, parse_dates=DATE_COLUMNS.get(name))


# --------------------------------------------------------------------------- #
# Limpeza por tabela
# --------------------------------------------------------------------------- #
def clean_orders(orders: pd.DataFrame) -> pd.DataFrame:
    """Mantém apenas pedidos entregues e cria as métricas de prazo de entrega."""
    df = orders[orders["order_status"].isin(config.VALID_ORDER_STATUS)].copy()

    # Sem data de entrega não dá para medir prazo: são poucos casos, removemos.
    df = df.dropna(subset=["order_delivered_customer_date"])

    # Dias entre a compra e a entrega ao cliente (experiência real do consumidor).
    df["delivery_days"] = (
        df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
    ).dt.total_seconds() / 86_400

    # Diferença entre o prometido e o realizado.
    # Positivo = entregou antes do prazo; negativo = atrasou.
    df["delivery_vs_estimate_days"] = (
        df["order_estimated_delivery_date"] - df["order_delivered_customer_date"]
    ).dt.total_seconds() / 86_400

    df["is_late"] = df["delivery_vs_estimate_days"] < 0

    # Recortes de tempo usados nas análises de sazonalidade.
    purchase = df["order_purchase_timestamp"]
    df["order_date"] = purchase.dt.normalize()
    df["order_year"] = purchase.dt.year
    df["order_month"] = purchase.dt.to_period("M").dt.to_timestamp()
    df["order_weekday"] = purchase.dt.weekday  # 0 = segunda
    df["order_hour"] = purchase.dt.hour

    return df


def clean_order_items(items: pd.DataFrame) -> pd.DataFrame:
    """Remove itens com preço inválido e cria o valor total do item."""
    df = items[items["price"] > 0].copy()
    df["item_total"] = df["price"] + df["freight_value"]
    # Peso do frete no valor pago pelo item — usado na análise de logística.
    df["freight_ratio"] = df["freight_value"] / df["item_total"]
    return df


def clean_products(products: pd.DataFrame, categories: pd.DataFrame) -> pd.DataFrame:
    """Traduz a categoria e padroniza colunas com erro de digitação na origem."""
    df = products.rename(
        columns={
            # O dataset original vem com "lenght" (typo) em duas colunas.
            "product_name_lenght": "product_name_length",
            "product_description_lenght": "product_description_length",
        }
    ).copy()

    df = df.merge(categories, on="product_category_name", how="left")

    # ~1,6k produtos não têm categoria: viram "sem_categoria" em vez de sumirem.
    df["product_category_name_english"] = df["product_category_name_english"].fillna(
        "uncategorized"
    )
    df["category_pt"] = (
        df["product_category_name_english"]
        .map(config.CATEGORY_LABELS_PT)
        .fillna(df["product_category_name_english"].str.replace("_", " ").str.capitalize())
    )

    # Volume da embalagem em litros — proxy de "produto grande" no estudo de frete.
    df["product_volume_l"] = (
        df["product_length_cm"] * df["product_height_cm"] * df["product_width_cm"]
    ) / 1000

    return df


def clean_payments(payments: pd.DataFrame) -> pd.DataFrame:
    """Agrega os pagamentos por pedido (um pedido pode ter vários pagamentos)."""
    df = payments.copy()
    df["payment_type_pt"] = df["payment_type"].map(config.PAYMENT_LABELS_PT).fillna(
        df["payment_type"]
    )

    # Forma de pagamento "principal" = a de maior valor dentro do pedido.
    main_payment = (
        df.sort_values("payment_value", ascending=False)
        .groupby("order_id", as_index=False)
        .first()[["order_id", "payment_type", "payment_type_pt", "payment_installments"]]
    )

    totals = df.groupby("order_id", as_index=False).agg(
        payment_value=("payment_value", "sum"),
        payment_methods_used=("payment_type", "nunique"),
    )

    return main_payment.merge(totals, on="order_id", how="left")


def clean_reviews(reviews: pd.DataFrame) -> pd.DataFrame:
    """Fica com uma avaliação por pedido (a mais recente) e marca se houve comentário."""
    df = reviews.sort_values("review_creation_date").drop_duplicates(
        subset="order_id", keep="last"
    ).copy()

    df["has_comment"] = df["review_comment_message"].notna()
    df["review_response_days"] = (
        df["review_answer_timestamp"] - df["review_creation_date"]
    ).dt.total_seconds() / 86_400

    return df[
        ["order_id", "review_score", "has_comment", "review_response_days"]
    ]


# --------------------------------------------------------------------------- #
# Tabela analítica
# --------------------------------------------------------------------------- #
def build_analytical_table() -> pd.DataFrame:
    """Junta tudo em uma tabela onde cada linha é um item vendido e entregue."""
    orders = clean_orders(load_raw("orders"))
    items = clean_order_items(load_raw("order_items"))
    products = clean_products(load_raw("products"), load_raw("categories"))
    payments = clean_payments(load_raw("payments"))
    reviews = clean_reviews(load_raw("reviews"))
    customers = load_raw("customers")
    sellers = load_raw("sellers")

    df = (
        items.merge(orders, on="order_id", how="inner")
        .merge(customers, on="customer_id", how="left")
        .merge(sellers, on="seller_id", how="left")
        .merge(
            products[
                [
                    "product_id",
                    "product_category_name_english",
                    "category_pt",
                    "product_weight_g",
                    "product_volume_l",
                    "product_photos_qty",
                ]
            ],
            on="product_id",
            how="left",
        )
        .merge(payments, on="order_id", how="left")
        .merge(reviews, on="order_id", how="left")
    )

    # Recorte temporal com operação estável (ver justificativa em config.py).
    mask = (df["order_purchase_timestamp"] >= config.ANALYSIS_START) & (
        df["order_purchase_timestamp"] <= f"{config.ANALYSIS_END} 23:59:59"
    )
    df = df.loc[mask].copy()

    df["customer_region"] = df["customer_state"].map(config.REGION_BY_STATE)
    df["seller_region"] = df["seller_state"].map(config.REGION_BY_STATE)
    # Venda interestadual costuma significar frete mais caro e prazo maior.
    df["is_interstate"] = df["customer_state"] != df["seller_state"]
    df["weekday_label"] = df["order_weekday"].map(
        dict(enumerate(config.WEEKDAY_LABELS_PT))
    )

    return df.reset_index(drop=True)


def get_data(use_cache: bool = True) -> pd.DataFrame:
    """Devolve a tabela analítica, usando cache em Parquet quando disponível.

    Reconstruir a tabela custa ~10s; ler o Parquet é quase instantâneo, o que
    deixa o dashboard rápido no primeiro carregamento.
    """
    config.ensure_output_dirs()
    cache_path = config.PROCESSED_DIR / "olist_analytical_table.parquet"

    if use_cache and cache_path.exists():
        return pd.read_parquet(cache_path)

    df = build_analytical_table()
    try:
        df.to_parquet(cache_path, index=False)
    except (ImportError, ValueError):  # pyarrow ausente: segue sem cache
        pass

    return df


if __name__ == "__main__":
    table = get_data(use_cache=False)
    print(f"Tabela analítica: {table.shape[0]:,} linhas x {table.shape[1]} colunas")
    print(f"Período: {table['order_date'].min():%d/%m/%Y} a {table['order_date'].max():%d/%m/%Y}")
    print(f"Faturamento total: R$ {table['price'].sum():,.2f}")
