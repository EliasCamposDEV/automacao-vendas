from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from toolkit.loader import clean_sales
from toolkit.organizer import category_for, organize, plan_organization
from toolkit.report import generate_excel_report


@pytest.fixture
def clean_frame() -> pd.DataFrame:
    raw = pd.DataFrame(
        [
            ["2025-01-05", "PED-001", "Notebook", "Informatica", "Site", 2, 1000, "CE"],
            ["2025-01-06", "PED-002", "Mouse", "Perifericos", "Loja", 1, 50, "SP"],
            ["2025-02-01", "PED-003", "Monitor", "Monitores", "Site", 1, 800, "RJ"],
        ],
        columns=[
            "data",
            "pedido_id",
            "produto",
            "categoria",
            "canal",
            "quantidade",
            "preco_unitario",
            "estado",
        ],
    )
    frame, _ = clean_sales(raw)
    return frame


def test_generate_excel_report_creates_sheets_and_charts(tmp_path: Path, clean_frame: pd.DataFrame) -> None:
    from openpyxl import load_workbook

    output = generate_excel_report(clean_frame, tmp_path / "relatorio.xlsx", top_limit=2)

    assert output.exists()
    workbook = load_workbook(output)
    assert workbook.sheetnames == [
        "Resumo",
        "Receita Mensal",
        "Top Produtos",
        "Categorias",
        "Canais",
        "Dados",
    ]

    summary = workbook["Resumo"]
    labels = [summary.cell(row=row, column=1).value for row in range(2, summary.max_row + 1)]
    assert "Receita total (R$)" in labels
    assert summary.cell(row=2, column=2).value == pytest.approx(2850.0)
    assert len(workbook["Receita Mensal"]._charts) == 1
    assert len(workbook["Top Produtos"]._charts) == 1

    with pytest.raises(ValueError):
        generate_excel_report(clean_frame.iloc[0:0], tmp_path / "vazio.xlsx")


def test_organize_dry_run_does_not_move_files(tmp_path: Path) -> None:
    (tmp_path / "foto.JPG").write_text("imagem", encoding="utf-8")
    (tmp_path / "relatorio.pdf").write_text("pdf", encoding="utf-8")
    (tmp_path / "dados.csv").write_text("csv", encoding="utf-8")
    (tmp_path / "arquivo.xyz").write_text("outro", encoding="utf-8")

    result = organize(tmp_path, apply=False)

    assert result.applied is False
    assert len(result.moves) == 4
    assert result.categories == {
        "Documentos": 1,
        "Imagens": 1,
        "Outros": 1,
        "Planilhas": 1,
    }
    assert (tmp_path / "foto.JPG").exists()
    assert not (tmp_path / "Imagens").exists()


def test_organize_moves_files_into_categories(tmp_path: Path) -> None:
    (tmp_path / "foto.JPG").write_text("imagem", encoding="utf-8")
    (tmp_path / "relatorio.pdf").write_text("pdf", encoding="utf-8")
    (tmp_path / "script.py").write_text("print('oi')", encoding="utf-8")
    (tmp_path / "arquivo.xyz").write_text("outro", encoding="utf-8")

    result = organize(tmp_path, apply=True)

    assert result.applied is True
    assert (tmp_path / "Imagens" / "foto.JPG").read_text(encoding="utf-8") == "imagem"
    assert (tmp_path / "Documentos" / "relatorio.pdf").exists()
    assert (tmp_path / "Codigo" / "script.py").exists()
    assert (tmp_path / "Outros" / "arquivo.xyz").exists()
    assert not (tmp_path / "foto.JPG").exists()


def test_organize_handles_name_collisions(tmp_path: Path) -> None:
    source = tmp_path / "origem"
    source.mkdir()
    (source / "foto.png").write_text("nova", encoding="utf-8")

    destination = tmp_path / "destino"
    (destination / "Imagens").mkdir(parents=True)
    (destination / "Imagens" / "foto.png").write_text("antiga", encoding="utf-8")

    plan = plan_organization(source, destination)
    assert plan[0].destination.name == "foto (1).png"

    organize(source, destination, apply=True)
    assert (destination / "Imagens" / "foto.png").read_text(encoding="utf-8") == "antiga"
    assert (destination / "Imagens" / "foto (1).png").read_text(encoding="utf-8") == "nova"


def test_organize_validates_source_directory(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        plan_organization(tmp_path / "nao-existe")

    assert category_for(Path("arquivo.PDF")) == "Documentos"
    assert category_for(Path("arquivo.zzz")) == "Outros"
