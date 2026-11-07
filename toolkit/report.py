"""Geracao de relatorio Excel formatado com graficos."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .analysis import (
    compute_kpis,
    revenue_by_dimension,
    revenue_by_month,
    top_products,
)

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(color="FFFFFF", bold=True)
HEADER_ALIGNMENT = Alignment(horizontal="center", vertical="center")
CURRENCY_FORMAT = 'R$ #,##0.00'
INTEGER_FORMAT = "#,##0"
PERCENT_FORMAT = '0.00"%"'
DATE_FORMAT = "dd/mm/yyyy"


def generate_excel_report(
    frame: pd.DataFrame,
    output_path: str | Path,
    *,
    top_limit: int = 5,
) -> Path:
    """Gera um arquivo .xlsx com resumo, graficos e dados tratados."""
    if frame.empty:
        raise ValueError("Nao ha dados para gerar o relatorio")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    kpis = compute_kpis(frame)
    monthly = revenue_by_month(frame).rename(
        columns={
            "mes": "Mês",
            "receita": "Receita (R$)",
            "pedidos": "Pedidos",
            "itens": "Itens",
        }
    )
    products = top_products(frame, limit=top_limit).rename(
        columns={
            "produto": "Produto",
            "categoria": "Categoria",
            "receita": "Receita (R$)",
            "itens": "Itens",
            "pedidos": "Pedidos",
        }
    )[["Produto", "Receita (R$)", "Categoria", "Itens", "Pedidos"]]
    categories = revenue_by_dimension(frame, "categoria").rename(
        columns={
            "categoria": "Categoria",
            "receita": "Receita (R$)",
            "itens": "Itens",
            "pedidos": "Pedidos",
            "participacao_pct": "Participação (%)",
        }
    )
    channels = revenue_by_dimension(frame, "canal").rename(
        columns={
            "canal": "Canal",
            "receita": "Receita (R$)",
            "itens": "Itens",
            "pedidos": "Pedidos",
            "participacao_pct": "Participação (%)",
        }
    )
    details = frame.rename(
        columns={
            "data": "Data",
            "pedido_id": "Pedido",
            "produto": "Produto",
            "categoria": "Categoria",
            "canal": "Canal",
            "quantidade": "Quantidade",
            "preco_unitario": "Preço unitário (R$)",
            "estado": "Estado",
            "receita": "Receita (R$)",
            "mes": "Mês",
        }
    )

    summary = pd.DataFrame(
        {
            "Indicador": [
                "Receita total (R$)",
                "Pedidos",
                "Itens vendidos",
                "Ticket médio (R$)",
                "Preço médio por item (R$)",
                "Produtos vendidos",
                "Crescimento do último mês (%)",
            ],
            "Valor": [
                kpis["receita_total"],
                kpis["pedidos"],
                kpis["itens_vendidos"],
                kpis["ticket_medio"],
                kpis["preco_medio_item"],
                kpis["produtos_vendidos"],
                kpis["crescimento_ultimo_mes_pct"],
            ],
        }
    )

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Resumo", index=False)
        monthly.to_excel(writer, sheet_name="Receita Mensal", index=False)
        products.to_excel(writer, sheet_name="Top Produtos", index=False)
        categories.to_excel(writer, sheet_name="Categorias", index=False)
        channels.to_excel(writer, sheet_name="Canais", index=False)
        details.to_excel(writer, sheet_name="Dados", index=False)

        workbook = writer.book

        summary_sheet = workbook["Resumo"]
        _style_header(summary_sheet)
        summary_sheet.freeze_panes = "A2"
        summary_sheet.column_dimensions["A"].width = 36
        summary_sheet.column_dimensions["B"].width = 20
        for row in range(2, summary_sheet.max_row + 1):
            cell = summary_sheet.cell(row=row, column=2)
            label = str(summary_sheet.cell(row=row, column=1).value)
            if "(R$)" in label:
                cell.number_format = CURRENCY_FORMAT
            elif "(%)" in label:
                cell.number_format = PERCENT_FORMAT
            else:
                cell.number_format = INTEGER_FORMAT
            cell.alignment = Alignment(horizontal="right")
            if row % 2 == 0:
                summary_sheet.cell(row=row, column=1).fill = PatternFill("solid", fgColor="EAF1F8")
                cell.fill = PatternFill("solid", fgColor="EAF1F8")

        _style_table(monthly_sheet := workbook["Receita Mensal"])
        _style_table(products_sheet := workbook["Top Produtos"])
        _style_table(workbook["Categorias"])
        _style_table(workbook["Canais"])
        _style_table(workbook["Dados"])

        _add_bar_chart(
            monthly_sheet,
            title="Receita por mês",
            y_title="Receita (R$)",
            value_column=2,
            anchor="F2",
            horizontal=False,
        )
        _add_bar_chart(
            products_sheet,
            title=f"Top {top_limit} produtos por receita",
            y_title="Receita (R$)",
            value_column=2,
            anchor="H2",
            horizontal=True,
        )

    return output


def _style_header(sheet) -> None:
    for cell in sheet[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = HEADER_ALIGNMENT
    sheet.row_dimensions[1].height = 22


def _style_table(sheet) -> None:
    _style_header(sheet)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions

    formats = {
        "Receita (R$)": CURRENCY_FORMAT,
        "Preço unitário (R$)": CURRENCY_FORMAT,
        "Participação (%)": PERCENT_FORMAT,
        "Pedidos": INTEGER_FORMAT,
        "Itens": INTEGER_FORMAT,
        "Quantidade": INTEGER_FORMAT,
        "Data": DATE_FORMAT,
    }

    headers = {cell.column: str(cell.value) for cell in sheet[1]}
    for column_index, header in headers.items():
        number_format = formats.get(header)
        if number_format:
            for row in range(2, sheet.max_row + 1):
                sheet.cell(row=row, column=column_index).number_format = number_format

    for column_index in range(1, sheet.max_column + 1):
        letter = get_column_letter(column_index)
        max_length = len(headers.get(column_index, ""))
        for row in range(2, min(sheet.max_row, 100) + 1):
            value = sheet.cell(row=row, column=column_index).value
            if value is not None:
                max_length = max(max_length, len(str(value)))
        sheet.column_dimensions[letter].width = min(max(max_length + 2, 12), 42)


def _add_bar_chart(
    sheet,
    *,
    title: str,
    y_title: str,
    value_column: int,
    anchor: str,
    horizontal: bool,
) -> None:
    chart = BarChart()
    chart.type = "bar" if horizontal else "col"
    chart.style = 10
    chart.title = title
    chart.y_axis.title = y_title
    chart.x_axis.title = None
    chart.height = 9
    chart.width = 20

    data = Reference(
        sheet,
        min_col=value_column,
        min_row=1,
        max_row=sheet.max_row,
    )
    categories = Reference(
        sheet,
        min_col=1,
        min_row=2,
        max_row=sheet.max_row,
    )
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(categories)
    chart.legend = None

    sheet.add_chart(chart, anchor)
