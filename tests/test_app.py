"""Testes do dashboard usando o AppTest nativo do Streamlit.

Executam o app de verdade (sem browser) e verificam que ele não quebra —
inclusive com filtros restritivos, que já causaram um IndexError quando um
recorte não tinha nenhum pedido atrasado.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP_TIMEOUT = 400
# Caminho absoluto para o teste rodar de qualquer diretório.
APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")


def run_app() -> AppTest:
    return AppTest.from_file(APP_PATH, default_timeout=APP_TIMEOUT).run()


def test_app_carrega_sem_erros():
    at = run_app()
    assert not at.exception
    assert not at.error


def test_estrutura_do_dashboard():
    at = run_app()
    assert len(at.tabs) == 6
    # 8 KPIs no topo + métricas de concentração e da aba de dados.
    assert len(at.metric) >= 12
    labels = [m.label for m in at.metric]
    for expected in ["Faturamento", "Pedidos", "Ticket médio", "Nota média"]:
        assert expected in labels


@pytest.mark.parametrize(
    "regions,categories",
    [
        (["Norte"], ["Livros"]),      # recorte minúsculo: pode não ter atrasos
        (["Nordeste"], []),
        ([], []),                      # nenhuma região marcada
    ],
)
def test_filtros_restritivos_nao_quebram(regions, categories):
    at = run_app()
    at.multiselect[0].set_value(regions).run()
    at.multiselect[1].set_value(categories).run()
    assert not at.exception, [e.value for e in at.exception]


def test_filtro_de_preco_nao_quebra():
    at = run_app()
    at.slider[0].set_value((0, 25)).run()
    assert not at.exception, [e.value for e in at.exception]
