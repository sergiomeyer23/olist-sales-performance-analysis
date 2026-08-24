# Currículo — Sérgio Meyer

Currículo em formato otimizado para ATS (Applicant Tracking Systems), alvo: **Analista de Dados Júnior**.

## Arquivos

| Arquivo | Uso |
|---|---|
| `Sergio_Meyer_CV_Analista_de_Dados.pdf` | Versão para envio em candidaturas |
| `Sergio_Meyer_CV_Analista_de_Dados.md` | Fonte em texto, fácil de editar e copiar para formulários |
| `gerar_pdf.py` | Script que gera o PDF a partir dos dados no topo do arquivo |

## Como editar e regerar

Os dados ficam em constantes no topo de `gerar_pdf.py` (NOME, TITULO, RESUMO,
COMPETENCIAS, PROJETOS, FORMACAO, IDIOMAS). Edite e rode:

```bash
pip install reportlab
python curriculo/gerar_pdf.py
```

## Dados pessoais

Os dados pessoais já estão preenchidos em `gerar_pdf.py`. Ao mudar de contato,
curso ou telefone, edite as constantes `CONTATO` e `FORMACAO` e regere o PDF.


## Decisões tomadas para compatibilidade com ATS

- **Coluna única** e fluxo linear, sem tabelas, caixas de texto ou posicionamento livre.
- **Sem imagens, ícones, gráficos ou barras de habilidade** — o PDF contém 0 imagens.
- **Texto 100% selecionável**: a extração automática recupera ~5.000 caracteres na ordem correta.
- **Títulos de seção convencionais**: Resumo Profissional, Competências Técnicas,
  Projetos, Formação Acadêmica, Idiomas.
- **Fontes padrão** (Helvetica), que não quebram a extração de texto.
- **Metadados do PDF** preenchidos com título, autor e palavras-chave da área.
- **2 páginas**, dentro do limite recomendado.

## Verificação automatizada

Para conferir como um ATS lê o arquivo:

```bash
pip install pypdf
python -c "
from pypdf import PdfReader
r = PdfReader('curriculo/Sergio_Meyer_CV_Analista_de_Dados.pdf')
print('\n'.join(p.extract_text() for p in r.pages))
"
```

## Adaptação por vaga

Este é o **currículo-base para vagas de dados**. Para cada candidatura:

1. Leia a descrição da vaga e liste as palavras-chave técnicas.
2. Ajuste o `TITULO` para espelhar o nome do cargo anunciado.
3. Reordene as categorias em `COMPETENCIAS`, colocando primeiro o que a vaga pede.
4. Inclua no `RESUMO` os termos exatos da vaga **que forem verdadeiros**.
5. Se a vaga pedir Power BI e você ainda não usa, não inclua — priorize aprender e
   depois adicionar.
