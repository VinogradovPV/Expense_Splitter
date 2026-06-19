from datetime import date
from decimal import Decimal

import pytest

from expense_splitter.analytics import (
    UNCATEGORIZED,
    aggregate_by_category,
    aggregate_by_participant,
    aggregate_by_payer,
    aggregate_summary,
    build_analytics_dataset,
    build_top_purchases,
    build_warnings,
    filter_purchases_by_period,
    parse_period,
)
from expense_splitter.models import Participant, Purchase

PARTICIPANTS = [Participant(name="Alice"), Participant(name="Bob"), Participant(name="Cara")]


def make_purchase(
    id_: str,
    purchase_date: date | None,
    amount: str,
    payer: str,
    participants: list[str],
    category: str | None = None,
    purchase_name: str = "Purchase",
) -> Purchase:
    return Purchase(
        id=id_,
        date=purchase_date,
        amount=Decimal(amount),
        payer=payer,
        participants=participants,
        purchase_name=purchase_name,
        category=category,
        comment=None,
    )


def sample_purchases():
    return [
        make_purchase("p1", date(2026, 6, 1), "120.00", "Alice", ["Alice", "Bob"], "Food", "Lunch"),
        make_purchase(
            "p2", date(2026, 6, 30), "60.00", "Bob", ["Alice", "Bob", "Cara"], None, "Coffee"
        ),
        make_purchase("p3", date(2026, 7, 1), "90.00", "Cara", ["Cara"], "Travel", "Taxi"),
        make_purchase("p4", None, "30.00", "Alice", ["Alice"], "Food", "Undated"),
    ]


def test_parse_period_month_quarter_and_year_boundaries():
    month = parse_period("month", 2026, month=2)
    quarter = parse_period("quarter", 2026, quarter=2)
    year = parse_period("year", 2026)

    assert month.start_date == date(2026, 2, 1)
    assert month.end_date == date(2026, 2, 28)
    assert month.period_id == "2026-02"
    assert quarter.start_date == date(2026, 4, 1)
    assert quarter.end_date == date(2026, 6, 30)
    assert quarter.period_id == "2026-Q2"
    assert year.start_date == date(2026, 1, 1)
    assert year.end_date == date(2026, 12, 31)
    assert year.period_id == "2026"


def test_parse_period_validates_required_inputs():
    with pytest.raises(ValueError, match="month"):
        parse_period("month", 2026)
    with pytest.raises(ValueError, match="quarter"):
        parse_period("quarter", 2026, quarter=5)
    with pytest.raises(ValueError, match="Period"):
        parse_period("week", 2026)


def test_filter_purchases_by_period_excludes_undated_by_default():
    purchases = sample_purchases()
    period = parse_period("month", 2026, month=6)

    filtered = filter_purchases_by_period(purchases, period)

    assert [purchase.id for purchase in filtered] == ["p1", "p2"]


def test_filter_purchases_by_period_can_include_undated():
    purchases = sample_purchases()
    period = parse_period("month", 2026, month=6)

    filtered = filter_purchases_by_period(purchases, period, include_undated=True)

    assert [purchase.id for purchase in filtered] == ["p1", "p2", "p4"]


def test_aggregate_summary_uses_decimal_values():
    period = parse_period("month", 2026, month=6)
    purchases = filter_purchases_by_period(sample_purchases(), period)

    summary = aggregate_summary(purchases, PARTICIPANTS, period)

    assert summary["total_amount"] == Decimal("180.00")
    assert summary["purchase_count"] == 2
    assert summary["average_purchase"] == Decimal("90.00")
    assert summary["participant_count"] == 3


def test_aggregate_by_category_maps_none_to_uncategorized():
    period = parse_period("month", 2026, month=6)
    purchases = filter_purchases_by_period(sample_purchases(), period)

    rows = aggregate_by_category(purchases)

    assert rows == [
        {"category": "Food", "purchase_count": 1, "total_amount": Decimal("120.00")},
        {"category": UNCATEGORIZED, "purchase_count": 1, "total_amount": Decimal("60.00")},
    ]


def test_aggregate_by_payer_sorts_by_total_paid():
    period = parse_period("month", 2026, month=6)
    purchases = filter_purchases_by_period(sample_purchases(), period)

    rows = aggregate_by_payer(purchases)

    assert rows[0] == {"payer": "Alice", "purchase_count": 1, "total_paid": Decimal("120.00")}
    assert rows[1] == {"payer": "Bob", "purchase_count": 1, "total_paid": Decimal("60.00")}


def test_aggregate_by_participant_uses_existing_split_logic():
    period = parse_period("month", 2026, month=6)
    purchases = filter_purchases_by_period(sample_purchases(), period)

    rows = aggregate_by_participant(purchases, PARTICIPANTS)
    by_name = {row["participant"]: row for row in rows}

    assert by_name["Alice"]["total_share"] == Decimal("80.00")
    assert by_name["Bob"]["total_share"] == Decimal("80.00")
    assert by_name["Cara"]["total_share"] == Decimal("20.00")
    assert by_name["Alice"]["purchase_count"] == 2


def test_build_top_purchases_uses_purchase_name_and_limit():
    period = parse_period("year", 2026)
    purchases = filter_purchases_by_period(sample_purchases(), period)

    rows = build_top_purchases(purchases, limit=2)

    assert [row["purchase_name"] for row in rows] == ["Lunch", "Taxi"]
    assert [row["rank"] for row in rows] == [1, 2]


def test_build_warnings_reports_undated_purchases():
    warnings = build_warnings(sample_purchases())

    assert warnings == [
        {
            "warning_type": "undated_purchase",
            "purchase_id": "p4",
            "purchase_name": "Undated",
            "message": "Покупка без даты не включается в периодную аналитику по умолчанию.",
        }
    ]


def test_build_analytics_dataset_uses_balances_and_settlements_for_period():
    period = parse_period("month", 2026, month=6)

    dataset = build_analytics_dataset(PARTICIPANTS, [], sample_purchases(), period)

    assert [purchase.id for purchase in dataset.purchases] == ["p1", "p2"]
    assert dataset.summary["total_amount"] == Decimal("180.00")
    assert len(dataset.balances) == 3
    assert sum(balance.net for balance in dataset.balances) == Decimal("0.00")
    assert dataset.settlements
    assert dataset.warnings[0]["purchase_id"] == "p4"
