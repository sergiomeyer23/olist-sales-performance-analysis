"""Gera o PDF do currículo em formato compatível com ATS.

Decisões tomadas para maximizar a leitura automatizada (ATS/IA):
- Coluna única, fluxo linear de cima para baixo.
- Sem tabelas, caixas de texto, imagens, ícones ou barras de habilidade.
- Fontes padrão (Helvetica), que geram texto selecionável e extraível.
- Títulos de seção convencionais e em caixa alta.

Uso:
    python curriculo/gerar_pdf.py
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

OUT_DIR = Path(__file__).resolve().parent
DARK = HexColor("#1a1a1a")
GRAY = HexColor("#3d3d3d")

# --------------------------------------------------------------------------- #
# DADOS DO CURRÍCULO — edite aqui os campos entre colchetes
# --------------------------------------------------------------------------- #
NOME = "SÉRGIO MEYER"
TITULO = "Analista de Dados | Python | Pandas | SQL | Excel"
CONTATO = [
    "Cascavel, Paraná, Brasil",
    "sergio.gabriel.meyer10@gmail.com | (45) 99909-9340",
    "linkedin.com/in/sérgio-meyer-7aaa45407 | github.com/sergiomeyer23",
]

RESUMO = (
    "Analista de Dados em formação, com foco em análise exploratória de dados, "
    "construção de dashboards e automação de rotinas de dados com Python. Desenvolvi "
    "um projeto completo de análise de e-commerce processando 96 mil pedidos e "
    "R$ 13,2 milhões em vendas, integrando 9 bases de dados em uma tabela analítica e "
    "entregando um dashboard interativo em Streamlit com 6 painéis e 17 visualizações. "
    "Aplico Python, pandas, SQL, Excel e visualização de dados para transformar dados "
    "brutos em indicadores de negócio e recomendações acionáveis. Cursando Tecnologia "
    "em Análise e Desenvolvimento de Sistemas na UNIVEL e em busca da primeira "
    "oportunidade como Analista de Dados Júnior."
)

COMPETENCIAS = [
    ("Análise de Dados", "Python, pandas, NumPy, análise exploratória de dados (EDA), "
                         "ETL, limpeza e tratamento de dados, estatística descritiva, "
                         "análise de séries temporais"),
    ("Visualização e BI", "Plotly, Streamlit, Matplotlib, Excel (tabelas dinâmicas, "
                          "fórmulas, dashboards), storytelling com dados"),
    ("Banco de Dados", "SQL, MySQL, modelagem relacional, consultas e joins"),
    ("Programação", "Python, Java, JavaScript, HTML, CSS"),
    ("Ferramentas e Práticas", "Git, GitHub, Jupyter Notebook, pytest (testes "
                               "automatizados), documentação técnica, versionamento de código"),
    ("Competências Complementares", "pensamento analítico, resolução de problemas, "
                                    "comunicação de resultados para áreas de negócio, "
                                    "aprendizado contínuo"),
]

PROJETOS = [
    {
        "titulo": "Análise de Performance de Vendas — E-commerce Olist",
        "stack": "Python, pandas, Plotly, Streamlit, pytest",
        "link": "github.com/sergiomeyer23/olist-sales-performance-analysis",
        "contexto": "Análise completa de dados de vendas de um marketplace brasileiro, "
                    "com dashboard interativo para exploração dos indicadores por "
                    "período, região e categoria.",
        "bullets": [
            "Integrei 9 bases de dados (pedidos, itens, clientes, vendedores, produtos, "
            "pagamentos e avaliações) em uma tabela analítica única com 109 mil "
            "registros, usando pandas e joins tratados para não duplicar linhas.",
            "Estruturei pipeline de ETL (extração, transformação e carga) com regras de limpeza documentadas (filtro de "
            "pedidos entregues, recorte temporal, deduplicação de avaliações), "
            "reduzindo o tempo de carga com cache em Parquet.",
            "Desenvolvi dashboard em Streamlit com 6 painéis, filtros interativos e 17 "
            "visualizações interativas em Plotly, permitindo análise self-service dos dados.",
            "Identifiquei que pedidos entregues com atraso recebem nota média 2,57 "
            "contra 4,29 dos entregues no prazo — queda de 1,7 estrela que aponta a "
            "logística como principal driver de satisfação do cliente.",
            "Demonstrei, por meio de curva de Pareto, que 18% dos vendedores concentram "
            "80% do faturamento, sustentando recomendação de gestão de contas segmentada.",
            "Implementei 22 testes automatizados com pytest para validar métricas e o "
            "dashboard, identificando e corrigindo falha em cenários de filtro restritivo.",
        ],
    },
    {
        "titulo": "Retail Sales Analyzer — Relatório Automatizado de Vendas",
        "stack": "Python",
        "link": "github.com/sergiomeyer23/retail-sales-analyzer",
        "contexto": "Script de análise de vendas a partir de arquivos CSV, com geração "
                    "automática de relatório gerencial.",
        "bullets": [
            "Automatizei a leitura e o processamento de arquivos CSV de vendas, "
            "calculando total faturado, ticket médio e volume de itens sem intervenção manual.",
            "Implementei identificação de produtos de maior e menor preço e de maior "
            "receita, além de filtro configurável por valor mínimo.",
            "Desenvolvi tratamento de erros por arquivo, coluna e valor, garantindo "
            "execução estável mesmo com dados inconsistentes na origem.",
        ],
    },
    {
        "titulo": "Fundamentos de pandas — Laboratório de Manipulação de Dados",
        "stack": "Python, pandas",
        "link": "github.com/sergiomeyer23/pandas-fundamentos",
        "contexto": "Conjunto de exercícios práticos cobrindo o fluxo completo de "
                    "tratamento de dados.",
        "bullets": [
            "Pratiquei leitura, limpeza, filtros, groupby, merge, manipulação de datas e "
            "exportação de resultados, concluindo os 12 exercícios propostos.",
            "Consolidei a base técnica de pandas aplicada posteriormente nos projetos de análise.",
        ],
    },
    {
        "titulo": "Personal Finance API — API REST de Controle Financeiro",
        "stack": "Java 21, Spring Boot, Spring Data JPA, MySQL",
        "link": "github.com/sergiomeyer23/personal-finance-api",
        "contexto": "API REST para gestão de finanças pessoais, com modelagem de dados "
                    "relacional.",
        "bullets": [
            "Modelei as entidades Usuário, Conta, Categoria e Transação com Spring Data "
            "JPA e MySQL, aplicando relacionamentos e validação de dados.",
            "Estruturei o projeto em camadas (controller, entity, repository) seguindo o "
            "padrão MVC, com build gerenciado por Maven.",
        ],
    },
]

FORMACAO = [
    ("Tecnologia em Análise e Desenvolvimento de Sistemas — UNIVEL",
     "Cursando | Previsão de conclusão: dezembro de 2029"),
]

CURSOS = [
    "Estudos contínuos em análise de dados com Python e pandas, com projetos práticos "
    "publicados no GitHub",
    "Fundamentos de SQL e modelagem de banco de dados relacional",
    "Visualização de dados e construção de dashboards (Plotly, Streamlit, Excel)",
]

IDIOMAS = [
    "<b>Português:</b> nativo",
    "<b>Inglês:</b> intermediário (B1) — leitura de documentação técnica",
]


# --------------------------------------------------------------------------- #
# Estilos
# --------------------------------------------------------------------------- #
def build_styles() -> dict[str, ParagraphStyle]:
    return {
        "nome": ParagraphStyle(
            "nome", fontName="Helvetica-Bold", fontSize=19, leading=23,
            textColor=DARK, spaceAfter=2,
        ),
        "titulo": ParagraphStyle(
            "titulo", fontName="Helvetica", fontSize=11.5, leading=14,
            textColor=GRAY, spaceAfter=6,
        ),
        "contato": ParagraphStyle(
            "contato", fontName="Helvetica", fontSize=9.2, leading=12.5,
            textColor=GRAY,
        ),
        "secao": ParagraphStyle(
            "secao", fontName="Helvetica-Bold", fontSize=11, leading=13,
            textColor=DARK, spaceBefore=11, spaceAfter=3,
        ),
        "corpo": ParagraphStyle(
            "corpo", fontName="Helvetica", fontSize=9.4, leading=12.8,
            textColor=DARK, alignment=TA_JUSTIFY,
        ),
        "proj_titulo": ParagraphStyle(
            "proj_titulo", fontName="Helvetica-Bold", fontSize=9.9, leading=12.5,
            textColor=DARK, spaceBefore=6,
        ),
        "proj_meta": ParagraphStyle(
            "proj_meta", fontName="Helvetica-Oblique", fontSize=8.8, leading=11.5,
            textColor=GRAY, spaceAfter=1,
        ),
        "bullet": ParagraphStyle(
            "bullet", fontName="Helvetica", fontSize=9.2, leading=12.3,
            textColor=DARK, alignment=TA_JUSTIFY,
        ),
    }


def section(title: str, styles: dict) -> list:
    """Título de seção com uma linha horizontal simples (não é tabela)."""
    return [
        Paragraph(title, styles["secao"]),
        HRFlowable(width="100%", thickness=0.7, color=HexColor("#9a9a9a"),
                   spaceBefore=1, spaceAfter=5),
    ]


def bullets(items: list[str], styles: dict) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(text, styles["bullet"]), leftIndent=11) for text in items],
        bulletType="bullet", start="•", leftIndent=11, bulletFontSize=8,
        spaceBefore=1, spaceAfter=1,
    )


def build_pdf(path: Path) -> None:
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.3 * cm, bottomMargin=1.3 * cm,
        title="Sérgio Meyer - Analista de Dados",
        author="Sérgio Meyer",
        subject="Currículo - Analista de Dados",
        keywords="Analista de Dados, Python, pandas, SQL, Excel, Power BI, Streamlit, "
                 "Plotly, análise de dados, dashboard, ETL",
    )

    story: list = []

    # Cabeçalho
    story.append(Paragraph(NOME, styles["nome"]))
    story.append(Paragraph(TITULO, styles["titulo"]))
    for line in CONTATO:
        story.append(Paragraph(line, styles["contato"]))

    # Resumo
    story += section("RESUMO PROFISSIONAL", styles)
    story.append(Paragraph(RESUMO, styles["corpo"]))

    # Competências
    story += section("COMPETÊNCIAS TÉCNICAS", styles)
    for categoria, itens in COMPETENCIAS:
        story.append(Paragraph(f"<b>{categoria}:</b> {itens}", styles["corpo"]))
        story.append(Spacer(1, 2.5))

    # Projetos
    story += section("PROJETOS", styles)
    for proj in PROJETOS:
        story.append(Paragraph(proj["titulo"], styles["proj_titulo"]))
        story.append(Paragraph(f"{proj['stack']} | {proj['link']}", styles["proj_meta"]))
        story.append(Paragraph(proj["contexto"], styles["corpo"]))
        story.append(Spacer(1, 2))
        story.append(bullets(proj["bullets"], styles))

    # Formação
    story += section("FORMAÇÃO ACADÊMICA", styles)
    for curso, detalhe in FORMACAO:
        story.append(Paragraph(f"<b>{curso}</b>", styles["corpo"]))
        story.append(Paragraph(detalhe, styles["corpo"]))

    # Cursos
    story += section("CURSOS E DESENVOLVIMENTO COMPLEMENTAR", styles)
    story.append(bullets(CURSOS, styles))

    # Idiomas
    story += section("IDIOMAS", styles)
    for idioma in IDIOMAS:
        story.append(Paragraph(idioma, styles["corpo"]))

    doc.build(story)


if __name__ == "__main__":
    output = OUT_DIR / "Sergio_Meyer_CV_Analista_de_Dados.pdf"
    build_pdf(output)
    print(f"PDF gerado: {output}")
