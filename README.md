# Automação e Análise de Vendas

[![CI](https://github.com/EliasCamposDEV/automacao-vendas/actions/workflows/ci.yml/badge.svg)](https://github.com/EliasCamposDEV/automacao-vendas/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/github/license/EliasCamposDEV/automacao-vendas)](LICENSE)

Toolkit em Python 3.11+ para organizar arquivos e analisar vendas, gerando relatório Excel com gráficos.

## Instalar

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## Analisar vendas

```bash
python -m toolkit analyze data/vendas.csv --top 5
```

Limpa o CSV (remove linhas inválidas e duplicatas), calcula KPIs e agregações por mês, produto, categoria e canal. Saída em texto ou JSON (`--json`).

## Gerar relatório Excel

```bash
python -m toolkit report data/vendas.csv -o reports/relatorio_vendas.xlsx
```

Gera abas de resumo, receita mensal, top produtos, categorias, canais e dados tratados, com gráficos.

## Organizar arquivos

```bash
python -m toolkit organize "C:\Downloads"          # simulação (dry-run)
python -m toolkit organize "C:\Downloads" --apply  # executa
python -m toolkit organize "C:\Downloads" -d "C:\Arquivos" --apply
```

Move arquivos para pastas por categoria (Imagens, Documentos, Planilhas, Código, Arquivos, Mídia, Outros). Dry-run por padrão.

## Testes

```bash
python -m pytest
ruff check .
```

17 testes cobrem limpeza, KPIs, agregações, geração do Excel e organização de arquivos.

## Recriar a base de exemplo

```bash
python scripts/gerar_dados_exemplo.py
```

Usa `random.Random(42)`, então a base é reproduzível. O CSV incluído tem 10 linhas sujas de propósito (5 duplicatas e 5 inválidas) para demonstrar a limpeza.

## Regras de limpeza

Remove linhas com data inválida/vazia, quantidade ou preço <= 0, campos obrigatórios vazios (`pedido_id`, `produto`, `categoria`, `canal`, `estado`) e duplicatas do par `(pedido_id, produto)`, mantendo a primeira ocorrência. Depois calcula `receita = quantidade * preço_unitario` e `mes` no formato `AAAA-MM`.

## Estrutura

```
automacao-vendas/
├── data/vendas.csv
├── scripts/gerar_dados_exemplo.py
├── toolkit/          # loader, analysis, report, organizer, cli
├── tests/
└── reports/          # saída (ignorada pelo Git)
```