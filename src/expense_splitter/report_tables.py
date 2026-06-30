from __future__ import annotations

from pathlib import Path
from typing import Sequence

PURCHASE_DISPLAY_EXCLUDED_COLUMNS = {"id", "payer_total", "payer_rank"}
CHART_DISPLAY_TITLES = {
    "participant_share.png": "Объем расходов на человека",
}


def rows_for_visual_table(filename: str | Path, rows: Sequence[Sequence[str]]) -> list[list[str]]:
    """Remove machine-only purchase columns from user-facing table renderers."""
    if not rows or Path(filename).name != "purchases.csv":
        return [list(row) for row in rows]

    headers = [str(header) for header in rows[0]]
    visible_indexes = [
        index
        for index, header in enumerate(headers)
        if header.strip().casefold() not in PURCHASE_DISPLAY_EXCLUDED_COLUMNS
    ]
    return [[row[index] for index in visible_indexes if index < len(row)] for row in rows]


def chart_display_title(filename: str | Path) -> str:
    path = Path(filename)
    return CHART_DISPLAY_TITLES.get(path.name, path.stem)
