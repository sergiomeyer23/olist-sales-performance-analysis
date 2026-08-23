"""Testes de sanidade das análises.

Não testam "o número exato", e sim as regras que não podem quebrar quando o
código muda: granularidade dos joins, faixas de valores plausíveis e
coerência entre métricas. Rode com:

    pytest -q
"""

from __future__ import annotations

import pandas as pd
import pytest

from src import analysis as an
from src.data_loader import get_data


@pytest.fixture(scope="module")
def df() -> pd.DataFrame:
    return get_data()


# --------------------------------------------------------------------------- #
# Integridade da tabela analítica
# --------------------------------------------------------------------------- #
def test_tabela_nao_esta_vazia(df):
    assert len(df) > 100_000


def test_apenas_pedidos_entregues(df):
    assert set(df["order_status"].unique()) == {"delivered"}


def test_periodo_dentro_do_recorte(df):
    assert df["order_purchase_timestamp"].min() >= pd.Timestamp("2017-01-01")
    assert df["order_purchase_timestamp"].max() <= pd.Timestamp("2018-09-01")


def test_joins_nao_duplicaram_itens(df):
    """Cada (pedido, item) deve aparecer uma única vez após todos os merges."""
    assert not df.duplicated(subset=["order_id", "order_item_id"]).any()


def test_colunas_criticas_sem_nulos(df):
    for column in ["order_id", "price", "customer_state", "delivery_days"]:
        assert df[column].notna().all(), f"Coluna {column} tem nulos"


def test_precos_positivos(df):
    assert (df["price"] > 0).all()
    assert (df["freight_value"] >= 0).all()


def test_prazo_de_entrega_plausivel(df):
    """Entrega não pode ser negativa nem levar mais de um ano."""
    assert df["delivery_days"].min() >= 0
    assert df["delivery_days"].max() < 365


# --------------------------------------------------------------------------- #
# Coerência das métricas
# --------------------------------------------------------------------------- #
def test_kpis_em_faixas_esperadas(df):
    kpis = an.kpi_summary(df)

    assert kpis["faturamento"] > 10_000_000
    assert 50 < kpis["ticket_medio"] < 500
    assert 1 <= kpis["nota_media"] <= 5
    assert 0 <= kpis["taxa_atraso"] <= 1
    # Não podem existir mais clientes únicos do que pedidos.
    assert kpis["clientes_unicos"] <= kpis["pedidos"]


def test_faturamento_mensal_bate_com_o_total(df):
    monthly = an.monthly_revenue(df)
    assert monthly["faturamento"].sum() == pytest.approx(df["price"].sum(), rel=1e-9)


def test_participacao_dos_estados_soma_um(df):
    states = an.revenue_by_state(df)
    assert states["participacao"].sum() == pytest.approx(1.0, abs=1e-9)


def test_pareto_e_monotonico(df):
    """A curva acumulada só pode subir e deve terminar em 100%."""
    pareto = an.market_concentration(df)
    assert pareto["participacao_acumulada"].is_monotonic_increasing
    assert pareto["participacao_acumulada"].iloc[-1] == pytest.approx(1.0, abs=1e-9)


def test_top_categorias_esta_ordenado(df):
    categories = an.top_categories(df, top_n=10)
    assert categories["faturamento"].is_monotonic_decreasing


def test_top5_por_estado_respeita_o_limite(df):
    top5 = an.top_categories_by_state(df, top_n=5)
    assert top5.groupby("customer_state").size().max() <= 5


# --------------------------------------------------------------------------- #
# Insight central: atraso derruba a nota
# --------------------------------------------------------------------------- #
def test_atraso_reduz_a_nota(df):
    late = an.late_delivery_impact(df)

    on_time = late.loc[~late["is_late"], "nota_media"].iloc[0]
    delayed = late.loc[late["is_late"], "nota_media"].iloc[0]

    assert on_time > delayed
    # A diferença é grande o bastante para ser um insight, não ruído.
    assert on_time - delayed > 1.0


def test_nota_cai_conforme_o_prazo_aumenta(df):
    delivery = an.delivery_vs_review(df)
    scores = delivery["nota_media"].tolist()
    assert scores == sorted(scores, reverse=True)


def test_distribuicao_de_notas_cobre_todas_as_estrelas(df):
    reviews = an.review_distribution(df)
    assert set(reviews["nota"]) == {1, 2, 3, 4, 5}
    assert reviews["participacao"].sum() == pytest.approx(1.0, abs=1e-9)
