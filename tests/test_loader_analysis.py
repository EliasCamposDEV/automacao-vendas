from __future__ import annotations

import pandas as pd
import pytest

from toolkit.analysis import (
    compute_kpis,
    revenue_by_dimension,
    revenue_by_month,
    top_products,
)
from toolkit.loader import REQUIRED_COLUMNS, clean_sales, load_sales


@pytest.fixture
def raw_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["2025-01-05", "PED-001", "Notebook", "Informatica", "Site", 2, 1000, "CE"],
            ["2025-01-06", "PED-002", "Mouse", "Perifericos", "Loja", 1, 50, "SP"],
            ["2025-01-05", "PED-001", "Notebook", "Informatica", "Site", 3, 900, "CE"],
            ["2025-02-01", "PED-003", "Monitor", "Monitores", "Site", 1, 800, "RJ"],
            ["2025-02-02", "PED-004", "Teclado", "Perifericos", "Site", 0, 200, "MG"],
            ["2025-02-03", "PED-005", "", "Perifericos", "Site", 1, 100, "BA"],
            ["31/02/2025", "PED-006", "Cabo", "Acessorios", "Site", 1, 30, "PE"],
        ],
        columns=REQUIRED_COLUMNS,
    )


@pytest.fixture
def clean_frame(raw_frame: pd.DataFrame) -> pd.DataFrame:
    frame, _ = clean_sales(raw_frame)
    return frame


def test_clean_sales_removes_invalid_and_duplicate_rows(raw_frame: pd.DataFrame) -> None:
    _, report = clean_sales(raw_frame)

    assert report.input_rows == 7
    assert report.output_rows == 3
    assert report.removed_invalid == 3
    assert report.removed_duplicates == 1
    assert report.removed_rows == 4


def test_clean_sales_adds_derived_columns_and_normalizes_text(raw_frame: pd.DataFrame) -> None:
    manual = raw_frame.copy()
    manual.loc[0, "produto"] = "  Notebook  "
    frame, _ = clean_sales(manual)

    assert frame.loc[0, "produto"] == "Notebook"
    assert frame.loc[0, "receita"] == 2000.0
    assert frame.loc[0, "mes"] == "2025-01"
    assert frame["data"].dtype.kind == "M"


def test_clean_sales_rejects_missing_columns(raw_frame: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="Colunas obrigatorias ausentes"):
        clean_sales(raw_frame.drop(columns=["estado"]))


def test_load_sales_reads_csv_and_load_missing_file(tmp_path, raw_frame: pd.DataFrame) -> None:
    csv_path = tmp_path / "vendas.csv"
    raw_frame.to_csv(csv_path, index=False)

    frame, report = load_sales(csv_path)
    assert len(frame) == 3
    assert report.input_rows == 7

    with pytest.raises(FileNotFoundError):
        load_sales(tmp_path / "nao-existe.csv")


def test_analysis_kpis(clean_frame: pd.DataFrame) -> None:
    kpis = compute_kpis(clean_frame)

    assert kpis["receita_total"] == 2850.0
    assert kpis["pedidos"] == 3
    assert kpis["itens_vendidos"] == 4
    assert kpis["ticket_medio"] == 950.0
    assert kpis["preco_medio_item"] == 712.5
    assert kpis["produtos_vendidos"] == 3
    assert kpis["crescimento_ultimo_mes_pct"] == -60.98


def test_revenue_by_month(clean_frame: pd.DataFrame) -> None:
    monthly = revenue_by_month(clean_frame)

    assert list(monthly["mes"]) == ["2025-01", "2025-02"]
    assert list(monthly["receita"]) == [2050.0, 800.0]
    assert list(monthly["pedidos"]) == [2, 1]


def test_top_products_and_limit(clean_frame: pd.DataFrame) -> None:
    products = top_products(clean_frame, limit=2)

    assert len(products) == 2
    assert products.iloc[0]["produto"] == "Notebook"
    assert products.iloc[0]["receita"] == 2000.0

    with pytest.raises(ValueError):
        top_products(clean_frame, limit=0)


def test_revenue_by_dimension_share(clean_frame: pd.DataFrame) -> None:
    categories = revenue_by_dimension(clean_frame, "categoria")

    assert categories["participacao_pct"].sum() == pytest.approx(100.0)
    assert categories.iloc[0]["categoria"] == "Informatica"

    with pytest.raises(ValueError):
        revenue_by_dimension(clean_frame, "inexistente")


def test_analysis_rejects_empty_data(clean_frame: pd.DataFrame) -> None:
    empty = clean_frame.iloc[0:0]
    with pytest.raises(ValueError, match="Nao ha dados"):
        compute_kpis(empty)
