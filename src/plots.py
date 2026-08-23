"""Construção dos gráficos Plotly usados no dashboard e no relatório.

Separar "cálculo" (analysis.py) de "desenho" (plots.py) permite testar os
números sem abrir figura e reaproveitar o mesmo gráfico em vários lugares.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src import config

# Layout base aplicado em todas as figuras (identidade visual consistente).
BASE_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Inter, Segoe UI, sans-serif", size=13),
    title=dict(font=dict(size=18)),
    margin=dict(l=60, r=30, t=70, b=50),
    hoverlabel=dict(font_size=12),
    colorway=config.COLOR_SEQUENCE,
)


def _finish(fig: go.Figure, title: str, subtitle: str = "") -> go.Figure:
    """Aplica o layout padrão e um subtítulo opcional em cinza."""
    full_title = title
    if subtitle:
        full_title = f"{title}<br><span style='font-size:12px;color:#6e7781'>{subtitle}</span>"

    fig.update_layout(**BASE_LAYOUT)
    fig.update_layout(title_text=full_title)
    return fig


def _brl(values: pd.Series) -> list[str]:
    """Formata uma série numérica como moeda brasileira abreviada."""
    return [f"R$ {v/1000:,.0f}k" if v >= 1000 else f"R$ {v:,.0f}" for v in values]


# --------------------------------------------------------------------------- #
# Evolução temporal
# --------------------------------------------------------------------------- #
def plot_monthly_revenue(monthly: pd.DataFrame) -> go.Figure:
    """Barras de faturamento mensal + linha de média móvel de 3 meses."""
    fig = go.Figure()

    fig.add_bar(
        x=monthly["order_month"],
        y=monthly["faturamento"],
        name="Faturamento",
        marker_color=config.COLOR_PRIMARY,
        hovertemplate="%{x|%b/%Y}<br>R$ %{y:,.0f}<extra></extra>",
    )
    fig.add_scatter(
        x=monthly["order_month"],
        y=monthly["media_movel_3m"],
        name="Média móvel (3 meses)",
        mode="lines",
        line=dict(color=config.COLOR_SECONDARY, width=3),
        hovertemplate="%{x|%b/%Y}<br>R$ %{y:,.0f}<extra></extra>",
    )

    # Black Friday de 2017 é o pico da base — vale destacar no gráfico.
    peak = monthly.loc[monthly["faturamento"].idxmax()]
    fig.add_annotation(
        x=peak["order_month"],
        y=peak["faturamento"],
        text="Black Friday",
        showarrow=True,
        arrowhead=2,
        yshift=10,
        font=dict(size=11, color=config.COLOR_NEGATIVE),
    )

    fig.update_yaxes(title="Faturamento (R$)", tickformat=",.0f")
    fig.update_xaxes(title="")
    return _finish(
        fig,
        "Evolução do faturamento mensal",
        "Crescimento consistente ao longo de 2017 e estabilização em 2018",
    )


def plot_growth(monthly: pd.DataFrame) -> go.Figure:
    """Crescimento mês a mês, verde para alta e vermelho para queda."""
    data = monthly.dropna(subset=["crescimento_mom"])
    colors = [
        config.COLOR_POSITIVE if v >= 0 else config.COLOR_NEGATIVE
        for v in data["crescimento_mom"]
    ]

    fig = go.Figure(
        go.Bar(
            x=data["order_month"],
            y=data["crescimento_mom"] * 100,
            marker_color=colors,
            hovertemplate="%{x|%b/%Y}<br>%{y:.1f}%<extra></extra>",
        )
    )

    fig.add_hline(y=0, line_width=1, line_color="#6e7781")
    fig.update_yaxes(title="Variação vs. mês anterior (%)", ticksuffix="%")
    fig.update_xaxes(title="")
    return _finish(fig, "Crescimento mês a mês (MoM)", "Sazonalidade forte em novembro e janeiro")


def plot_weekday_hour_heatmap(heat: pd.DataFrame) -> go.Figure:
    """Mapa de calor de pedidos por dia da semana e hora do dia."""
    pivot = heat.pivot_table(
        index="weekday_label", columns="order_hour", values="pedidos", fill_value=0
    ).reindex(config.WEEKDAY_LABELS_PT)

    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale="Blues",
            hovertemplate="%{y} às %{x}h<br>%{z} pedidos<extra></extra>",
            colorbar=dict(title="Pedidos"),
        )
    )

    fig.update_xaxes(title="Hora da compra", dtick=2)
    fig.update_yaxes(title="")
    return _finish(
        fig,
        "Quando o cliente compra",
        "Concentração entre 10h e 22h nos dias úteis; fim de semana é mais fraco",
    )


# --------------------------------------------------------------------------- #
# Categorias
# --------------------------------------------------------------------------- #
def plot_top_categories(categories: pd.DataFrame) -> go.Figure:
    """Barras horizontais das categorias campeãs de faturamento."""
    data = categories.sort_values("faturamento")

    fig = go.Figure(
        go.Bar(
            x=data["faturamento"],
            y=data["category_pt"],
            orientation="h",
            marker_color=config.COLOR_PRIMARY,
            text=_brl(data["faturamento"]),
            textposition="outside",
            customdata=data[["participacao", "nota_media", "itens"]],
            hovertemplate=(
                "<b>%{y}</b><br>Faturamento: R$ %{x:,.0f}"
                "<br>Participação: %{customdata[0]:.1%}"
                "<br>Nota média: %{customdata[1]:.2f}"
                "<br>Itens: %{customdata[2]:,}<extra></extra>"
            ),
        )
    )

    fig.update_xaxes(title="Faturamento (R$)")
    fig.update_yaxes(title="")
    return _finish(
        fig,
        "Categorias com maior faturamento",
        "Nenhuma categoria passa de 11% do total: portfólio bem distribuído",
    )


def plot_category_matrix(matrix: pd.DataFrame) -> go.Figure:
    """Dispersão volume x nota, com o tamanho da bolha = faturamento."""
    fig = px.scatter(
        matrix,
        x="itens",
        y="nota_media",
        size="faturamento",
        color="preco_medio",
        hover_name="category_pt",
        size_max=48,
        color_continuous_scale="Viridis",
        labels={
            "itens": "Itens vendidos",
            "nota_media": "Nota média",
            "preco_medio": "Preço médio (R$)",
        },
    )

    fig.add_hline(
        y=matrix["nota_media"].mean(),
        line_dash="dash",
        line_color="#6e7781",
        annotation_text="Nota média geral",
        annotation_position="bottom right",
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>Itens: %{x:,}<br>Nota: %{y:.2f}"
            "<br>Preço médio: R$ %{marker.color:.0f}<extra></extra>"
        )
    )

    return _finish(
        fig,
        "Volume x satisfação por categoria",
        "Bolhas abaixo da linha vendem muito mas decepcionam: prioridade de melhoria",
    )


def plot_state_category_heatmap(top_by_state: pd.DataFrame, top_states: list[str]) -> go.Figure:
    """Heatmap das categorias líderes nos maiores estados."""
    data = top_by_state[top_by_state["customer_state"].isin(top_states)]
    pivot = data.pivot_table(
        index="category_pt", columns="customer_state", values="faturamento", fill_value=0
    )
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=True).index]
    pivot = pivot[[s for s in top_states if s in pivot.columns]]

    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale="Blues",
            hovertemplate="%{y} em %{x}<br>R$ %{z:,.0f}<extra></extra>",
            colorbar=dict(title="R$"),
        )
    )

    fig.update_xaxes(title="Estado do cliente")
    fig.update_yaxes(title="")
    return _finish(
        fig,
        "Categorias líderes nos principais estados",
        "O mix de consumo se repete entre as UFs: estratégia nacional funciona",
    )


# --------------------------------------------------------------------------- #
# Vendedores
# --------------------------------------------------------------------------- #
def plot_top_sellers(sellers: pd.DataFrame) -> go.Figure:
    """Ranking de vendedores colorido pela nota média recebida."""
    data = sellers.sort_values("faturamento")

    fig = go.Figure(
        go.Bar(
            x=data["faturamento"],
            y=data["seller_label"],
            orientation="h",
            marker=dict(
                color=data["nota_media"],
                colorscale="RdYlGn",
                cmin=3.0,
                cmax=5.0,
                colorbar=dict(title="Nota"),
            ),
            customdata=data[["estado", "pedidos", "nota_media", "taxa_atraso"]],
            hovertemplate=(
                "<b>%{y}</b> (%{customdata[0]})<br>Faturamento: R$ %{x:,.0f}"
                "<br>Pedidos: %{customdata[1]:,}"
                "<br>Nota média: %{customdata[2]:.2f}"
                "<br>Atrasos: %{customdata[3]:.1%}<extra></extra>"
            ),
        )
    )

    fig.update_xaxes(title="Faturamento (R$)")
    fig.update_yaxes(title="ID do vendedor")
    return _finish(
        fig,
        "Maiores vendedores por faturamento",
        "Cor indica a nota média: vender muito não garante cliente satisfeito",
    )


def plot_pareto(pareto: pd.DataFrame) -> go.Figure:
    """Curva de Pareto da concentração de faturamento entre vendedores."""
    fig = go.Figure()

    fig.add_scatter(
        x=pareto["percentual_vendedores"] * 100,
        y=pareto["participacao_acumulada"] * 100,
        mode="lines",
        line=dict(color=config.COLOR_PRIMARY, width=3),
        fill="tozeroy",
        fillcolor="rgba(31,111,235,0.12)",
        name="Faturamento acumulado",
        hovertemplate="%{x:.0f}% dos vendedores<br>%{y:.1f}% do faturamento<extra></extra>",
    )
    # Linha de referência: distribuição perfeitamente igualitária.
    fig.add_scatter(
        x=[0, 100],
        y=[0, 100],
        mode="lines",
        line=dict(color="#6e7781", dash="dash", width=1.5),
        name="Distribuição igualitária",
        hoverinfo="skip",
    )
    fig.add_vline(x=20, line_dash="dot", line_color=config.COLOR_NEGATIVE)
    fig.add_annotation(
        x=20, y=50, text="20% dos vendedores", showarrow=False, xshift=70,
        font=dict(size=11, color=config.COLOR_NEGATIVE),
    )

    fig.update_xaxes(title="% dos vendedores (ordenados por faturamento)", ticksuffix="%")
    fig.update_yaxes(title="% do faturamento acumulado", ticksuffix="%")
    return _finish(
        fig,
        "Concentração de mercado (curva de Pareto)",
        "Os 20% maiores vendedores respondem por ~82% da receita",
    )


# --------------------------------------------------------------------------- #
# Geografia
# --------------------------------------------------------------------------- #
def plot_state_bars(states: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Faturamento por UF, colorido por região."""
    data = states.head(top_n).sort_values("faturamento")

    fig = px.bar(
        data,
        x="faturamento",
        y="customer_state",
        color="regiao",
        orientation="h",
        labels={"faturamento": "Faturamento (R$)", "customer_state": "", "regiao": "Região"},
        custom_data=["participacao", "ticket_medio", "nota_media"],
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>Faturamento: R$ %{x:,.0f}"
            "<br>Participação: %{customdata[0]:.1%}"
            "<br>Ticket médio: R$ %{customdata[1]:.0f}"
            "<br>Nota média: %{customdata[2]:.2f}<extra></extra>"
        )
    )

    return _finish(
        fig,
        "Faturamento por estado",
        "São Paulo sozinho responde por 38% de toda a receita",
    )


def plot_state_map(states: pd.DataFrame, coords: pd.DataFrame) -> go.Figure:
    """Mapa de bolhas do Brasil: tamanho = receita, cor = prazo de entrega."""
    data = states.merge(coords, on="customer_state", how="inner")

    fig = px.scatter_map(
        data,
        lat="lat",
        lon="lon",
        size="faturamento",
        color="prazo_medio",
        hover_name="customer_state",
        size_max=55,
        zoom=2.6,
        color_continuous_scale="RdYlGn_r",
        map_style="carto-positron",
        custom_data=["faturamento", "pedidos", "prazo_medio", "nota_media"],
        labels={"prazo_medio": "Prazo médio (dias)"},
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>Faturamento: R$ %{customdata[0]:,.0f}"
            "<br>Pedidos: %{customdata[1]:,}"
            "<br>Prazo médio: %{customdata[2]:.1f} dias"
            "<br>Nota média: %{customdata[3]:.2f}<extra></extra>"
        )
    )
    fig.update_layout(**BASE_LAYOUT)
    fig.update_layout(
        title_text=(
            "Receita e prazo de entrega pelo Brasil<br>"
            "<span style='font-size:12px;color:#6e7781'>"
            "Quanto mais ao norte, mais demorada a entrega e menor a receita</span>"
        ),
        margin=dict(l=0, r=0, t=70, b=0),
        height=560,
    )
    return fig


def plot_state_map_static(states: pd.DataFrame, coords: pd.DataFrame) -> go.Figure:
    """Mapa de bolhas em coordenadas puras (latitude x longitude).

    ``plot_state_map`` usa tiles do Mapbox e precisa de internet para desenhar
    o fundo. Esta versão plota apenas as UFs pelas suas coordenadas, então
    renderiza offline — é a que exportamos como PNG para o README.
    """
    data = states.merge(coords, on="customer_state", how="inner")

    fig = px.scatter(
        data,
        x="lon",
        y="lat",
        size="faturamento",
        color="prazo_medio",
        text="customer_state",
        size_max=60,
        color_continuous_scale="RdYlGn_r",
        custom_data=["customer_state", "faturamento", "pedidos", "prazo_medio", "nota_media"],
        labels={"prazo_medio": "Prazo médio (dias)"},
    )

    fig.update_traces(
        textposition="middle center",
        textfont=dict(size=9, color="#1f2328"),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>Faturamento: R$ %{customdata[1]:,.0f}"
            "<br>Pedidos: %{customdata[2]:,}"
            "<br>Prazo médio: %{customdata[3]:.1f} dias"
            "<br>Nota média: %{customdata[4]:.2f}<extra></extra>"
        ),
    )
    fig.update_xaxes(title="Longitude", showgrid=True, gridcolor="#eef1f4", zeroline=False)
    fig.update_yaxes(
        title="Latitude",
        showgrid=True,
        gridcolor="#eef1f4",
        zeroline=False,
        # Mantém a proporção geográfica correta do Brasil.
        scaleanchor="x",
        scaleratio=1,
    )
    fig.update_layout(**BASE_LAYOUT)
    fig.update_layout(
        title_text=(
            "Receita e prazo de entrega pelo Brasil<br>"
            "<span style='font-size:12px;color:#6e7781'>"
            "Cada bolha é uma UF | tamanho = faturamento | cor = prazo médio "
            "(vermelho = mais lento)</span>"
        ),
        height=620,
        plot_bgcolor="#fbfcfd",
    )
    return fig


def plot_freight_by_region(freight: pd.DataFrame) -> go.Figure:
    """Peso do frete sobre o preço, por região e tipo de venda."""
    fig = px.bar(
        freight,
        x="customer_region",
        y="frete_sobre_preco",
        color="tipo_venda",
        barmode="group",
        labels={
            "customer_region": "",
            "frete_sobre_preco": "Frete / preço do produto",
            "tipo_venda": "",
        },
        color_discrete_sequence=[config.COLOR_PRIMARY, config.COLOR_SECONDARY],
    )

    fig.update_yaxes(tickformat=".0%")
    fig.update_traces(hovertemplate="%{x}<br>Frete = %{y:.1%} do preço<extra></extra>")
    return _finish(
        fig,
        "Peso do frete por região",
        "No Norte e Nordeste o frete come uma fatia bem maior do valor do produto",
    )


# --------------------------------------------------------------------------- #
# Entrega e satisfação
# --------------------------------------------------------------------------- #
def plot_delivery_vs_review(delivery: pd.DataFrame) -> go.Figure:
    """Nota média por faixa de prazo + % de avaliações negativas."""
    fig = go.Figure()

    fig.add_bar(
        x=delivery["faixa_prazo"].astype(str),
        y=delivery["nota_media"],
        name="Nota média",
        marker_color=config.COLOR_PRIMARY,
        text=[f"{v:.2f}" for v in delivery["nota_media"]],
        textposition="outside",
        hovertemplate="%{x}<br>Nota média: %{y:.2f}<extra></extra>",
    )
    fig.add_scatter(
        x=delivery["faixa_prazo"].astype(str),
        y=delivery["perc_nota_1_2"] * 100,
        name="% notas 1 e 2",
        mode="lines+markers",
        yaxis="y2",
        line=dict(color=config.COLOR_NEGATIVE, width=3),
        hovertemplate="%{x}<br>%{y:.1f}% de notas baixas<extra></extra>",
    )

    fig.update_layout(
        yaxis=dict(title="Nota média", range=[0, 5.4]),
        yaxis2=dict(
            title="% de notas 1 e 2", overlaying="y", side="right",
            range=[0, 70], ticksuffix="%", showgrid=False,
        ),
        legend=dict(orientation="h", y=1.02, x=0),
    )
    fig.update_xaxes(title="Tempo entre a compra e a entrega")
    return _finish(
        fig,
        "Prazo de entrega x satisfação do cliente",
        "Acima de 30 dias a nota despenca para 2,24 e 63% avaliam com 1 ou 2",
    )


def plot_late_impact(late: pd.DataFrame) -> go.Figure:
    """Comparação direta: pedido no prazo x pedido atrasado."""
    fig = go.Figure()

    fig.add_bar(
        x=late["situacao"],
        y=late["nota_media"],
        marker_color=[config.COLOR_POSITIVE, config.COLOR_NEGATIVE],
        text=[f"{v:.2f}" for v in late["nota_media"]],
        textposition="outside",
        width=0.5,
        customdata=late[["perc_nota_1", "pedidos"]],
        hovertemplate=(
            "<b>%{x}</b><br>Nota média: %{y:.2f}"
            "<br>Nota 1: %{customdata[0]:.1%}"
            "<br>Pedidos: %{customdata[1]:,}<extra></extra>"
        ),
    )

    fig.update_yaxes(title="Nota média", range=[0, 5.4])
    return _finish(
        fig,
        "Impacto do atraso na avaliação",
        "Atrasar custa 1,7 estrela: 46% dos pedidos atrasados recebem nota 1",
    )


def plot_review_distribution(reviews: pd.DataFrame) -> go.Figure:
    """Distribuição das notas de 1 a 5."""
    colors = [
        config.COLOR_NEGATIVE, "#e8743b", config.COLOR_SECONDARY,
        "#8bc34a", config.COLOR_POSITIVE,
    ]

    fig = go.Figure(
        go.Bar(
            x=reviews["nota"].astype(str),
            y=reviews["pedidos"],
            marker_color=colors[: len(reviews)],
            text=[f"{v:.1%}" for v in reviews["participacao"]],
            textposition="outside",
            hovertemplate="Nota %{x}<br>%{y:,} pedidos<extra></extra>",
        )
    )

    fig.update_xaxes(title="Nota da avaliação")
    fig.update_yaxes(title="Pedidos")
    return _finish(
        fig,
        "Distribuição das avaliações",
        "Base polarizada: muita nota 5, mas um bloco relevante de nota 1",
    )


def plot_delivery_evolution(evolution: pd.DataFrame) -> go.Figure:
    """Prazo médio e taxa de atraso ao longo dos meses."""
    fig = go.Figure()

    fig.add_scatter(
        x=evolution["order_month"],
        y=evolution["prazo_medio"],
        name="Prazo médio (dias)",
        mode="lines+markers",
        line=dict(color=config.COLOR_PRIMARY, width=3),
        hovertemplate="%{x|%b/%Y}<br>%{y:.1f} dias<extra></extra>",
    )
    fig.add_scatter(
        x=evolution["order_month"],
        y=evolution["taxa_atraso"] * 100,
        name="Taxa de atraso (%)",
        mode="lines+markers",
        yaxis="y2",
        line=dict(color=config.COLOR_NEGATIVE, width=3, dash="dot"),
        hovertemplate="%{x|%b/%Y}<br>%{y:.1f}% atrasados<extra></extra>",
    )

    fig.update_layout(
        yaxis=dict(title="Prazo médio (dias)"),
        yaxis2=dict(
            title="Taxa de atraso", overlaying="y", side="right",
            ticksuffix="%", showgrid=False,
        ),
        legend=dict(orientation="h", y=1.02, x=0),
    )
    return _finish(
        fig,
        "Evolução da operação logística",
        "Prazos caíram ao longo de 2018, mas com picos de atraso em fevereiro e março",
    )


# --------------------------------------------------------------------------- #
# Pagamentos
# --------------------------------------------------------------------------- #
def plot_payment_mix(payments: pd.DataFrame) -> go.Figure:
    """Participação de cada meio de pagamento."""
    fig = go.Figure(
        go.Pie(
            labels=payments["payment_type_pt"],
            values=payments["pedidos"],
            hole=0.55,
            marker=dict(colors=config.COLOR_SEQUENCE),
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>%{value:,} pedidos<br>%{percent}<extra></extra>",
        )
    )

    fig.update_layout(showlegend=False)
    return _finish(
        fig,
        "Meios de pagamento",
        "Cartão de crédito domina; boleto ainda representa ~1 em cada 5 pedidos",
    )


def plot_installments(installments: pd.DataFrame) -> go.Figure:
    """Pedidos e ticket médio por faixa de parcelamento."""
    fig = go.Figure()

    fig.add_bar(
        x=installments["faixa_parcelas"].astype(str),
        y=installments["pedidos"],
        name="Pedidos",
        marker_color=config.COLOR_PRIMARY,
        hovertemplate="%{x}<br>%{y:,} pedidos<extra></extra>",
    )
    fig.add_scatter(
        x=installments["faixa_parcelas"].astype(str),
        y=installments["valor_medio"],
        name="Ticket médio (R$)",
        mode="lines+markers",
        yaxis="y2",
        line=dict(color=config.COLOR_SECONDARY, width=3),
        hovertemplate="%{x}<br>R$ %{y:,.0f}<extra></extra>",
    )

    fig.update_layout(
        yaxis=dict(title="Pedidos"),
        yaxis2=dict(title="Ticket médio (R$)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.02, x=0),
    )
    fig.update_xaxes(title="Número de parcelas")
    return _finish(
        fig,
        "Parcelamento no cartão de crédito",
        "Quanto maior o valor da compra, mais o cliente parcela",
    )
