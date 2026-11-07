from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from toolkit.cli import main


def _write_csv(path: Path) -> Path:
    frame = pd.DataFrame(
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
    csv_path = path / "vendas.csv"
    frame.to_csv(csv_path, index=False)
    return csv_path


def test_cli_analyze_json(tmp_path: Path, capsys) -> None:
    csv_path = _write_csv(tmp_path)

    assert main(["analyze", str(csv_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["kpis"]["receita_total"] == 2850.0
    assert len(payload["top_produtos"]) == 3
    assert payload["limpeza"]["linhas_saida"] == 3


def test_cli_report_and_organize(tmp_path: Path, capsys) -> None:
    csv_path = _write_csv(tmp_path)
    output = tmp_path / "relatorio.xlsx"

    assert main(["report", str(csv_path), "-o", str(output)]) == 0
    assert output.exists()
    assert "Relatorio gerado" in capsys.readouterr().out

    files_dir = tmp_path / "arquivos"
    files_dir.mkdir()
    (files_dir / "nota.pdf").write_text("pdf", encoding="utf-8")

    assert main(["organize", str(files_dir)]) == 0
    output_text = capsys.readouterr().out
    assert "Simulacao" in output_text
    assert "Nada foi movido" in output_text
    assert (files_dir / "nota.pdf").exists()


def test_cli_returns_error_for_missing_csv(tmp_path: Path, capsys) -> None:
    assert main(["analyze", str(tmp_path / "nao-existe.csv")]) == 1
    assert "nao encontrado" in capsys.readouterr().err
