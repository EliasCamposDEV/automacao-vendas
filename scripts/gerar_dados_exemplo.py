"""Gera o CSV de exemplo usado nos comandos do README."""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

PRODUCTS = [
    ("Notebook Pro 14", "Informatica", 3899.90),
    ("Mouse Sem Fio", "Perifericos", 129.90),
    ("Teclado Mecanico", "Perifericos", 349.90),
    ("Monitor 27 polegadas", "Monitores", 1899.00),
    ("Headset USB", "Audio", 249.90),
    ("Webcam Full HD", "Perifericos", 279.90),
    ("Cadeira Ergonomica", "Escritorio", 1499.00),
    ("Mesa Digitalizadora", "Perifericos", 459.00),
    ("SSD 1TB", "Componentes", 549.90),
    ("Memoria RAM 16GB", "Componentes", 329.90),
    ("Hub USB-C", "Acessorios", 189.90),
    ("Suporte para Notebook", "Acessorios", 119.90),
]

CHANNELS = ("Site", "Marketplace", "Loja Fisica", "WhatsApp")
STATES = ("CE", "SP", "RJ", "MG", "BA", "PE", "PR", "RS")
COLUMNS = (
    "data",
    "pedido_id",
    "produto",
    "categoria",
    "canal",
    "quantidade",
    "preco_unitario",
    "estado",
)


def generate_rows(seed: int = 42) -> list[dict[str, object]]:
    rng = random.Random(seed)
    start = date(2025, 1, 1)
    rows: list[dict[str, object]] = []

    for order_number in range(1, 341):
        order_date = start + timedelta(days=rng.randrange(365))
        order_id = f"PED-{order_number:04d}"
        channel = rng.choice(CHANNELS)
        state = rng.choice(STATES)
        products = rng.sample(PRODUCTS, rng.randint(1, 3))

        for product, category, price in products:
            quantity = rng.choices((1, 2, 3, 4), weights=(55, 25, 15, 5))[0]
            rows.append(
                {
                    "data": order_date.isoformat(),
                    "pedido_id": order_id,
                    "produto": product,
                    "categoria": category,
                    "canal": channel,
                    "quantidade": quantity,
                    "preco_unitario": f"{price:.2f}",
                    "estado": state,
                }
            )

    # Linhas "sujas" de proposito para demonstrar a etapa de limpeza.
    rows.extend(dict(rng.choice(rows)) for _ in range(5))

    dirty_rows = [
        {**rows[0], "produto": "", "pedido_id": "PED-9001"},
        {**rows[1], "categoria": "", "pedido_id": "PED-9002"},
        {**rows[2], "data": "31/02/2025", "pedido_id": "PED-9003"},
        {**rows[3], "quantidade": 0, "pedido_id": "PED-9004"},
        {**rows[4], "preco_unitario": "-10.00", "pedido_id": "PED-9005"},
    ]
    rows.extend(dirty_rows)
    rng.shuffle(rows)
    return rows


def main() -> None:
    output = Path(__file__).resolve().parents[1] / "data" / "vendas.csv"
    output.parent.mkdir(parents=True, exist_ok=True)

    rows = generate_rows()
    with output.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Gerado {output} com {len(rows)} linhas")


if __name__ == "__main__":
    main()
