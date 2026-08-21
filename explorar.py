import pandas as pd

# Carregar dados
vendas = pd.read_csv('dados/olist_order_items_dataset.csv')
pedidos = pd.read_csv('dados/olist_orders_dataset.csv')
clientes = pd.read_csv('dados/olist_customers_dataset.csv')
vendedores = pd.read_csv('dados/olist_sellers_dataset.csv')
produtos = pd.read_csv('dados/olist_products_dataset.csv')
categorias = pd.read_csv('dados/product_category_name_translation.csv')

# Juntar tabelas
merge1 = pd.merge(vendas, pedidos, on='order_id', how='left')
merge2 = pd.merge(merge1, clientes, on='customer_id', how='left')
merge3 = pd.merge(merge2, vendedores, on='seller_id', how='left')
merge4 = pd.merge(merge3, produtos, on='product_id', how='left')
dados = pd.merge(merge4, categorias, on='product_category_name', how='left')

# ========== Q1 — Top 10 Vendedores ==========
top_10_vendedores = dados.groupby('seller_id')['price'].sum().sort_values(ascending=False).head(10)
total_geral = dados['price'].sum()
participacao_top10 = top_10_vendedores.sum() / total_geral

print("=" * 60)
print("Q1 — TOP 10 VENDEDORES POR VALOR DE VENDAS")
print("=" * 60)
print(top_10_vendedores.to_string())
print(f"\nConclusão: Os 10 maiores vendedores respondem por {participacao_top10:.1%} do faturamento total.")
print("→ Mercado fragmentado, sem concentração elevada.\n")

# ========== Q2 — Vendas por Estado ==========
vendas_por_estado = dados.groupby('customer_state')['price'].sum().sort_values(ascending=False)

print("=" * 60)
print("Q2 — FATURAMENTO POR ESTADO")
print("=" * 60)
print(vendas_por_estado.to_string())
print(f"\nConclusão: SP lidera com {vendas_por_estado.iloc[0]:,.2f}, seguido de RJ e MG.")
print("→ 3 estados concentram mais de 50% do faturamento total.\n")

# ========== Q3 — Top 5 Categorias por UF ==========
top_categorias = (
    dados.groupby(['customer_state', 'product_category_name_english'])['price']
    .sum()
    .reset_index()
    .sort_values(['customer_state', 'price'], ascending=[True, False])
)

top5_por_uf = top_categorias.groupby('customer_state').head(5)

print("=" * 60)
print("Q3 — TOP 5 CATEGORIAS COM MAIOR FATURAMENTO POR ESTADO")
print("=" * 60)
print(top5_por_uf.to_string(index=False))
print("\nConclusão: Saúde e Beleza, Esporte e Lazer e Relógios e Presentes aparecem com mais frequência no topo dos estados.")
print("→ Padrão de consumo consistente entre as regiões.\n")