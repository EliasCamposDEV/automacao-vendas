# Automação e Análise de Vendas

Toolkit em **Python 3.11+** para automatizar a organização de arquivos e analisar dados de vendas, gerando relatórios Excel formatados com gráficos.

Projeto do portfólio baseado no item **“Scripts de Automação e Análise de Dados | Python”** do currículo.

## Funcionalidades

### Análise de dados
- Leitura de CSV com validação de colunas obrigatórias
- Limpeza de dados: campos vazios, datas inválidas, quantidades/preços inválidos e duplicatas
- KPIs: receita, pedidos, itens, ticket médio, preço médio, produtos e crescimento mensal
- Agregações por mês, produto, categoria e canal
- Ranking de produtos por receita
- Saída em texto amigável ou JSON para automações

### Relatório Excel
- Planilha `Resumo` com KPIs formatados em reais/percentual
- Abas de receita mensal, top produtos, categorias e canais
- Aba `Dados` com os registros tratados
- Cabeçalhos estilizados, filtros, painéis congelados e formatos numéricos
- Gráficos de barras de receita mensal e top produtos

### Automação de arquivos
- Organização por categoria: Imagens, Documentos, Planilhas, Código, Arquivos, Mídia e Outros
- **Simulação por padrão** (dry-run): nada é movido sem `--apply`
- Resolução automática de nomes duplicados (`foto (1).png`)
- Funciona com diretório de destino separado

## Stack

| Área | Tecnologia |
|---|---|
| Linguagem | Python 3.11+ |
| Dados | pandas |
| Excel | openpyxl |
| Testes | pytest |
| Qualidade | ruff |
| Empacotamento | pyproject.toml + setuptools |

## Estrutura

```text
automacao-vendas/
├── data/
│   └── vendas.csv                 # Base de exemplo (2025)
├── scripts/
│   └── gerar_dados_exemplo.py     # Gera a base com seed fixa
├── toolkit/
│   ├── loader.py                  # Leitura + limpeza
│   ├── analysis.py                # KPIs e agregações
│   ├── report.py                  # Relatório Excel + gráficos
│   ├── organizer.py               # Automação de arquivos
│   ├── cli.py                     # Interface de linha de comando
│   └── __main__.py
├── tests/
│   ├── test_loader_analysis.py
│   ├── test_report_organizer.py
│   └── test_cli.py
├── reports/                       # Saída dos relatórios (ignorada pelo Git)
└── pyproject.toml
```

## Como rodar

### Pré-requisitos

- Python 3.11+

```bash
python -m venv .venv
```

```powershell
# Windows PowerShell (sem ativar o venv, evita bloqueio de scripts)
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m toolkit analyze data/vendas.csv
```

```bash
# Linux/macOS
source .venv/bin/activate
pip install -e ".[dev]"
```

Se preferir ativar o venv no Windows, use
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` antes de
`.\.venv\Scripts\Activate.ps1`.

### Analisar vendas

```bash
python -m toolkit analyze data/vendas.csv --top 5
```

Saída do exemplo incluído:

```text
Analise de vendas
Limpeza: 691 -> 681 linhas (5 invalidas, 5 duplicadas)
Receita total: R$ 1.098.603,40
Pedidos: 340 | Itens: 1198 | Ticket medio: R$ 3.231,19
Produtos diferentes: 12 | Crescimento do ultimo mes: -37.86%

Top 5 produtos por receita:
  1. Notebook Pro 14 (Informatica) - R$ 440.688,70 | 113 itens
  2. Monitor 27 polegadas (Monitores) - R$ 231.678,00 | 122 itens
  3. Cadeira Ergonomica (Escritorio) - R$ 173.884,00 | 116 itens
  4. Mesa Digitalizadora (Perifericos) - R$ 52.326,00 | 114 itens
  5. SSD 1TB (Componentes) - R$ 47.841,30 | 87 itens
```

O CSV de exemplo contém **10 linhas sujas de propósito** (5 duplicatas e 5 inválidas) para demonstrar a etapa de limpeza.

### Gerar relatório Excel

```bash
python -m toolkit report data/vendas.csv -o reports/relatorio_vendas.xlsx
```

O arquivo é criado em `reports/relatorio_vendas.xlsx` e pode ser aberto no Excel, LibreOffice ou Google Sheets.

### Saída JSON (para automações)

```bash
python -m toolkit analyze data/vendas.csv --json
```

```json
{
  "limpeza": {
    "linhas_entrada": 691,
    "linhas_saida": 681,
    "removidas_invalidas": 5,
    "removidas_duplicadas": 5
  },
  "kpis": {
    "receita_total": 1098603.4,
    "pedidos": 340,
    "itens_vendidos": 1198,
    "ticket_medio": 3231.19,
    "crescimento_ultimo_mes_pct": -37.86
  }
}
```

### Organizar arquivos

```bash
# Simula (não move nada)
python -m toolkit organize "C:\Downloads"

# Executa de fato
python -m toolkit organize "C:\Downloads" --apply

# Move para outro diretório
python -m toolkit organize "C:\Downloads" -d "C:\Arquivos" --apply
```

Exemplo de simulação:

```text
Simulacao de organizacao em: C:\Downloads
  foto.jpg -> Imagens/foto.jpg
  contrato.pdf -> Documentos/contrato.pdf
  vendas.xlsx -> Planilhas/vendas.xlsx
  backup.zip -> Arquivos/backup.zip

4 arquivos (2.3 MB)
Categorias: Arquivos: 1, Documentos: 1, Imagens: 1, Planilhas: 1
Nada foi movido. Use --apply para executar.
```

## Regras de limpeza

O comando remove linhas que tenham:

- data inválida ou vazia
- quantidade menor ou igual a zero
- preço unitário menor ou igual a zero
- campos de texto obrigatórios vazios (`pedido_id`, `produto`, `categoria`, `canal`, `estado`)
- duplicata do par `(pedido_id, produto)`, mantendo a primeira ocorrência

Depois calcula `receita = quantidade × preço_unitario` e `mes` no formato `AAAA-MM`.

## Testes

```bash
python -m pytest
```

17 testes cobrem limpeza, KPIs, agregações, geração do Excel (abas e gráficos), organização de arquivos (dry-run, execução, colisões) e CLI.

Qualidade de código:

```bash
ruff check .
```

## Recriar a base de exemplo

```bash
python scripts/gerar_dados_exemplo.py
```

O gerador usa `random.Random(42)`, então a base é reproduzível.

## Decisões técnicas

- **Limpeza separada da análise**: `loader.py` devolve um `CleaningReport`, tornando a etapa auditável.
- **Funções puras de análise**: recebem DataFrame e devolvem dados, sem efeitos colaterais.
- **Excel real com openpyxl**: gráficos e formatação nativos, sem depender de serviços externos.
- **Dry-run por padrão**: operações destrutivas em arquivos exigem `--apply`.
- **CLI com `argparse`**: sem dependências extras; fácil de agendar com Agendador de Tarefas/cron.
- **JSON na análise**: permite integrar o toolkit com dashboards, APIs ou pipelines.

## Próximos passos sugeridos

- Suporte a múltiplos arquivos CSV/Parquet
- Exportar também em PDF
- Agendamento automático com cron/Task Scheduler
- Testes de performance com bases maiores
- Empacotar com Docker ou publicar no PyPI
