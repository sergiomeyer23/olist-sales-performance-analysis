"""Funções de análise: cada uma responde a uma pergunta de negócio.

Todas recebem a tabela analítica (ver ``src.data_loader``) e devolvem um
DataFrame pronto para virar gráfico ou tabela. Nenhuma função imprime nada
nem desenha nada — assim o mesmo cálculo alimenta o dashboard, o relatório
e eventuais testes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import config


# --------------------------------------------------------------------------- #
# Visão geral
# --------------------------------------------------------------------------- #
def kpi_summary(df: pd.DataFrame) -> dict[str, float]:
    """Indicadores de topo do dashboard."""
    orders = df["order_id"].nunique()
    revenue = df["price"].sum()

    return {
        "faturamento": revenue,
        "pedidos": orders,
        "itens_vendidos": len(df),
        "ticket_medio": revenue / orders if orders else 0.0,
        "clientes_unicos": df["customer_unique_id"].nunique(),
        "vendedores_ativos": df["seller_id"].nunique(),
        "nota_media": df["review_score"].mean(),
        "prazo_medio_dias": df["delivery_days"].mean(),
        "taxa_atraso": df.drop_duplicates("order_id")["is_late"].mean(),
        "frete_medio": df["freight_value"].mean(),
        "percentual_frete": df["freight_value"].sum() / (revenue + df["freight_value"].sum()),
    }


def monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Série mensal de faturamento, pedidos e ticket médio, com crescimento MoM."""
    monthly = (
        df.groupby("order_month")
        .agg(
            faturamento=("price", "sum"),
            pedidos=("order_id", "nunique"),
            itens=("order_id", "size"),
        )
        .reset_index()
    )

    monthly["ticket_medio"] = monthly["faturamento"] / monthly["pedidos"]
    monthly["crescimento_mom"] = monthly["faturamento"].pct_change()
    # Média móvel de 3 meses suaviza o ruído e mostra a tendência.
    monthly["media_movel_3m"] = monthly["faturamento"].rolling(3).mean()

    return monthly


def revenue_by_weekday_hour(df: pd.DataFrame) -> pd.DataFrame:
    """Matriz dia da semana x hora da compra — mostra quando o cliente compra."""
    orders = df.drop_duplicates("order_id")

    heat = (
        orders.groupby(["order_weekday", "order_hour"])
        .size()
        .reset_index(name="pedidos")
    )
    heat["weekday_label"] = heat["order_weekday"].map(
        dict(enumerate(config.WEEKDAY_LABELS_PT))
    )

    return heat


# --------------------------------------------------------------------------- #
# Produtos e categorias
# --------------------------------------------------------------------------- #
def top_categories(df: pd.DataFrame, top_n: int = 12) -> pd.DataFrame:
    """Ranking de categorias por faturamento, com nota média e preço médio."""
    grouped = (
        df.groupby("category_pt")
        .agg(
            faturamento=("price", "sum"),
            itens=("price", "size"),
            preco_medio=("price", "mean"),
            nota_media=("review_score", "mean"),
            frete_medio=("freight_value", "mean"),
        )
        .reset_index()
        .sort_values("faturamento", ascending=False)
    )

    grouped["participacao"] = grouped["faturamento"] / grouped["faturamento"].sum()
    return grouped.head(top_n)


def category_matrix(df: pd.DataFrame, min_items: int = 300) -> pd.DataFrame:
    """Categorias em 2 eixos (volume x nota) para achar oportunidades e problemas.

    ``min_items`` evita que categorias minúsculas com 5 vendas apareçam como
    "melhor nota do site".
    """
    grouped = (
        df.groupby("category_pt")
        .agg(
            faturamento=("price", "sum"),
            itens=("price", "size"),
            nota_media=("review_score", "mean"),
            preco_medio=("price", "mean"),
            taxa_atraso=("is_late", "mean"),
        )
        .reset_index()
    )

    return grouped[grouped["itens"] >= min_items].sort_values(
        "faturamento", ascending=False
    )


def top_categories_by_state(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """Top N categorias de cada estado (pergunta original do projeto)."""
    grouped = (
        df.groupby(["customer_state", "category_pt"])["price"]
        .sum()
        .reset_index(name="faturamento")
        .sort_values(["customer_state", "faturamento"], ascending=[True, False])
    )

    grouped["ranking"] = grouped.groupby("customer_state")["faturamento"].rank(
        method="first", ascending=False
    ).astype(int)

    return grouped[grouped["ranking"] <= top_n].reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Vendedores
# --------------------------------------------------------------------------- #
def seller_ranking(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """Ranking de vendedores com métricas de qualidade, não só de volume."""
    grouped = (
        df.groupby("seller_id")
        .agg(
            faturamento=("price", "sum"),
            pedidos=("order_id", "nunique"),
            itens=("price", "size"),
            nota_media=("review_score", "mean"),
            prazo_medio=("delivery_days", "mean"),
            taxa_atraso=("is_late", "mean"),
            estado=("seller_state", "first"),
            categorias=("category_pt", "nunique"),
        )
        .reset_index()
        .sort_values("faturamento", ascending=False)
    )

    grouped["ticket_medio"] = grouped["faturamento"] / grouped["pedidos"]
    grouped["participacao"] = grouped["faturamento"] / grouped["faturamento"].sum()
    # Identificador curto para caber no eixo dos gráficos.
    grouped["seller_label"] = grouped["seller_id"].str[:8]

    return grouped.head(top_n)


def market_concentration(df: pd.DataFrame) -> pd.DataFrame:
    """Curva de Pareto: quanto do faturamento vem dos maiores vendedores."""
    revenue = (
        df.groupby("seller_id")["price"].sum().sort_values(ascending=False).reset_index()
    )

    revenue["acumulado"] = revenue["price"].cumsum()
    revenue["participacao_acumulada"] = revenue["acumulado"] / revenue["price"].sum()
    revenue["percentual_vendedores"] = (revenue.index + 1) / len(revenue)

    return revenue


def concentration_headline(df: pd.DataFrame) -> dict[str, float]:
    """Resume a concentração em números citáveis (para README e dashboard)."""
    pareto = market_concentration(df)
    total_sellers = len(pareto)

    def share_of_top(pct: float) -> float:
        cutoff = max(1, int(round(total_sellers * pct)))
        return pareto["price"].head(cutoff).sum() / pareto["price"].sum()

    # Quantos vendedores são necessários para chegar a 80% do faturamento.
    sellers_for_80 = int((pareto["participacao_acumulada"] < 0.80).sum() + 1)

    return {
        "vendedores_total": total_sellers,
        "share_top_10_vendedores": pareto["price"].head(10).sum() / pareto["price"].sum(),
        "share_top_1pct": share_of_top(0.01),
        "share_top_20pct": share_of_top(0.20),
        "vendedores_para_80pct": sellers_for_80,
        "percentual_vendedores_para_80pct": sellers_for_80 / total_sellers,
    }


# --------------------------------------------------------------------------- #
# Geografia
# --------------------------------------------------------------------------- #
def revenue_by_state(df: pd.DataFrame) -> pd.DataFrame:
    """Desempenho por UF do cliente: receita, ticket, prazo, nota e frete."""
    grouped = (
        df.groupby("customer_state")
        .agg(
            faturamento=("price", "sum"),
            pedidos=("order_id", "nunique"),
            clientes=("customer_unique_id", "nunique"),
            nota_media=("review_score", "mean"),
            prazo_medio=("delivery_days", "mean"),
            taxa_atraso=("is_late", "mean"),
            frete_medio=("freight_value", "mean"),
        )
        .reset_index()
        .sort_values("faturamento", ascending=False)
    )

    grouped["ticket_medio"] = grouped["faturamento"] / grouped["pedidos"]
    grouped["participacao"] = grouped["faturamento"] / grouped["faturamento"].sum()
    grouped["participacao_acumulada"] = grouped["participacao"].cumsum()
    grouped["regiao"] = grouped["customer_state"].map(config.REGION_BY_STATE)
    # Peso do frete sobre o preço: mostra o custo de vender longe do Sudeste.
    grouped["frete_sobre_preco"] = grouped["frete_medio"] / (
        grouped["faturamento"] / grouped["pedidos"]
    )

    return grouped


def revenue_by_region(df: pd.DataFrame) -> pd.DataFrame:
    """Mesma leitura, agregada por região — menos ruído que 27 UFs."""
    grouped = (
        df.groupby("customer_region")
        .agg(
            faturamento=("price", "sum"),
            pedidos=("order_id", "nunique"),
            nota_media=("review_score", "mean"),
            prazo_medio=("delivery_days", "mean"),
            frete_medio=("freight_value", "mean"),
        )
        .reset_index()
        .sort_values("faturamento", ascending=False)
    )

    grouped["participacao"] = grouped["faturamento"] / grouped["faturamento"].sum()
    return grouped


def state_coordinates(geolocation: pd.DataFrame) -> pd.DataFrame:
    """Centroide aproximado de cada UF a partir do próprio dataset de CEPs.

    Usar os dados que já temos evita depender de um shapefile externo.
    A mediana (em vez da média) protege contra coordenadas erradas na base.
    """
    clean = geolocation[
        geolocation["geolocation_lat"].between(-34, 6)
        & geolocation["geolocation_lng"].between(-74, -34)
    ]

    return (
        clean.groupby("geolocation_state")
        .agg(lat=("geolocation_lat", "median"), lon=("geolocation_lng", "median"))
        .reset_index()
        .rename(columns={"geolocation_state": "customer_state"})
    )


# --------------------------------------------------------------------------- #
# Entrega e satisfação
# --------------------------------------------------------------------------- #
def delivery_vs_review(df: pd.DataFrame) -> pd.DataFrame:
    """Nota média por faixa de prazo de entrega — o insight mais forte da base."""
    orders = df.drop_duplicates("order_id").dropna(subset=["review_score"])

    bins = [0, 3, 7, 14, 21, 30, np.inf]
    labels = ["até 3 dias", "4 a 7", "8 a 14", "15 a 21", "22 a 30", "31+ dias"]
    orders = orders.assign(
        faixa_prazo=pd.cut(orders["delivery_days"], bins=bins, labels=labels, right=True)
    )

    grouped = (
        orders.groupby("faixa_prazo", observed=True)
        .agg(
            nota_media=("review_score", "mean"),
            pedidos=("order_id", "size"),
            perc_nota_1_2=("review_score", lambda s: (s <= 2).mean()),
            perc_nota_5=("review_score", lambda s: (s == 5).mean()),
        )
        .reset_index()
    )

    return grouped


def late_delivery_impact(df: pd.DataFrame) -> pd.DataFrame:
    """Compara pedidos no prazo x atrasados (nota, % detratores, volume)."""
    orders = df.drop_duplicates("order_id").dropna(subset=["review_score"])

    grouped = (
        orders.groupby("is_late")
        .agg(
            nota_media=("review_score", "mean"),
            pedidos=("order_id", "size"),
            perc_nota_1=("review_score", lambda s: (s == 1).mean()),
            perc_nota_1_2=("review_score", lambda s: (s <= 2).mean()),
            perc_nota_5=("review_score", lambda s: (s == 5).mean()),
        )
        .reset_index()
    )

    grouped["situacao"] = grouped["is_late"].map({False: "No prazo", True: "Atrasado"})
    grouped["participacao"] = grouped["pedidos"] / grouped["pedidos"].sum()

    return grouped


def review_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Distribuição das notas de 1 a 5."""
    orders = df.drop_duplicates("order_id").dropna(subset=["review_score"])

    grouped = (
        orders["review_score"].value_counts().sort_index().reset_index()
    )
    grouped.columns = ["nota", "pedidos"]
    grouped["participacao"] = grouped["pedidos"] / grouped["pedidos"].sum()

    return grouped


def delivery_evolution(df: pd.DataFrame) -> pd.DataFrame:
    """Prazo médio e taxa de atraso mês a mês — a operação melhorou?"""
    orders = df.drop_duplicates("order_id")

    return (
        orders.groupby("order_month")
        .agg(
            prazo_medio=("delivery_days", "mean"),
            taxa_atraso=("is_late", "mean"),
            nota_media=("review_score", "mean"),
            pedidos=("order_id", "size"),
        )
        .reset_index()
    )


# --------------------------------------------------------------------------- #
# Pagamentos e frete
# --------------------------------------------------------------------------- #
def payment_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Uso de cada meio de pagamento e o ticket médio associado."""
    orders = df.drop_duplicates("order_id").dropna(subset=["payment_type_pt"])

    grouped = (
        orders.groupby("payment_type_pt")
        .agg(
            pedidos=("order_id", "size"),
            valor_medio=("payment_value", "mean"),
            parcelas_medias=("payment_installments", "mean"),
        )
        .reset_index()
        .sort_values("pedidos", ascending=False)
    )

    grouped["participacao"] = grouped["pedidos"] / grouped["pedidos"].sum()
    return grouped


def installments_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Ticket médio por número de parcelas (só cartão de crédito)."""
    orders = df.drop_duplicates("order_id")
    credit = orders[orders["payment_type"] == "credit_card"].copy()

    credit["faixa_parcelas"] = pd.cut(
        credit["payment_installments"],
        bins=[0, 1, 2, 3, 6, 10, 24],
        labels=["À vista", "2x", "3x", "4-6x", "7-10x", "11x+"],
    )

    grouped = (
        credit.groupby("faixa_parcelas", observed=True)
        .agg(pedidos=("order_id", "size"), valor_medio=("payment_value", "mean"))
        .reset_index()
    )

    grouped["participacao"] = grouped["pedidos"] / grouped["pedidos"].sum()
    return grouped


def freight_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Peso do frete por região e efeito da venda interestadual."""
    grouped = (
        df.groupby(["customer_region", "is_interstate"])
        .agg(
            frete_medio=("freight_value", "mean"),
            preco_medio=("price", "mean"),
            prazo_medio=("delivery_days", "mean"),
            itens=("price", "size"),
        )
        .reset_index()
    )

    grouped["frete_sobre_preco"] = grouped["frete_medio"] / grouped["preco_medio"]
    grouped["tipo_venda"] = grouped["is_interstate"].map(
        {False: "Mesmo estado", True: "Interestadual"}
    )

    return grouped
