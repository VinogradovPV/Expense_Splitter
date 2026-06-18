from __future__ import annotations

from decimal import Decimal, InvalidOperation
from itertools import cycle
from typing import Sequence


PALETTE_NAME = "expense_splitter_default"
PALETTE_VERSION = 1

QUALITATIVE_PALETTE = [
    "#001542",
    "#09C886",
    "#FF5A50",
    "#3A3377",
    "#822B93",
    "#2EA3D8",
    "#7D8AFA",
    "#166A75",
    "#B48DE9",
    "#60AEA1",
    "#E6D957",
    "#D8D8D8",
]

SEQUENTIAL_PALETTE = [
    "#D2ECF9",
    "#BFD5E9",
    "#ACBED9",
    "#90A7C8",
    "#737BAA",
    "#606998",
    "#4D4A87",
    "#3A3377",
]

CONTRAST_SEQUENTIAL_PALETTE = [
    "#D2ECF9",
    "#BFD5E9",
    "#ACBED9",
    "#90A7C8",
    "#737BAA",
    "#606998",
    "#4D4A87",
    "#3A3377",
]

STATUS_PALETTE = {
    "норма": "#09C886",
    "предупреждение": "#E6D957",
    "риск": "#FF5A50",
    "требует проверки": "#FF5A50",
    "нет данных": "#D8D8D8",
}

EXPENSE_DIMENSION_COLOR_MAP = {
    "Период": "#001542",
    "Категория": "#166A75",
    "Плательщик": "#3A3377",
    "Участник": "#822B93",
    "Покупка": "#2EA3D8",
}

BALANCE_STATUS_COLOR_MAP = {
    "к получению": "#09C886",
    "к оплате": "#FF5A50",
    "ноль": "#D8D8D8",
}

WARNING_STATUS_PALETTE = STATUS_PALETTE

CHART_COLOR_STRATEGIES = {
    "spending_by_category.png": "stable_category_map",
    "spending_by_payer.png": "qualitative_palette_by_payer",
    "participant_share.png": "qualitative_palette_by_participant",
    "balances.png": "balance_status_map",
    "period_trend.png": "period_chronological_sequential",
    "top_purchases.png": "qualitative_palette_by_rank",
}


def build_stable_color_map(
    labels: Sequence[object],
    palette: Sequence[str] = QUALITATIVE_PALETTE,
) -> dict[str, str]:
    """Return deterministic label-to-color mapping, cycling colors when needed."""
    if not palette:
        raise ValueError("Palette must contain at least one color.")

    color_cycle = cycle(palette)
    color_map: dict[str, str] = {}
    for label in labels:
        key = str(label)
        if key not in color_map:
            color_map[key] = next(color_cycle)
    return color_map


def color_for_label(
    label: object,
    labels: Sequence[object],
    palette: Sequence[str] = QUALITATIVE_PALETTE,
) -> str:
    label_key = str(label)
    color_map = build_stable_color_map(labels, palette)
    if label_key not in color_map:
        color_map = build_stable_color_map([*labels, label], palette)
    return color_map[label_key]


def build_period_color_map(periods: Sequence[object]) -> dict[str, str]:
    return build_stable_color_map(periods, SEQUENTIAL_PALETTE)


def color_for_period(period: object, periods: Sequence[object]) -> str:
    return color_for_label(period, periods, SEQUENTIAL_PALETTE)


def color_for_balance_status(net_amount: Decimal | int | float | str) -> str:
    try:
        amount = net_amount if isinstance(net_amount, Decimal) else Decimal(str(net_amount))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid net amount: {net_amount!r}") from exc

    if amount > 0:
        return BALANCE_STATUS_COLOR_MAP["к получению"]
    if amount < 0:
        return BALANCE_STATUS_COLOR_MAP["к оплате"]
    return BALANCE_STATUS_COLOR_MAP["ноль"]
