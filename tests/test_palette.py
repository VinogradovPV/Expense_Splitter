import re
from decimal import Decimal

import pytest

from expense_splitter.visual.palette import (
    BALANCE_STATUS_COLOR_MAP,
    CHART_COLOR_STRATEGIES,
    CONTRAST_SEQUENTIAL_PALETTE,
    EXPENSE_DIMENSION_COLOR_MAP,
    PALETTE_NAME,
    PALETTE_VERSION,
    QUALITATIVE_PALETTE,
    SEQUENTIAL_PALETTE,
    STATUS_PALETTE,
    WARNING_STATUS_PALETTE,
    build_period_color_map,
    build_stable_color_map,
    color_for_balance_status,
    color_for_label,
    color_for_period,
)


HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def collect_colors():
    colors = []
    colors.extend(QUALITATIVE_PALETTE)
    colors.extend(SEQUENTIAL_PALETTE)
    colors.extend(CONTRAST_SEQUENTIAL_PALETTE)
    colors.extend(STATUS_PALETTE.values())
    colors.extend(EXPENSE_DIMENSION_COLOR_MAP.values())
    colors.extend(BALANCE_STATUS_COLOR_MAP.values())
    return colors


def test_all_palette_colors_are_valid_hex():
    assert all(HEX_COLOR.fullmatch(color) for color in collect_colors())


def test_palette_metadata_is_stable():
    assert PALETTE_NAME == "expense_splitter_default"
    assert PALETTE_VERSION == 1
    assert CHART_COLOR_STRATEGIES["spending_by_category.png"] == "stable_category_map"
    assert WARNING_STATUS_PALETTE is STATUS_PALETTE


def test_build_stable_color_map_is_deterministic_and_deduplicates_labels():
    labels = ["Кофе", "Еда", "Кофе", "Такси"]

    first = build_stable_color_map(labels)
    second = build_stable_color_map(labels)

    assert first == second
    assert list(first) == ["Кофе", "Еда", "Такси"]
    assert first["Кофе"] == QUALITATIVE_PALETTE[0]
    assert first["Еда"] == QUALITATIVE_PALETTE[1]


def test_build_stable_color_map_cycles_palette():
    labels = [f"category-{index}" for index in range(len(QUALITATIVE_PALETTE) + 2)]

    color_map = build_stable_color_map(labels)

    assert color_map["category-0"] == QUALITATIVE_PALETTE[0]
    assert color_map[f"category-{len(QUALITATIVE_PALETTE)}"] == QUALITATIVE_PALETTE[0]
    assert color_map[f"category-{len(QUALITATIVE_PALETTE) + 1}"] == QUALITATIVE_PALETTE[1]


def test_build_stable_color_map_rejects_empty_palette():
    with pytest.raises(ValueError, match="Palette must contain"):
        build_stable_color_map(["Кофе"], palette=[])


def test_color_for_label_uses_label_universe():
    labels = ["Павел", "Сергей", "Елена"]

    assert color_for_label("Сергей", labels) == QUALITATIVE_PALETTE[1]
    assert color_for_label("Мария", labels) == QUALITATIVE_PALETTE[3]


def test_period_colors_follow_chronological_input_order():
    periods = ["2026-01", "2026-02", "2026-03"]

    color_map = build_period_color_map(periods)

    assert color_map["2026-01"] == SEQUENTIAL_PALETTE[0]
    assert color_for_period("2026-03", periods) == SEQUENTIAL_PALETTE[2]


def test_balance_status_colors_distinguish_positive_negative_and_zero():
    assert color_for_balance_status(Decimal("10.00")) == BALANCE_STATUS_COLOR_MAP["к получению"]
    assert color_for_balance_status("-0.01") == BALANCE_STATUS_COLOR_MAP["к оплате"]
    assert color_for_balance_status(0) == BALANCE_STATUS_COLOR_MAP["ноль"]


def test_balance_status_rejects_invalid_amount():
    with pytest.raises(ValueError, match="Invalid net amount"):
        color_for_balance_status("not-a-number")
