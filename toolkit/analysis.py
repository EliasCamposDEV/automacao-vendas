"""Metricas e agregacoes de vendas."""

from __future__ import annotations

import pandas as pd


def _require_data(frame: pd.DataFrame) -> None:
    if frame.empty:
        raise ValueError("Nao ha dados de vendas para analisar")
    if "receita" not in frame.columns:
        raise ValueError("A coluna 'receita' e obrigatoria; use clean_sales ou load_sales")


def compute_kpis(frame: pd.DataFrame) -> dict[str, float | int | None]:
    """Calcula os principais indicadores de vendas."""
    _require_data(frame)

    revenue = float(frame["receita"].sum())
    orders = int(frame["pedido_id"].nunique())
    items = int(frame["quantidade"].sum())

    monthly = revenue_by_month(frame)
    growth = None
    if len(monthly) >= 2:
        previous = float(monthly.iloc[-2]["receita"])
        current = float(monthly.iloc[-1]["receita"])
        if previous > 0:
            growth = round((current - previous) / previous * 100, 2)

    return {
        "receita_total": round(revenue, 2),
        "pedidos": orders,
        "itens_vendidos": items,
        "ticket_medio": round(revenue / orders, 2) if orders else 0.0,
        "preco_medio_item": round(revenue / items, 2) if items else 0.0,
        "produtos_vendidos": int(frame["produto"].nunique()),
        "crescimento_ultimo_mes_pct": growth,
    }


def revenue_by_month(frame: pd.DataFrame) -> pd.DataFrame:
    """Receita, pedidos e itens agrupados por mes."""
    _require_data(frame)

    return (
        frame.groupby("mes", as_index=False)
        .agg(
            receita=("receita", "sum"),
            pedidos=("pedido_id", "nunique"),
            itens=("quantidade", "sum"),
        )
        .assign(receita=lambda data: data["receita"].round(2))
        .sort_values("mes")
        .reset_index(drop=True)
    )


def top_products(frame: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    """Produtos ordenados por receita."""
    _require_data(frame)
    if limit <= 0:
        raise ValueError("O limite deve ser maior que zero")

    return (
        frame.groupby(["produto", "categoria"], as_index=False)
        .agg(
            receita=("receita", "sum"),
            itens=("quantidade", "sum"),
            pedidos=("pedido_id", "nunique"),
        )
        .assign(receita=lambda data: data["receita"].round(2))
        .sort_values(["receita", "produto"], ascending=[False, True])
        .head(limit)
        .reset_index(drop=True)
    )


def revenue_by_dimension(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    """Receita e participacao percentual por dimensao (categoria, canal etc.)."""
    _require_data(frame)
    if column not in frame.columns:
        raise ValueError(f"Coluna inexistente para agrupamento: {column}")

    grouped = (
        frame.groupby(column, as_index=False)
        .agg(
            receita=("receita", "sum"),
            itens=("quantidade", "sum"),
            pedidos=("pedido_id", "nunique"),
        )
        .assign(receita=lambda data: data["receita"].round(2))
        .sort_values("receita", ascending=False)
        .reset_index(drop=True)
    )
    total = grouped["receita"].sum()
    grouped["participacao_pct"] = (
        (grouped["receita"] / total * 100).round(2) if total else 0.0
    )
    return grouped


def dataframe_to_records(frame: pd.DataFrame) -> list[dict]:
    """Converte um DataFrame em registros JSON, preservando tipos numericos."""
    import json

    return json.loads(frame.to_json(orient="records", date_format="iso"))
