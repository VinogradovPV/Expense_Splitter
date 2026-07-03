from datetime import date
from decimal import Decimal

import pytest

from expense_splitter.analytics import build_analytics_dataset, parse_period
from expense_splitter.analytics_charts import (
    CHART_FILENAMES,
    _format_chart_value,
    generate_analytics_charts,
    set_non_negative_x_axis,
)
from expense_splitter.models import Participant, Purchase


def build_dataset(with_purchase=True):
    participants = [Participant("Alice"), Participant("Bob")]
    purchases = []
    if with_purchase:
        purchases.append(
            Purchase(
                id="p1",
                date=date(2026, 6, 1),
                amount=Decimal("50.00"),
                payer="Alice",
                participants=["Alice", "Bob"],
                purchase_name="Lunch",
                category="Food",
            )
        )
    return build_analytics_dataset(
        participants, [], purchases, parse_period("month", 2026, month=6)
    )


def test_charts_are_headless_png_files(tmp_path):
    paths, warnings = generate_analytics_charts(build_dataset(), tmp_path)

    assert [warning["message"] for warning in warnings] == [
        "Недостаточно дат для построения динамики расходов."
    ]
    assert {path.name for path in paths} == set(CHART_FILENAMES) - {"period_trend.png"}
    assert all(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for path in paths)


def test_empty_dataset_returns_warnings_instead_of_failing(tmp_path):
    paths, warnings = generate_analytics_charts(build_dataset(False), tmp_path)

    assert paths == []
    assert len(warnings) == len(CHART_FILENAMES)
    assert {warning["warning_type"] for warning in warnings} == {"chart_no_data"}


def test_chart_data_labels_use_readable_money_format():
    assert _format_chart_value(1200.5) == "1 200.50"
    assert _format_chart_value(-25) == "-25.00"


def test_non_negative_x_axis_starts_at_zero_with_right_padding():
    class Axis:
        def __init__(self):
            self.limits = None

        def set_xlim(self, *args, **kwargs):
            self.limits = args, kwargs

    axis = Axis()

    set_non_negative_x_axis(axis, [10.0, 20.0])

    args, kwargs = axis.limits
    assert args == ()
    assert kwargs["left"] == 0
    assert kwargs["right"] == pytest.approx(23.6)
