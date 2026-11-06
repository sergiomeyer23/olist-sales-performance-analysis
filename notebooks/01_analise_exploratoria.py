"""Análise exploratória, versão narrada em script.

Este arquivo é o caderno de campo do projeto: mostra o raciocínio passo a
passo, com as perguntas na ordem em que foram feitas. O código de produção
está em src/ e o resultado final no dashboard (app.py).

Pode ser executado direto (`python notebooks/01_analise_exploratoria.py`) ou
aberto no VS Code / Jupyter, já que usa células `# %%`.
"""

# %%
import sys
from pathlib import Path

import pandas as pd

# Permite importar src/ mesmo executando de dentro da pasta notebooks/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import analysis as an  # noqa: E402
from src.data_loader import get_data  # noqa: E402

pd.set_option("display.float_format", lambda v: f"{v:,.2f}")
pd.set_option("display.max_columns", 40)

df = get_data()
print(f"{len(df):,} itens | {df['order_id'].nunique():,} pedidos")
print(f"Período: {df['order_date'].min():%d/%m/%Y} a {df['order_date'].max():%d/%m/%Y}")

# %% [markdown]
# ## 1. Como está a saúde do negócio?
# Primeiro os números de topo, para saber a ordem de grandeza com que lidamos.

# %%
kpis = an.kpi_summary(df)
for name, value in kpis.items():
    print(f"{name:.<26} {value:,.2f}")

# %% [markdown]
# Leitura: R$ 13,2 milhões em 96 mil pedidos, ticket médio de R$ 137 e nota
# média 4,16. O frete representa ~14% do valor total pago.

# %% [markdown]
# ## 2. A receita está crescendo?

# %%
monthly = an.monthly_revenue(df)
print(monthly[["order_month", "faturamento", "pedidos", "ticket_medio", "crescimento_mom"]])

# %% [markdown]
# Leitura: 2017 teve crescimento forte; de janeiro a agosto de 2018 o
# faturamento mensal ficou em torno de R$ 900 mil (média de R$ 902 mil). O pico
# de nov/2017 (R$ 988 mil) é a Black Friday. Em dezembro o faturamento cai,
# provavelmente porque o cliente antecipa a compra de Natal sabendo que a
# entrega demora.

# %% [markdown]
# ## 3. Quando o cliente compra?

# %%
heat = an.revenue_by_weekday_hour(df)
print(heat.groupby("weekday_label")["pedidos"].sum().sort_values(ascending=False))
print("\nHorários de pico:")
print(heat.nlargest(5, "pedidos")[["weekday_label", "order_hour", "pedidos"]])

# %% [markdown]
# Leitura: segunda-feira é o dia mais forte (15,7 mil pedidos) e sábado o mais
# fraco (10,5 mil). O volume se concentra entre 10h e 22h. Isso sugere compra de
# rotina em dia útil, o que favorece concentrar mídia e e-mail marketing no
# início da semana.

# %% [markdown]
# ## 4. Quais categorias sustentam a receita?

# %%
print(an.top_categories(df, top_n=10)[
    ["category_pt", "faturamento", "participacao", "itens", "nota_media"]
])

# %% [markdown]
# Leitura: a maior categoria (Saúde e beleza) faz 9,3% do total e as 12 maiores
# somam 69%. Num marketplace 3P como a Olist, essa pulverização do catálogo
# reduz a dependência de um nicho: o risco de concentração é menor. A oferta de
# cada categoria depende dos sellers ativos nela, então o trabalho comercial é
# prospectar e ativar sellers onde há demanda e nota baixa.

# %% [markdown]
# ### Existe categoria que vende bem e tem nota baixa?

# %%
matrix = an.category_matrix(df)
print("Piores notas entre categorias relevantes:")
print(matrix.nsmallest(5, "nota_media")[
    ["category_pt", "itens", "faturamento", "nota_media", "taxa_atraso"]
])

# %% [markdown]
# Leitura: Móveis de escritório (nota 3,65) e Cama, mesa e banho (4,00) vendem
# muito e ficam abaixo da média geral de 4,16. São itens volumosos, com frete
# caro e maior chance de avaria, candidatos a uma revisão de embalagem e de
# expectativa de prazo no anúncio.

# %% [markdown]
# ## 5. O mercado é concentrado?

# %%
concentration = an.concentration_headline(df)
for name, value in concentration.items():
    print(f"{name:.<34} {value:,.4f}")

# %% [markdown]
# Leitura: os 10 maiores vendedores fazem 13,3% da receita. A curva completa
# mostra que 531 dos 2.945 vendedores (18%) geram 80%, e os 20% maiores fazem
# 82%. Um núcleo de ~530 vendedores carrega a operação.

# %% [markdown]
# ## 6. Onde estão os clientes?

# %%
states = an.revenue_by_state(df)
print(states.head(10)[
    ["customer_state", "faturamento", "participacao", "ticket_medio",
     "prazo_medio", "nota_media", "frete_medio"]
])
print("\nPor região:")
print(an.revenue_by_region(df))

# %% [markdown]
# Leitura: o Sudeste concentra 65% da receita (SP, RJ e MG juntos, 63%) e SP
# sozinho, 38%. No Sudeste o pedido chega em ~10,7 dias com frete médio de
# R$ 17; no Norte são ~22,6 dias e R$ 37 de frete. A nota média é 4,18 no
# Sudeste e 3,97 no Nordeste, a menor entre as regiões.

# %% [markdown]
# ## 7. Prazo de entrega x satisfação

# %%
print(an.delivery_vs_review(df))
print()
print(an.late_delivery_impact(df)[
    ["situacao", "pedidos", "nota_media", "perc_nota_1", "perc_nota_5"]
])

# %% [markdown]
# Leitura:
#
# - Entrega em até 3 dias: nota 4,48
# - Entrega acima de 30 dias: nota 2,24, com 63% de notas 1 ou 2
# - Pedido no prazo: 4,29; pedido atrasado: 2,57
#
# Atrasar custa 1,73 estrela, e 46% dos pedidos atrasados recebem nota 1. Só
# 8,1% dos pedidos atrasam (7.658 de 95.560 avaliados). Se esses pedidos
# tivessem a nota média dos entregues no prazo, a nota geral subiria de 4,16
# para 4,29. Os dados são observacionais, então esse número é uma ordem de
# grandeza e não um efeito causal medido.

# %% [markdown]
# ## 8. Como o cliente paga?

# %%
print(an.payment_profile(df))
print()
print(an.installments_profile(df))

# %% [markdown]
# Leitura: 75% dos pedidos saem no cartão e o ticket médio sobe de R$ 101
# (à vista) para R$ 333 (7 a 10 parcelas). O parcelamento viabiliza a compra
# de itens mais caros, então mexer nele afeta o ticket diretamente.
#
# O boleto ainda é ~20% dos pedidos.

# %% [markdown]
# ## 9. Quanto pesa o frete?

# %%
print(an.freight_analysis(df)[
    ["customer_region", "tipo_venda", "frete_medio", "frete_sobre_preco", "prazo_medio", "itens"]
])

# %% [markdown]
# Leitura: no Norte o frete equivale a 22,7% do preço do produto, contra
# 13,1% em vendas dentro do próprio estado no Sudeste. Quase toda venda para
# Norte e Nordeste é interestadual: só 1,8% dos vendedores ativos estão no
# Nordeste e 0,1% no Norte. O frete alto tende a pesar na conversão nessas
# regiões.

# %% [markdown]
# ---
# ## Conclusões e recomendações
#
# 1. Reduzir o atraso. Cada pedido atrasado perde 1,73 estrela, e a nota geral
#    iria de 4,16 para 4,29 se eles tivessem a nota dos entregues no prazo. No
#    marketplace, o atraso começa na postagem pelo seller
#    (order_delivered_carrier_date), então vale acompanhar o cumprimento do SLA
#    de postagem por seller.
# 2. Dois grupos de vendedores. ~530 vendedores (18%) fazem 80% da receita:
#    gerente de conta para eles e autoatendimento para a cauda.
# 3. Prospectar sellers no Norte e no Nordeste. Essas regiões têm prazo de 20 a
#    23 dias, frete de 22% a 23% do preço nas vendas interestaduais e, no
#    Nordeste, nota 3,97. Sellers locais encurtam o trajeto, e a malha
#    logística com cross-docking regional reduz o prazo dos que ficam no
#    Sudeste.
# 4. Revisar as categorias volumosas. Móveis de escritório e cama/mesa/banho têm
#    volume alto e nota abaixo da média: revisar embalagem e prometer prazos
#    realistas.
# 5. Preparar a operação para novembro. Em nov/2017 a taxa de atraso foi de 14%,
#    contra 5% em outubro, e a nota média caiu de 4,21 para 3,99.
