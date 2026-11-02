"""Análise exploratória — versão narrada em script.

Este arquivo é o "caderno de campo" do projeto: mostra o raciocínio passo a
passo, com as perguntas na ordem em que foram feitas. O código de produção
mora em src/ e o resultado final no dashboard (app.py).

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
# média 4,08. O frete representa ~14% do valor total pago, uma fatia relevante.

# %% [markdown]
# ## 2. A receita está crescendo?

# %%
monthly = an.monthly_revenue(df)
print(monthly[["order_month", "faturamento", "pedidos", "ticket_medio", "crescimento_mom"]])

# %% [markdown]
# Leitura: 2017 foi de crescimento forte; 2018 estabilizou em torno de
# R$ 900 mil/mês. O pico de nov/2017 (R$ 988 mil) é a Black Friday. Em
# dezembro o faturamento cai: o cliente antecipa a compra de Natal porque sabe
# que a entrega demora.

# %% [markdown]
# ## 3. Quando o cliente compra?

# %%
heat = an.revenue_by_weekday_hour(df)
print(heat.groupby("weekday_label")["pedidos"].sum().sort_values(ascending=False))
print("\nHorários de pico:")
print(heat.nlargest(5, "pedidos")[["weekday_label", "order_hour", "pedidos"]])

# %% [markdown]
# Leitura: segunda-feira é o dia mais forte e o volume se concentra entre
# 10h e 22h. Sábado é o pior dia. Isso sugere compra de escritório ou de
# rotina, não de lazer de fim de semana, e é um bom argumento para concentrar
# mídia e e-mail marketing no início da semana.

# %% [markdown]
# ## 4. Quais categorias sustentam a receita?

# %%
print(an.top_categories(df, top_n=10)[
    ["category_pt", "faturamento", "participacao", "itens", "nota_media"]
])

# %% [markdown]
# Leitura: a maior categoria (Saúde e beleza) faz só 9,3% do total. O
# portfólio é pulverizado, o que dilui o risco mas enfraquece a negociação com
# fornecedores.

# %% [markdown]
# ### Existe categoria que vende bem e decepciona?

# %%
matrix = an.category_matrix(df)
print("Piores notas entre categorias relevantes:")
print(matrix.nsmallest(5, "nota_media")[
    ["category_pt", "itens", "faturamento", "nota_media", "taxa_atraso"]
])

# %% [markdown]
# Leitura: Móveis de escritório (nota 3,52) e Cama, mesa e banho (3,92)
# vendem muito e avaliam mal. São itens volumosos, com frete caro e maior
# chance de avaria — candidatos naturais a uma revisão de embalagem e de
# expectativa de prazo no anúncio.

# %% [markdown]
# ## 5. O mercado é concentrado?

# %%
concentration = an.concentration_headline(df)
for name, value in concentration.items():
    print(f"{name:.<34} {value:,.4f}")

# %% [markdown]
# Leitura: os 10 maiores vendedores fazem apenas 13,3%, o que parece um
# mercado pulverizado. Mas a curva inteira mostra que 18% dos vendedores geram
# 80% da receita, um Pareto clássico. A leitura de mercado fragmentado só vale
# para o topo absoluto; na prática, um núcleo de ~530 vendedores carrega a
# operação.

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
# Leitura: o Sudeste concentra 65% da receita e SP sozinho, 38%. O contraste
# operacional é grande: no Sudeste o pedido chega em ~10,7 dias com frete médio
# de R$ 17; no Norte são ~22,6 dias e R$ 37 de frete. A nota acompanha:
# 4,11 no Sudeste contra 3,91 no Nordeste.

# %% [markdown]
# ## 7. O insight principal: prazo de entrega x satisfação

# %%
print(an.delivery_vs_review(df))
print()
print(an.late_delivery_impact(df)[
    ["situacao", "pedidos", "nota_media", "perc_nota_1", "perc_nota_5"]
])

# %% [markdown]
# Leitura: este é o achado mais acionável da base.
#
# - Entrega em até 3 dias → nota 4,48
# - Entrega acima de 30 dias → nota 2,24, com 63% de notas 1 ou 2
# - Pedido no prazo → 4,29; pedido atrasado → 2,57
#
# Atrasar custa 1,73 estrela. Como 46% dos pedidos atrasados recebem nota 1, o
# atraso gera detratores ativos além de insatisfação. Apenas 8,1% dos pedidos
# atrasam, então o problema é concentrado e, por isso mesmo, tratável.

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
# O boleto ainda é ~20% dos pedidos, um traço bem brasileiro do dataset.

# %% [markdown]
# ## 9. Quanto pesa o frete?

# %%
print(an.freight_analysis(df)[
    ["customer_region", "tipo_venda", "frete_medio", "frete_sobre_preco", "prazo_medio", "itens"]
])

# %% [markdown]
# Leitura: no Norte o frete equivale a 22,7% do preço do produto, contra
# 13,1% em vendas dentro do próprio estado no Sudeste. Como quase toda venda
# para o Norte/Nordeste é interestadual (sai do Sudeste), o custo logístico
# vira barreira de conversão nessas regiões.

# %% [markdown]
# ---
# ## Conclusões e recomendações
#
# 1. O prazo é o principal fator de satisfação. Reduzir atraso vale mais que
#    qualquer ação de marketing sobre NPS: são 1,73 estrela por pedido atrasado.
# 2. A base de vendedores pede dois trilhos. ~530 vendedores (18%) fazem 80% da
#    receita: gerente de conta para eles, autoatendimento para a cauda.
# 3. Um CD no Nordeste ataca três problemas de uma vez: prazo (20 dias), frete
#    (22% do preço) e nota (3,91, a pior do país).
# 4. As categorias volumosas precisam de atenção. Móveis de escritório e
#    cama/mesa/banho vendem bem e avaliam mal: revisar embalagem e prometer
#    prazos realistas.
# 5. A operação precisa estar pronta para novembro. A Black Friday gera o pico
#    de receita e também o maior risco de atraso e de nota 1.
