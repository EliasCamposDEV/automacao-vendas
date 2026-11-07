"""Carregamento e limpeza dos dados de vendas."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = (
    "data",
    "pedido_id",
    "produto",
    "categoria",
    "canal",
    "quantidade",
    "preco_unitario",
    "estado",
)

TEXT_COLUMNS = ("pedido_id", "produto", "categoria", "canal", "estado")


@dataclass(frozen=True)
class CleaningReport:
    input_rows: int
    output_rows: int
    removed_invalid: int
    removed_duplicates: int

    @property
    def removed_rows(self) -> int:
        return self.input_rows - self.output_rows

    def as_dict(self) -> dict[str, int]:
        return {
            "linhas_entrada": self.input_rows,
            "linhas_saida": self.output_rows,
            "removidas_invalidas": self.removed_invalid,
            "removidas_duplicadas": self.removed_duplicates,
        }


def load_sales(path: str | Path) -> tuple[pd.DataFrame, CleaningReport]:
    """Le um CSV de vendas, limpa os dados e calcula colunas derivadas."""
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Arquivo de vendas nao encontrado: {csv_path}")

    frame = pd.read_csv(csv_path)
    return clean_sales(frame)


def clean_sales(frame: pd.DataFrame) -> tuple[pd.DataFrame, CleaningReport]:
    """Valida, normaliza e deduplica os dados de vendas.

    Regras:
    - exige todas as colunas de REQUIRED_COLUMNS;
    - remove linhas com campos essenciais vazios, data invalida,
      quantidade <= 0 ou preco <= 0;
    - remove duplicatas do par (pedido_id, produto), mantendo a primeira;
    - adiciona ``receita`` (quantidade * preco_unitario) e ``mes`` (AAAA-MM).
    """
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"Colunas obrigatorias ausentes: {', '.join(missing_columns)}")

    data = frame.loc[:, REQUIRED_COLUMNS].copy()
    input_rows = len(data)

    for column in TEXT_COLUMNS:
        data[column] = data[column].astype("string").str.strip()

    data["data"] = pd.to_datetime(data["data"], errors="coerce")
    data["quantidade"] = pd.to_numeric(data["quantidade"], errors="coerce")
    data["preco_unitario"] = pd.to_numeric(data["preco_unitario"], errors="coerce")

    invalid_mask = (
        data["data"].isna()
        | data["quantidade"].isna()
        | data["preco_unitario"].isna()
        | (data["quantidade"] <= 0)
        | (data["preco_unitario"] <= 0)
        | data[list(TEXT_COLUMNS)].isna().any(axis=1)
        | data[list(TEXT_COLUMNS)]
        .apply(lambda column: column.fillna("").eq(""))
        .any(axis=1)
    )

    data = data.loc[~invalid_mask].copy()
    removed_invalid = int(invalid_mask.sum())

    before_duplicates = len(data)
    data = data.drop_duplicates(subset=["pedido_id", "produto"], keep="first").copy()
    removed_duplicates = before_duplicates - len(data)

    data["quantidade"] = data["quantidade"].astype(int)
    data["preco_unitario"] = data["preco_unitario"].astype(float)
    data["receita"] = (data["quantidade"] * data["preco_unitario"]).round(2)
    data["mes"] = data["data"].dt.to_period("M").astype(str)
    data = data.sort_values(["data", "pedido_id", "produto"]).reset_index(drop=True)

    report = CleaningReport(
        input_rows=input_rows,
        output_rows=len(data),
        removed_invalid=removed_invalid,
        removed_duplicates=removed_duplicates,
    )
    return data, report
