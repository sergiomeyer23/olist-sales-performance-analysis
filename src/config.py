"""Central configuration: paths, business rules and display labels.

Manter constantes em um único lugar evita "números mágicos" espalhados
pelo código e facilita mudar uma regra de negócio sem caçar strings.
"""

from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "dados"
PROCESSED_DIR = PROJECT_ROOT / "data_processed"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figuras"
TABLES_DIR = OUTPUT_DIR / "tabelas"

RAW_FILES = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "categories": "product_category_name_translation.csv",
    "geolocation": "olist_geolocation_dataset.csv",
}

# --------------------------------------------------------------------------- #
# Regras de negócio
# --------------------------------------------------------------------------- #
# Consideramos "venda concretizada" apenas pedidos que chegaram ao cliente.
# Pedidos cancelados/indisponíveis inflariam o faturamento sem receita real.
VALID_ORDER_STATUS = ("delivered",)

# A base tem meses de "cauda" com pouquíssimos pedidos (set/2016, dez/2016,
# set-out/2018) que quebram qualquer gráfico de série temporal. Cortamos o
# período para a janela com operação estável.
ANALYSIS_START = "2017-01-01"
ANALYSIS_END = "2018-08-31"

# Faturamento = soma do preço dos itens (frete é analisado à parte).
REVENUE_COLUMN = "price"

# --------------------------------------------------------------------------- #
# Labels de exibição
# --------------------------------------------------------------------------- #
WEEKDAY_LABELS_PT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

PAYMENT_LABELS_PT = {
    "credit_card": "Cartão de crédito",
    "boleto": "Boleto",
    "voucher": "Voucher",
    "debit_card": "Cartão de débito",
    "not_defined": "Não informado",
}

# Tradução das categorias mais relevantes para leitura em PT-BR nos gráficos.
CATEGORY_LABELS_PT = {
    "health_beauty": "Saúde e beleza",
    "watches_gifts": "Relógios e presentes",
    "bed_bath_table": "Cama, mesa e banho",
    "sports_leisure": "Esporte e lazer",
    "computers_accessories": "Informática e acessórios",
    "furniture_decor": "Móveis e decoração",
    "housewares": "Utilidades domésticas",
    "cool_stuff": "Diversos",
    "auto": "Automotivo",
    "garden_tools": "Jardinagem",
    "toys": "Brinquedos",
    "baby": "Bebê",
    "perfumery": "Perfumaria",
    "telephony": "Telefonia",
    "office_furniture": "Móveis de escritório",
    "musical_instruments": "Instrumentos musicais",
    "electronics": "Eletrônicos",
    "stationery": "Papelaria",
    "computers": "Computadores",
    "pet_shop": "Pet shop",
    "luggage_accessories": "Malas e acessórios",
    "construction_tools_construction": "Ferramentas e construção",
    "small_appliances": "Eletroportáteis",
    "home_appliances": "Eletrodomésticos",
    "home_construction": "Casa e construção",
    "fashion_bags_accessories": "Moda: bolsas e acessórios",
    "air_conditioning": "Ar-condicionado",
    "consoles_games": "Consoles e games",
    "food_drink": "Alimentos e bebidas",
    "books_general_interest": "Livros",
    "office_furniture": "Móveis de escritório",
    "audio": "Áudio",
    "home_confort": "Conforto para casa",
    "uncategorized": "Sem categoria",
}

REGION_BY_STATE = {
    "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte",
    "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste",
    "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste",
    "MS": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}

# Paleta usada em todos os gráficos (consistência visual do dashboard).
COLOR_PRIMARY = "#1f6feb"
COLOR_SECONDARY = "#f2a900"
COLOR_POSITIVE = "#2ea043"
COLOR_NEGATIVE = "#d1373b"
COLOR_SEQUENCE = [
    "#1f6feb", "#f2a900", "#2ea043", "#d1373b", "#8957e5",
    "#0d9488", "#e36209", "#6e7781", "#bf3989", "#1b7c83",
]


def ensure_output_dirs() -> None:
    """Cria as pastas de saída se ainda não existirem."""
    for directory in (PROCESSED_DIR, OUTPUT_DIR, FIGURES_DIR, TABLES_DIR):
        directory.mkdir(parents=True, exist_ok=True)
