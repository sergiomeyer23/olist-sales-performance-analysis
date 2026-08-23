"""Dashboard interativo de performance de vendas do Olist.

Executar com:
    streamlit run app.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src import analysis as an
from src import config, plots
from src.data_loader import get_data, load_raw

st.set_page_config(
    page_title="Olist | Performance de Vendas",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Pequenos ajustes visuais para o dashboard não parecer um app padrão.
st.markdown(
    """
    <style>
      .block-container {padding-top: 2.2rem; padding-bottom: 3rem;}
      [data-testid="stMetricValue"] {font-size: 1.6rem;}
      [data-testid="stMetricLabel"] {color: #6e7781;}
      h1, h2, h3 {letter-spacing: -0.01em;}
      .insight-box {
        background: #f3f7ff; border-left: 4px solid #1f6feb;
        padding: 0.9rem 1.1rem; border-radius: 6px; margin: 0.6rem 0 1.2rem 0;
        font-size: 0.94rem; line-height: 1.55;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------- #
# Carga de dados (em cache para não reprocessar a cada interação)
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner="Carregando dados do Olist...")
def load_dataset() -> pd.DataFrame:
    return get_data()


@st.cache_data(show_spinner=False)
def load_coordinates() -> pd.DataFrame:
    return an.state_coordinates(load_raw("geolocation"))


def insight(text: str) -> None:
    """Caixa de destaque com a leitura de negócio do gráfico."""
    st.markdown(f"<div class='insight-box'>{text}</div>", unsafe_allow_html=True)


def first_value(df: pd.DataFrame, mask: pd.Series, column: str, default=None):
    """Primeiro valor de uma coluna sob um filtro, ou ``default`` se não houver.

    Necessário porque filtros muito restritivos podem gerar recortes sem
    nenhum pedido atrasado (ou sem nenhum no prazo) — nesse caso o app deve
    seguir funcionando em vez de quebrar.
    """
    subset = df.loc[mask, column]
    return subset.iloc[0] if len(subset) else default


df_full = load_dataset()

# --------------------------------------------------------------------------- #
# Sidebar: filtros globais
# --------------------------------------------------------------------------- #
st.sidebar.title("📦 Olist Analytics")
st.sidebar.caption("Dados de e-commerce brasileiro | 2017–2018")
st.sidebar.markdown("---")
st.sidebar.subheader("Filtros")

min_date = df_full["order_date"].min().date()
max_date = df_full["order_date"].max().date()

date_range = st.sidebar.date_input(
    "Período da compra",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    format="DD/MM/YYYY",
)

regions = sorted(df_full["customer_region"].dropna().unique())
selected_regions = st.sidebar.multiselect("Região do cliente", regions, default=regions)

categories = sorted(df_full["category_pt"].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "Categorias (vazio = todas)", categories, default=[]
)

price_min, price_max = st.sidebar.slider(
    "Faixa de preço do item (R$)",
    min_value=0,
    max_value=1000,
    value=(0, 1000),
    step=25,
    help="Itens acima de R$ 1.000 permanecem incluídos quando o limite está no máximo.",
)

# Aplicação dos filtros -------------------------------------------------------
df = df_full.copy()

if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
    df = df[
        (df["order_date"] >= pd.Timestamp(start)) & (df["order_date"] <= pd.Timestamp(end))
    ]

if selected_regions:
    df = df[df["customer_region"].isin(selected_regions)]

if selected_categories:
    df = df[df["category_pt"].isin(selected_categories)]

df = df[df["price"] >= price_min]
if price_max < 1000:  # no máximo do slider, não cortamos a cauda de itens caros
    df = df[df["price"] <= price_max]

st.sidebar.markdown("---")
st.sidebar.metric("Itens no filtro", f"{len(df):,}".replace(",", "."))
st.sidebar.caption(
    "Base: pedidos **entregues** entre jan/2017 e ago/2018. "
    "Faturamento considera o preço dos produtos (frete analisado à parte)."
)

if df.empty:
    st.warning("Nenhum dado encontrado com os filtros selecionados. Ajuste os filtros na barra lateral.")
    st.stop()

# --------------------------------------------------------------------------- #
# Cabeçalho e KPIs
# --------------------------------------------------------------------------- #
st.title("Performance de Vendas — Olist")
st.caption(
    "Análise de 96 mil pedidos entregues do maior marketplace brasileiro. "
    "Use os filtros à esquerda para explorar por período, região e categoria."
)

kpis = an.kpi_summary(df)

row1 = st.columns(4)
row1[0].metric("Faturamento", f"R$ {kpis['faturamento']/1_000_000:.2f}M")
row1[1].metric("Pedidos", f"{kpis['pedidos']:,.0f}".replace(",", "."))
row1[2].metric("Ticket médio", f"R$ {kpis['ticket_medio']:.2f}")
row1[3].metric("Clientes únicos", f"{kpis['clientes_unicos']:,.0f}".replace(",", "."))

row2 = st.columns(4)
row2[0].metric("Nota média", f"{kpis['nota_media']:.2f} ⭐")
row2[1].metric("Prazo médio de entrega", f"{kpis['prazo_medio_dias']:.1f} dias")
row2[2].metric(
    "Pedidos atrasados",
    f"{kpis['taxa_atraso']:.1%}",
    delta=f"{-kpis['taxa_atraso']:.1%} vs. meta 0%",
    delta_color="inverse",
)
row2[3].metric("Vendedores ativos", f"{kpis['vendedores_ativos']:,.0f}".replace(",", "."))

st.markdown("---")

# --------------------------------------------------------------------------- #
# Abas
# --------------------------------------------------------------------------- #
tab_overview, tab_products, tab_sellers, tab_geo, tab_delivery, tab_data = st.tabs(
    [
        "📈 Visão geral",
        "🛍️ Produtos",
        "🏪 Vendedores",
        "🗺️ Geografia",
        "🚚 Entrega & Satisfação",
        "🗂️ Dados",
    ]
)

# --- Visão geral ------------------------------------------------------------ #
with tab_overview:
    monthly = an.monthly_revenue(df)

    st.plotly_chart(plots.plot_monthly_revenue(monthly), width="stretch")

    best_month = monthly.loc[monthly["faturamento"].idxmax()]
    insight(
        f"<b>Sazonalidade clara.</b> O melhor mês foi "
        f"<b>{best_month['order_month']:%b/%Y}</b> com "
        f"R$ {best_month['faturamento']:,.0f} — efeito Black Friday. "
        "Novembro e janeiro puxam o pico; dezembro cai porque a entrega de Natal "
        "não chega a tempo e o cliente antecipa a compra."
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(plots.plot_growth(monthly), width="stretch")
    with col_b:
        st.plotly_chart(
            plots.plot_weekday_hour_heatmap(an.revenue_by_weekday_hour(df)),
            width="stretch",
        )

    insight(
        "<b>Janela de conversão.</b> As compras se concentram entre <b>10h e 22h de "
        "segunda a sexta</b>, com o pico na segunda-feira à noite. Fim de semana "
        "responde por bem menos pedidos — campanhas e disparos de e-mail rendem mais "
        "no início da semana."
    )

    st.subheader("Resumo mensal")
    display = monthly.copy()
    display["Mês"] = display["order_month"].dt.strftime("%m/%Y")
    display = display[
        ["Mês", "faturamento", "pedidos", "ticket_medio", "crescimento_mom"]
    ].rename(
        columns={
            "faturamento": "Faturamento (R$)",
            "pedidos": "Pedidos",
            "ticket_medio": "Ticket médio (R$)",
            "crescimento_mom": "Crescimento MoM",
        }
    )
    st.dataframe(
        display.style.format(
            {
                "Faturamento (R$)": "R$ {:,.0f}",
                "Pedidos": "{:,.0f}",
                "Ticket médio (R$)": "R$ {:.2f}",
                "Crescimento MoM": "{:+.1%}",
            }
        ).background_gradient(subset=["Faturamento (R$)"], cmap="Blues"),
        width="stretch",
        hide_index=True,
    )

# --- Produtos --------------------------------------------------------------- #
with tab_products:
    top_cat = an.top_categories(df, top_n=12)

    col_a, col_b = st.columns([1.1, 1])
    with col_a:
        st.plotly_chart(plots.plot_top_categories(top_cat), width="stretch")
    with col_b:
        st.plotly_chart(
            plots.plot_category_matrix(an.category_matrix(df)), width="stretch"
        )

    leader = top_cat.iloc[0]
    insight(
        f"<b>Portfólio pulverizado.</b> A líder — {leader['category_pt']} — representa "
        f"apenas <b>{leader['participacao']:.1%}</b> do faturamento, e as 12 maiores "
        f"somam {top_cat['participacao'].sum():.0%}. Não há dependência de uma única "
        "categoria, o que reduz risco, mas também dilui o poder de negociação com fornecedores."
    )

    top_states = (
        an.revenue_by_state(df)["customer_state"].head(8).tolist()
    )
    st.plotly_chart(
        plots.plot_state_category_heatmap(an.top_categories_by_state(df), top_states),
        width="stretch",
    )

    insight(
        "<b>Gosto nacional homogêneo.</b> As mesmas categorias (saúde e beleza, "
        "cama/mesa/banho, relógios e presentes) lideram em praticamente todos os "
        "estados. Isso permite um sortimento padronizado no centro de distribuição, "
        "com ajustes finos por região em vez de catálogos regionais separados."
    )

    st.subheader("Detalhe por categoria")
    cat_table = an.top_categories(df, top_n=30)[
        ["category_pt", "faturamento", "itens", "preco_medio", "nota_media", "participacao"]
    ].rename(
        columns={
            "category_pt": "Categoria",
            "faturamento": "Faturamento (R$)",
            "itens": "Itens",
            "preco_medio": "Preço médio (R$)",
            "nota_media": "Nota média",
            "participacao": "Participação",
        }
    )
    st.dataframe(
        cat_table.style.format(
            {
                "Faturamento (R$)": "R$ {:,.0f}",
                "Itens": "{:,.0f}",
                "Preço médio (R$)": "R$ {:.2f}",
                "Nota média": "{:.2f}",
                "Participação": "{:.1%}",
            }
        ).background_gradient(subset=["Nota média"], cmap="RdYlGn"),
        width="stretch",
        hide_index=True,
    )

# --- Vendedores ------------------------------------------------------------- #
with tab_sellers:
    sellers = an.seller_ranking(df, top_n=15)
    headline = an.concentration_headline(df)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Top 10 vendedores", f"{headline['share_top_10_vendedores']:.1%} da receita")
    col_b.metric("Top 20% vendedores", f"{headline['share_top_20pct']:.1%} da receita")
    col_c.metric(
        "Vendedores até 80% da receita",
        f"{headline['vendedores_para_80pct']:,.0f}".replace(",", "."),
        delta=f"{headline['percentual_vendedores_para_80pct']:.0%} da base",
        delta_color="off",
    )

    col_d, col_e = st.columns(2)
    with col_d:
        st.plotly_chart(plots.plot_top_sellers(sellers), width="stretch")
    with col_e:
        st.plotly_chart(plots.plot_pareto(an.market_concentration(df)), width="stretch")

    insight(
        f"<b>Cauda longa, mas com Pareto.</b> Nenhum vendedor individual domina "
        f"(os 10 maiores fazem {headline['share_top_10_vendedores']:.1%}), porém "
        f"<b>{headline['percentual_vendedores_para_80pct']:.0%} dos vendedores geram 80% "
        "da receita</b>. A gestão de contas deveria ser desenhada em dois trilhos: "
        "atendimento dedicado para esse núcleo e automação/autoatendimento para a cauda."
    )

    st.subheader("Ranking de vendedores")
    seller_table = sellers[
        ["seller_label", "estado", "faturamento", "pedidos", "ticket_medio",
         "nota_media", "taxa_atraso", "categorias"]
    ].rename(
        columns={
            "seller_label": "Vendedor",
            "estado": "UF",
            "faturamento": "Faturamento (R$)",
            "pedidos": "Pedidos",
            "ticket_medio": "Ticket médio (R$)",
            "nota_media": "Nota média",
            "taxa_atraso": "Atrasos",
            "categorias": "Categorias",
        }
    )
    st.dataframe(
        seller_table.style.format(
            {
                "Faturamento (R$)": "R$ {:,.0f}",
                "Pedidos": "{:,.0f}",
                "Ticket médio (R$)": "R$ {:.2f}",
                "Nota média": "{:.2f}",
                "Atrasos": "{:.1%}",
            }
        ).background_gradient(subset=["Nota média"], cmap="RdYlGn")
        .background_gradient(subset=["Atrasos"], cmap="Reds"),
        width="stretch",
        hide_index=True,
    )
    st.caption(
        "Atenção aos vendedores com faturamento alto e nota baixa: são os que mais "
        "geram atrito de marca por real vendido."
    )

# --- Geografia -------------------------------------------------------------- #
with tab_geo:
    states = an.revenue_by_state(df)

    st.plotly_chart(
        plots.plot_state_map(states, load_coordinates()), width="stretch"
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(plots.plot_state_bars(states), width="stretch")
    with col_b:
        st.plotly_chart(
            plots.plot_freight_by_region(an.freight_analysis(df)), width="stretch"
        )

    top3_share = states["participacao"].head(3).sum()
    insight(
        f"<b>O Brasil do e-commerce é o Sudeste.</b> SP, RJ e MG concentram "
        f"<b>{top3_share:.0%}</b> da receita. Nas regiões Norte e Nordeste o cliente "
        "espera quase o dobro do tempo e paga um frete proporcionalmente muito maior — "
        "um centro de distribuição no Nordeste atacaria simultaneamente prazo, frete e nota."
    )

    st.subheader("Desempenho por estado")
    state_table = states[
        ["customer_state", "regiao", "faturamento", "pedidos", "ticket_medio",
         "prazo_medio", "taxa_atraso", "nota_media", "frete_medio"]
    ].rename(
        columns={
            "customer_state": "UF",
            "regiao": "Região",
            "faturamento": "Faturamento (R$)",
            "pedidos": "Pedidos",
            "ticket_medio": "Ticket médio (R$)",
            "prazo_medio": "Prazo (dias)",
            "taxa_atraso": "Atrasos",
            "nota_media": "Nota média",
            "frete_medio": "Frete médio (R$)",
        }
    )
    st.dataframe(
        state_table.style.format(
            {
                "Faturamento (R$)": "R$ {:,.0f}",
                "Pedidos": "{:,.0f}",
                "Ticket médio (R$)": "R$ {:.2f}",
                "Prazo (dias)": "{:.1f}",
                "Atrasos": "{:.1%}",
                "Nota média": "{:.2f}",
                "Frete médio (R$)": "R$ {:.2f}",
            }
        ).background_gradient(subset=["Prazo (dias)"], cmap="Reds")
        .background_gradient(subset=["Nota média"], cmap="RdYlGn"),
        width="stretch",
        hide_index=True,
    )

# --- Entrega & Satisfação --------------------------------------------------- #
with tab_delivery:
    delivery = an.delivery_vs_review(df)
    late = an.late_delivery_impact(df)

    st.plotly_chart(plots.plot_delivery_vs_review(delivery), width="stretch")

    on_time = first_value(late, ~late["is_late"], "nota_media")
    delayed = first_value(late, late["is_late"], "nota_media")

    if on_time is not None and delayed is not None:
        insight(
            f"<b>Logística é o produto.</b> Pedidos entregues no prazo recebem nota média "
            f"<b>{on_time:.2f}</b>; os atrasados, <b>{delayed:.2f}</b> — uma queda de "
            f"{on_time - delayed:.2f} estrelas. Entre as entregas que passam de 30 dias, "
            "quase dois terços viram nota 1. Prazo não é detalhe operacional: é o principal "
            "driver de satisfação de toda a base."
        )
    else:
        insight(
            "<b>Logística é o produto.</b> O recorte atual não tem pedidos nos dois "
            "grupos (no prazo e atrasado) para a comparação. Na base completa, atrasar "
            "custa 1,73 estrela: 4,29 no prazo contra 2,57 atrasado."
        )

    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(plots.plot_late_impact(late), width="stretch")
    with col_b:
        st.plotly_chart(
            plots.plot_review_distribution(an.review_distribution(df)),
            width="stretch",
        )

    st.plotly_chart(
        plots.plot_delivery_evolution(an.delivery_evolution(df)), width="stretch"
    )

    st.markdown("### Pagamentos")
    col_c, col_d = st.columns(2)
    with col_c:
        st.plotly_chart(plots.plot_payment_mix(an.payment_profile(df)), width="stretch")
    with col_d:
        st.plotly_chart(
            plots.plot_installments(an.installments_profile(df)), width="stretch"
        )

    insight(
        "<b>Crédito parcelado sustenta o ticket.</b> O cartão responde pela maior parte "
        "dos pedidos e o ticket médio cresce junto com o número de parcelas — sinal de "
        "que o parcelamento viabiliza a compra de itens mais caros. Reduzir o número "
        "máximo de parcelas encolheria diretamente o ticket médio."
    )

# --- Dados ------------------------------------------------------------------ #
with tab_data:
    st.subheader("Sobre a base")
    st.markdown(
        """
        **Fonte:** [Brazilian E-Commerce Public Dataset by Olist (Kaggle)](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

        **Tratamentos aplicados** (ver `src/data_loader.py`):
        - Apenas pedidos com status `delivered` — cancelados/indisponíveis inflariam a receita.
        - Recorte de **jan/2017 a ago/2018**: os meses das pontas têm pouquíssimos pedidos
          e distorcem as séries temporais.
        - Uma avaliação por pedido (a mais recente) e um meio de pagamento principal
          (o de maior valor), evitando duplicar linhas nos joins.
        - Produtos sem categoria viram `uncategorized` em vez de serem descartados.
        - Granularidade final: **uma linha por item vendido**.
        """
    )

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Linhas (itens)", f"{len(df):,}".replace(",", "."))
    col_b.metric("Colunas", f"{df.shape[1]}")
    col_c.metric(
        "Período",
        f"{df['order_date'].min():%m/%Y} – {df['order_date'].max():%m/%Y}",
    )

    st.subheader("Amostra da tabela analítica")
    preview_cols = [
        "order_id", "order_purchase_timestamp", "customer_state", "seller_state",
        "category_pt", "price", "freight_value", "delivery_days", "is_late",
        "review_score", "payment_type_pt",
    ]
    st.dataframe(df[preview_cols].head(200), width="stretch", hide_index=True)

    st.download_button(
        "⬇️ Baixar dados filtrados (CSV)",
        data=df[preview_cols].to_csv(index=False).encode("utf-8"),
        file_name="olist_dados_filtrados.csv",
        mime="text/csv",
    )

st.markdown("---")
st.caption(
    "Projeto de análise de dados • Python · Pandas · Plotly · Streamlit • "
    "Código em github.com/sergiomeyer23/olist-sales-performance-analysis"
)
