"""Automacao de organizacao de arquivos por categoria."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

EXTENSION_CATEGORIES = {
    "Imagens": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"},
    "Documentos": {".pdf", ".doc", ".docx", ".txt", ".md", ".odt", ".rtf"},
    "Planilhas": {".xlsx", ".xls", ".csv", ".ods"},
    "Codigo": {".py", ".js", ".ts", ".java", ".json", ".html", ".css", ".sql", ".sh"},
    "Arquivos": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "Midia": {".mp3", ".mp4", ".mov", ".wav", ".avi", ".mkv"},
}

EXTENSION_LOOKUP = {
    extension: category
    for category, extensions in EXTENSION_CATEGORIES.items()
    for extension in extensions
}

DEFAULT_CATEGORY = "Outros"


@dataclass(frozen=True)
class PlannedMove:
    source: Path
    destination: Path
    category: str
    size_bytes: int


@dataclass(frozen=True)
class OrganizationResult:
    moves: tuple[PlannedMove, ...]
    applied: bool

    @property
    def total_bytes(self) -> int:
        return sum(move.size_bytes for move in self.moves)

    @property
    def categories(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for move in self.moves:
            counts[move.category] = counts.get(move.category, 0) + 1
        return dict(sorted(counts.items()))


def category_for(path: Path) -> str:
    """Retorna a categoria de um arquivo a partir da extensao."""
    return EXTENSION_LOOKUP.get(path.suffix.lower(), DEFAULT_CATEGORY)


def plan_organization(
    source_dir: str | Path,
    destination_dir: str | Path | None = None,
) -> list[PlannedMove]:
    """Monta o plano de movimentacao sem alterar nenhum arquivo."""
    source = Path(source_dir).resolve()
    if not source.is_dir():
        raise FileNotFoundError(f"Diretorio de origem nao encontrado: {source}")

    destination_root = Path(destination_dir).resolve() if destination_dir else source
    if destination_root.exists() and not destination_root.is_dir():
        raise ValueError(f"O destino nao e um diretorio: {destination_root}")

    files = sorted(
        (item for item in source.iterdir() if item.is_file()),
        key=lambda item: item.name.lower(),
    )

    reserved: set[Path] = set()
    moves: list[PlannedMove] = []

    for file_path in files:
        category = category_for(file_path)
        destination = _available_destination(
            destination_root / category / file_path.name,
            reserved,
        )
        moves.append(
            PlannedMove(
                source=file_path,
                destination=destination,
                category=category,
                size_bytes=file_path.stat().st_size,
            )
        )

    return moves


def organize(
    source_dir: str | Path,
    destination_dir: str | Path | None = None,
    *,
    apply: bool = False,
) -> OrganizationResult:
    """Planeja e, opcionalmente, executa a organizacao dos arquivos."""
    moves = plan_organization(source_dir, destination_dir)

    if apply:
        for move in moves:
            move.destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(move.source), str(move.destination))

    return OrganizationResult(moves=tuple(moves), applied=apply)


def _available_destination(destination: Path, reserved: set[Path]) -> Path:
    candidate = destination
    counter = 1

    while candidate.exists() or candidate in reserved:
        candidate = destination.with_name(
            f"{destination.stem} ({counter}){destination.suffix}"
        )
        counter += 1

    reserved.add(candidate)
    return candidate
