from datetime import date
from decimal import Decimal

import pytest

from expense_splitter.analytics import (
    aggregate_daily_spending,
    build_analytics_dataset,
    parse_period,
)
from expense_splitter.analytics_charts import (
    CHART_FILENAMES,
    _balances,
    _format_chart_value,
    _line_label_offset,
    _top_purchases,
    generate_analytics_charts,
    set_non_negative_x_axis,
)
from expense_splitter.models import Participant, Purchase
from expense_splitter.report_tables import BALANCE_CHART_TITLE, BALANCE_CHART_XLABEL


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


def build_dataset_with_purchases(purchases):
    return build_analytics_dataset(
        [Participant("Alice"), Participant("Bob")],
        [],
        purchases,
        parse_period("month", 2026, month=7),
    )


def test_charts_are_headless_png_files(tmp_path):
    paths, warnings = generate_analytics_charts(build_dataset(), tmp_path)

    assert [warning["message"] for warning in warnings] == [
        "Недостаточно дат для построения динамики расходов."
    ]
    assert {path.name for path in paths} == set(CHART_FILENAMES) - {"period_trend.png"}
    assert all(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for path in paths)


def test_period_trend_aggregates_duplicate_dates_and_skips_single_unique_date(tmp_path):
    dataset = build_dataset_with_purchases(
        [
            Purchase(
                id="p1",
                date=date(2026, 7, 3),
                amount=Decimal("619.00"),
                payer="Alice",
                participants=["Alice", "Bob"],
                purchase_name="Hotel",
            ),
            Purchase(
                id="p2",
                date=date(2026, 7, 3),
                amount=Decimal("550.00"),
                payer="Bob",
                participants=["Alice", "Bob"],
                purchase_name="Dinner",
            ),
        ]
    )

    points = aggregate_daily_spending(dataset.purchases)
    paths, warnings = generate_analytics_charts(dataset, tmp_path)

    assert [(point.day, point.amount) for point in points] == [
        (date(2026, 7, 3), Decimal("1169.00"))
    ]
    assert "period_trend.png" not in {path.name for path in paths}
    assert not (tmp_path / "period_trend.png").exists()
    assert {
        "chart": "period_trend",
        "warning_type": "chart_not_enough_data",
        "purchase_id": "",
        "purchase_name": "",
        "message": "Недостаточно дат для построения динамики расходов.",
    } in warnings


def test_period_trend_builds_for_two_unique_dates_with_daily_totals(tmp_path):
    dataset = build_dataset_with_purchases(
        [
            Purchase(
                id="p1",
                date=date(2026, 7, 3),
                amount=Decimal("619.00"),
                payer="Alice",
                participants=["Alice", "Bob"],
                purchase_name="Hotel",
            ),
            Purchase(
                id="p2",
                date=date(2026, 7, 4),
                amount=Decimal("550.00"),
                payer="Bob",
                participants=["Alice", "Bob"],
                purchase_name="Dinner",
            ),
        ]
    )

    paths, warnings = generate_analytics_charts(dataset, tmp_path)

    assert [(point.day, point.amount) for point in aggregate_daily_spending(dataset.purchases)] == [
        (date(2026, 7, 3), Decimal("619.00")),
        (date(2026, 7, 4), Decimal("550.00")),
    ]
    assert "period_trend.png" in {path.name for path in paths}
    assert not any(warning["warning_type"] == "chart_not_enough_data" for warning in warnings)


def test_period_trend_label_offsets_keep_local_minima_below_line():
    assert _line_label_offset(4, [1169.0, 90.0, 580.0, 970.0, 196.0, 911.0]) == (
        0,
        -14,
        "top",
    )
    assert _line_label_offset(3, [1169.0, 90.0, 580.0, 970.0, 196.0, 911.0]) == (
        0,
        10,
        "bottom",
    )


def test_top_purchases_chart_keeps_largest_purchase_first(tmp_path, monkeypatch):
    captured = {}
    dataset = build_dataset_with_purchases(
        [
            Purchase(
                id="small",
                date=date(2026, 7, 1),
                amount=Decimal("90.00"),
                payer="Alice",
                participants=["Alice", "Bob"],
                purchase_name="Small",
            ),
            Purchase(
                id="large",
                date=date(2026, 7, 2),
                amount=Decimal("760.00"),
                payer="Bob",
                participants=["Alice", "Bob"],
                purchase_name="Large",
            ),
            Purchase(
                id="middle",
                date=date(2026, 7, 3),
                amount=Decimal("196.00"),
                payer="Alice",
                participants=["Alice", "Bob"],
                purchase_name="Middle",
            ),
        ]
    )

    def fake_save_barh(path, labels, values, colors, title, xlabel, **kwargs):
        captured["labels"] = labels
        captured["values"] = values

    monkeypatch.setattr("expense_splitter.analytics_charts._save_barh", fake_save_barh)

    _top_purchases(dataset, tmp_path / "top_purchases.png")

    assert captured["labels"] == ["Large", "Middle", "Small"]
    assert captured["values"] == [760.0, 196.0, 90.0]


def test_empty_dataset_returns_warnings_instead_of_failing(tmp_path):
    paths, warnings = generate_analytics_charts(build_dataset(False), tmp_path)

    assert paths == []
    assert len(warnings) == len(CHART_FILENAMES)
    assert {warning["warning_type"] for warning in warnings} == {"chart_no_data"}


def test_chart_data_labels_use_readable_money_format():
    assert _format_chart_value(1200.5) == "1 200,50"
    assert _format_chart_value(-25.2) == "-25,20"


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


def test_balance_chart_uses_plain_language_title_axis_and_status_colors(tmp_path, monkeypatch):
    captured = {}

    def fake_save_barh(path, labels, values, colors, title, xlabel, **kwargs):
        captured.update(
            {
                "labels": labels,
                "values": values,
                "colors": colors,
                "title": title,
                "xlabel": xlabel,
                "value_label_colors": kwargs["value_label_colors"],
            }
        )

    monkeypatch.setattr("expense_splitter.analytics_charts._save_barh", fake_save_barh)

    _balances(build_dataset(), tmp_path / "balances.png")

    assert captured["title"] == BALANCE_CHART_TITLE
    assert captured["xlabel"] == BALANCE_CHART_XLABEL
    assert captured["value_label_colors"] == captured["colors"]
    assert captured["values"] == [-25.0, 25.0]
