from __future__ import annotations

from pathlib import Path
from typing import Sequence

PURCHASE_DISPLAY_EXCLUDED_COLUMNS = {"id", "payer_total", "payer_rank"}
BALANCE_EXPLANATION = (
    "Положительный итоговый баланс означает, что участнику должны вернуть деньги. "
    "Отрицательный итоговый баланс означает, что участник должен доплатить."
)
CHART_DISPLAY_TITLES = {
    "balances.png": "Итоговые балансы",
    "period_trend.png": "Динамика расходов за период",
    "spending_by_category.png": "Расходы по категориям",
    "spending_by_payer.png": "Расходы по плательщикам",
    "top_purchases.png": "Крупнейшие покупки",
    "participant_share.png": "Объем расходов на человека",
}
VISUAL_HEADER_RENAMES = {
    "by_participant.csv": {
        "Доля": "Объем расходов на человека",
        "Доля расходов": "Объем расходов на человека",
    },
    "balances.csv": {
        "Доля": "Объем расходов на человека",
        "Баланс": "Итоговый баланс",
    },
}


def rows_for_visual_table(filename: str | Path, rows: Sequence[Sequence[str]]) -> list[list[str]]:
    """Remove machine-only purchase columns from user-facing table renderers."""
    name = Path(filename).name
    if not rows:
        return [["Предупреждений нет."]] if name == "warnings.csv" else []
    if name == "warnings.csv" and len(rows) == 1:
        return [["Предупреждений нет."]]
    if name != "purchases.csv":
        return _rename_visual_headers(name, rows)

    headers = [str(header) for header in rows[0]]
    visible_indexes = [
        index
        for index, header in enumerate(headers)
        if header.strip().casefold() not in PURCHASE_DISPLAY_EXCLUDED_COLUMNS
    ]
    visible_rows = [[row[index] for index in visible_indexes if index < len(row)] for row in rows]
    return _rename_visual_headers(name, visible_rows)


def chart_display_title(filename: str | Path) -> str:
    path = Path(filename)
    return CHART_DISPLAY_TITLES.get(path.name, path.stem)


def visual_table_note(filename: str | Path) -> str | None:
    if Path(filename).name == "balances.csv":
        return BALANCE_EXPLANATION
    return None


def _rename_visual_headers(
    filename: str,
    rows: Sequence[Sequence[str]],
) -> list[list[str]]:
    result = [list(row) for row in rows]
    if not result:
        return result
    renames = VISUAL_HEADER_RENAMES.get(filename, {})
    if not renames:
        return result
    result[0] = [renames.get(str(header), str(header)) for header in result[0]]
    return result
