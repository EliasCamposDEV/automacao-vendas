"""Interface de linha de comando do toolkit."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .analysis import (
    compute_kpis,
    dataframe_to_records,
    revenue_by_month,
    top_products,
)
from .loader import load_sales
from .organizer import organize
from .report import generate_excel_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="toolkit",
        description="Automacao de arquivos e analise de dados de vendas.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analisa um CSV de vendas")
    analyze.add_argument("csv", type=Path, help="Caminho do CSV de vendas")
    analyze.add_argument("--top", type=int, default=5, help="Quantidade de produtos no ranking")
    analyze.add_argument("--json", action="store_true", help="Imprime o resultado em JSON")

    report = subparsers.add_parser("report", help="Gera um relatorio Excel")
    report.add_argument("csv", type=Path, help="Caminho do CSV de vendas")
    report.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("reports/relatorio_vendas.xlsx"),
        help="Arquivo .xlsx de saida",
    )
    report.add_argument("--top", type=int, default=5, help="Quantidade de produtos no ranking")

    organize_parser = subparsers.add_parser(
        "organize",
        help="Organiza arquivos em pastas por categoria (simulacao por padrao)",
    )
    organize_parser.add_argument("path", type=Path, help="Diretorio a organizar")
    organize_parser.add_argument(
        "-d",
        "--destination",
        type=Path,
        default=None,
        help="Diretorio de destino (padrao: o mesmo diretorio de origem)",
    )
    organize_parser.add_argument(
        "--apply",
        action="store_true",
        help="Executa a movimentacao; sem esta flag apenas simula",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "analyze":
            return _run_analyze(args)
        if args.command == "report":
            return _run_report(args)
        if args.command == "organize":
            return _run_organize(args)
    except (FileNotFoundError, ValueError, OSError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1

    parser.error("Comando invalido")
    return 2


def _run_analyze(args: argparse.Namespace) -> int:
    frame, cleaning = load_sales(args.csv)
    kpis = compute_kpis(frame)
    products = top_products(frame, limit=args.top)
    monthly = revenue_by_month(frame)

    if args.json:
        payload = {
            "limpeza": cleaning.as_dict(),
            "kpis": kpis,
            "top_produtos": dataframe_to_records(products),
            "receita_mensal": dataframe_to_records(monthly),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Analise de vendas")
    print(
        f"Limpeza: {cleaning.input_rows} -> {cleaning.output_rows} linhas "
        f"({cleaning.removed_invalid} invalidas, {cleaning.removed_duplicates} duplicadas)"
    )
    print(f"Receita total: {_brl(kpis['receita_total'])}")
    print(
        f"Pedidos: {kpis['pedidos']} | Itens: {kpis['itens_vendidos']} | "
        f"Ticket medio: {_brl(kpis['ticket_medio'])}"
    )
    growth = kpis["crescimento_ultimo_mes_pct"]
    growth_text = "N/A" if growth is None else f"{growth:+.2f}%"
    print(f"Produtos diferentes: {kpis['produtos_vendidos']} | Crescimento do ultimo mes: {growth_text}")

    print(f"\nTop {args.top} produtos por receita:")
    for position, row in enumerate(products.itertuples(index=False), start=1):
        print(f"  {position}. {row.produto} ({row.categoria}) - {_brl(row.receita)} | {row.itens} itens")

    print("\nUltimos meses:")
    for row in monthly.tail(6).itertuples(index=False):
        print(f"  {row.mes}: {_brl(row.receita)} | {row.pedidos} pedidos")

    return 0


def _run_report(args: argparse.Namespace) -> int:
    frame, cleaning = load_sales(args.csv)
    output = generate_excel_report(frame, args.output, top_limit=args.top)

    print(f"Relatorio gerado em: {output.resolve()}")
    print(
        f"Linhas analisadas: {cleaning.output_rows} | "
        f"ignoradas: {cleaning.removed_rows} | "
        f"receita total: {_brl(frame['receita'].sum())}"
    )
    return 0


def _run_organize(args: argparse.Namespace) -> int:
    result = organize(args.path, args.destination, apply=args.apply)
    destination_root = args.destination.resolve() if args.destination else args.path.resolve()

    action = "Organizacao executada" if result.applied else "Simulacao de organizacao"
    print(f"{action} em: {destination_root}")

    if not result.moves:
        print("Nenhum arquivo encontrado para organizar.")
        return 0

    for move in result.moves:
        print(f"  {move.source.name} -> {move.category}/{move.destination.name}")

    print(f"\n{len(result.moves)} arquivos ({_size(result.total_bytes)})")
    print("Categorias: " + ", ".join(f"{name}: {count}" for name, count in result.categories.items()))

    if not result.applied:
        print("Nada foi movido. Use --apply para executar.")
    return 0


def _brl(value: float) -> str:
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def _size(total_bytes: int) -> str:
    if total_bytes < 1024:
        return f"{total_bytes} B"
    if total_bytes < 1024 * 1024:
        return f"{total_bytes / 1024:.1f} KB"
    return f"{total_bytes / (1024 * 1024):.1f} MB"


if __name__ == "__main__":
    raise SystemExit(main())
