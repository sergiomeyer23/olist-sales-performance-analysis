"""Gera as saídas estáticas do projeto: figuras PNG/HTML e tabelas CSV.

Uso:
    python gerar_relatorio.py

As figuras alimentam o README e as tabelas servem como resumo executivo,
para quem quiser os números sem rodar o dashboard.
"""

from __future__ import annotations

import sys

from src import analysis as an
from src import config, plots
from src.data_loader import get_data, load_raw


def save_figure(fig, name: str, width: int = 1100, height: int = 560) -> None:
    """Salva a figura em HTML (sempre) e PNG (se o kaleido estiver instalado)."""
    html_path = config.FIGURES_DIR / f"{name}.html"
    fig.write_html(html_path, include_plotlyjs="cdn", full_html=True)

    try:
        fig.write_image(config.FIGURES_DIR / f"{name}.png", width=width, height=height, scale=2)
        print(f"  ✓ {name}.png + .html")
    except Exception:  # kaleido ausente ou falha de renderização
        print(f"  ✓ {name}.html (PNG ignorado: instale 'kaleido' para exportar imagens)")


def save_table(df, name: str) -> None:
    df.to_csv(config.TABLES_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")
    print(f"  ✓ {name}.csv")


def main() -> int:
    config.ensure_output_dirs()

    print("Carregando dados...")
    df = get_data()
    print(f"  {len(df):,} itens | R$ {df['price'].sum():,.2f} de faturamento\n")

    print("Gerando figuras...")
    monthly = an.monthly_revenue(df)
    states = an.revenue_by_state(df)

    save_figure(plots.plot_monthly_revenue(monthly), "01_faturamento_mensal")
    save_figure(plots.plot_growth(monthly), "02_crescimento_mom")
    save_figure(plots.plot_weekday_hour_heatmap(an.revenue_by_weekday_hour(df)), "03_heatmap_compras")
    save_figure(plots.plot_top_categories(an.top_categories(df)), "04_top_categorias")
    save_figure(plots.plot_category_matrix(an.category_matrix(df)), "05_matriz_categorias")
    save_figure(
        plots.plot_state_category_heatmap(
            an.top_categories_by_state(df), states["customer_state"].head(8).tolist()
        ),
        "06_categorias_por_estado",
    )
    save_figure(plots.plot_top_sellers(an.seller_ranking(df)), "07_top_vendedores")
    save_figure(plots.plot_pareto(an.market_concentration(df)), "08_pareto_vendedores")
    save_figure(plots.plot_state_bars(states), "09_faturamento_estado")
    coords = an.state_coordinates(load_raw("geolocation"))
    # Mapa com tiles (interativo, para o dashboard) e versão geo (exportável em PNG).
    save_figure(plots.plot_state_map(states, coords), "10_mapa_brasil")
    save_figure(plots.plot_state_map_static(states, coords), "10b_mapa_brasil_estatico", height=620)
    save_figure(plots.plot_freight_by_region(an.freight_analysis(df)), "11_frete_regiao")
    save_figure(plots.plot_delivery_vs_review(an.delivery_vs_review(df)), "12_prazo_vs_nota")
    save_figure(plots.plot_late_impact(an.late_delivery_impact(df)), "13_impacto_atraso")
    save_figure(plots.plot_review_distribution(an.review_distribution(df)), "14_distribuicao_notas")
    save_figure(plots.plot_delivery_evolution(an.delivery_evolution(df)), "15_evolucao_entrega")
    save_figure(plots.plot_payment_mix(an.payment_profile(df)), "16_meios_pagamento")
    save_figure(plots.plot_installments(an.installments_profile(df)), "17_parcelamento")

    print("\nGerando tabelas...")
    save_table(monthly, "resumo_mensal")
    save_table(an.top_categories(df, top_n=40), "categorias")
    save_table(an.seller_ranking(df, top_n=50), "top_vendedores")
    save_table(states, "estados")
    save_table(an.top_categories_by_state(df), "top5_categorias_por_estado")
    save_table(an.delivery_vs_review(df), "prazo_vs_nota")

    print("\nPrincipais números:")
    kpis = an.kpi_summary(df)
    conc = an.concentration_headline(df)
    late = an.late_delivery_impact(df)
    print(f"  Faturamento............. R$ {kpis['faturamento']:,.2f}")
    print(f"  Pedidos................. {kpis['pedidos']:,.0f}")
    print(f"  Ticket médio............ R$ {kpis['ticket_medio']:.2f}")
    print(f"  Nota média.............. {kpis['nota_media']:.2f}")
    print(f"  Prazo médio de entrega.. {kpis['prazo_medio_dias']:.1f} dias")
    print(f"  Taxa de atraso.......... {kpis['taxa_atraso']:.1%}")
    print(f"  Top 10 vendedores....... {conc['share_top_10_vendedores']:.1%} da receita")
    print(f"  Top 20% vendedores...... {conc['share_top_20pct']:.1%} da receita")
    print(
        "  Nota: no prazo x atrasado... "
        f"{late.loc[late['is_late'] == False, 'nota_media'].iloc[0]:.2f} x "  # noqa: E712
        f"{late.loc[late['is_late'] == True, 'nota_media'].iloc[0]:.2f}"  # noqa: E712
    )

    print(f"\nSaídas em: {config.OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
