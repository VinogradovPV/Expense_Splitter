from datetime import date, datetime, timezone
from decimal import Decimal

from expense_splitter.current_report import (
    OPERATIONS_BY_DAY_WARNING_MESSAGE,
    aggregate_daily_operations,
    build_current_report_dataset,
    generate_current_report,
    write_current_charts,
)
from expense_splitter.models import Participant, Purchase


def participants():
    return [Participant("Alice"), Participant("Bob")]


def purchase(
    purchase_id: str,
    purchase_date: date | None,
    amount: str,
    *,
    category: str = "Food",
) -> Purchase:
    return Purchase(
        id=purchase_id,
        date=purchase_date,
        amount=Decimal(amount),
        payer="Alice",
        participants=["Alice", "Bob"],
        purchase_name=purchase_id,
        category=category,
    )


def dataset(purchases):
    return build_current_report_dataset(
        participants(),
        purchases,
        scope="open",
        generated_at=datetime(2026, 7, 4, 10, 0, 0, tzinfo=timezone.utc),
    )


def test_current_report_two_unique_dates_builds_operations_by_day_chart(tmp_path):
    current_dataset = dataset(
        [
            purchase("p1", date(2026, 7, 1), "619.00"),
            purchase("p2", date(2026, 7, 1), "550.00"),
            purchase("p3", date(2026, 7, 3), "90.00"),
        ]
    )

    paths, warnings = write_current_charts(current_dataset, tmp_path)

    assert [(row.date, row.total_amount, row.purchase_count) for row in aggregate_daily_operations(
        current_dataset.purchases
    )] == [
        (date(2026, 7, 1), Decimal("1169.00"), 2),
        (date(2026, 7, 3), Decimal("90.00"), 1),
    ]
    assert "operations_by_day.png" in {path.name for path in paths}
    assert not any(warning["warning_type"] == "chart_not_enough_data" for warning in warnings)


def test_current_report_one_unique_date_skips_operations_by_day_with_warning(tmp_path):
    current_dataset = dataset(
        [
            purchase("p1", date(2026, 7, 1), "619.00"),
            purchase("p2", date(2026, 7, 1), "550.00"),
        ]
    )

    paths, warnings = write_current_charts(current_dataset, tmp_path)

    assert [(row.date, row.total_amount, row.purchase_count) for row in aggregate_daily_operations(
        current_dataset.purchases
    )] == [(date(2026, 7, 1), Decimal("1169.00"), 2)]
    assert "operations_by_day.png" not in {path.name for path in paths}
    assert not (tmp_path / "operations_by_day.png").exists()
    assert {
        "chart": "operations_by_day",
        "warning_type": "chart_not_enough_data",
        "purchase_id": "",
        "purchase_name": "",
        "message": OPERATIONS_BY_DAY_WARNING_MESSAGE,
    } in warnings


def test_current_report_undated_purchase_keeps_missing_date_without_chart_warning(tmp_path):
    current_dataset = dataset(
        [
            purchase("p1", date(2026, 7, 1), "619.00"),
            purchase("p2", None, "550.00"),
            purchase("p3", date(2026, 7, 3), "90.00"),
        ]
    )

    paths, warnings = write_current_charts(current_dataset, tmp_path)

    assert [(row.date, row.total_amount) for row in aggregate_daily_operations(
        current_dataset.purchases
    )] == [
        (date(2026, 7, 1), Decimal("619.00")),
        (date(2026, 7, 3), Decimal("90.00")),
    ]
    assert any(warning["warning_type"] == "missing_date" for warning in current_dataset.warnings)
    assert "operations_by_day.png" in {path.name for path in paths}
    assert not any(warning["warning_type"] == "chart_not_enough_data" for warning in warnings)


def test_current_report_stale_operations_by_day_png_is_removed_when_chart_skipped(tmp_path):
    current_dataset = dataset(
        [
            purchase("p1", date(2026, 7, 1), "619.00"),
            purchase("p2", date(2026, 7, 1), "550.00"),
        ]
    )
    stale_chart_dir = tmp_path / "open_2026-07-04_10-00-00" / "charts"
    stale_chart_dir.mkdir(parents=True)
    (stale_chart_dir / "operations_by_day.png").write_bytes(b"stale")

    report_dir = generate_current_report(current_dataset, tmp_path, "all")

    metadata = (report_dir / "metadata.json").read_text(encoding="utf-8")
    markdown = (report_dir / "current_state_report.md").read_text(encoding="utf-8")
    assert not (report_dir / "charts" / "operations_by_day.png").exists()
    assert "charts/operations_by_day.png" not in metadata
    assert "Операции по дням" not in markdown
    assert OPERATIONS_BY_DAY_WARNING_MESSAGE in markdown
