from datetime import date, datetime
from decimal import Decimal

import pytest

from expense_splitter.models import Purchase, Settlement, SettlementPeriod
from expense_splitter.settlement_periods import (
    DELETE_EMPTY_PERIOD_CONFIRM,
    DELETE_EMPTY_PERIODS_CONFIRM,
    delete_empty_settlement_period,
    delete_empty_settlement_periods,
    is_empty_settlement_period,
    is_meaningful_closed_period,
    suggest_next_settlement_period,
    update_settlement_period_metadata,
)


def make_purchase(purchase_id: str, purchase_date: date, settled: bool = False) -> Purchase:
    return Purchase(
        id=purchase_id,
        date=purchase_date,
        amount=Decimal("100.00"),
        payer="Alice",
        participants=["Alice", "Bob"],
        purchase_name=f"Purchase {purchase_id}",
        settled=settled,
    )


def make_period(
    period_id: str,
    status: str,
    date_to: date,
    *,
    empty: bool = False,
) -> SettlementPeriod:
    return SettlementPeriod(
        id=period_id,
        name=period_id,
        status=status,
        date_from=date(2026, 6, 1),
        date_to=date_to,
        closed_at=datetime(2026, 6, 30, 12, 0, 0),
        purchase_ids=[] if empty else ["p1"],
        total_amount=Decimal("0.00") if empty else Decimal("100.00"),
        settlements=[] if empty else [Settlement("Bob", "Alice", Decimal("50.00"))],
        reopened_at=datetime(2026, 7, 1, 12, 0, 0) if status == "reopened" else None,
    )


def test_suggest_uses_last_meaningful_closed_period_plus_one_day():
    periods = [
        make_period("empty-late", "closed", date(2026, 6, 30), empty=True),
        make_period("meaningful", "closed", date(2026, 6, 10)),
        make_period("reopened", "reopened", date(2026, 6, 20)),
    ]

    suggestion = suggest_next_settlement_period([], periods, today=date(2026, 6, 29))

    assert suggestion.date_from == date(2026, 6, 11)
    assert suggestion.date_to == date(2026, 6, 29)
    assert suggestion.reason == "last_meaningful_closed_period"


def test_suggest_ignores_empty_and_reopened_periods_and_uses_open_purchase_min_date():
    periods = [
        make_period("empty", "closed", date(2026, 6, 30), empty=True),
        make_period("reopened", "reopened", date(2026, 6, 20)),
    ]
    purchases = [
        make_purchase("p1", date(2026, 6, 3), settled=True),
        make_purchase("p2", date(2026, 6, 5)),
        make_purchase("p3", date(2026, 6, 1)),
    ]

    suggestion = suggest_next_settlement_period(purchases, periods, today=date(2026, 6, 29))

    assert suggestion.date_from == date(2026, 6, 1)
    assert suggestion.date_to == date(2026, 6, 29)
    assert suggestion.reason == "first_open_purchase_date"


def test_suggest_returns_today_when_no_open_purchases():
    suggestion = suggest_next_settlement_period([], [], today=date(2026, 6, 29))

    assert suggestion.date_from == date(2026, 6, 29)
    assert suggestion.date_to == date(2026, 6, 29)
    assert suggestion.name == "Период за 2026-06-29"
    assert suggestion.reason == "no_open_purchases"


def test_empty_and_meaningful_period_detection():
    empty = make_period("empty", "closed", date(2026, 6, 30), empty=True)
    meaningful = make_period("meaningful", "closed", date(2026, 6, 30))

    assert is_empty_settlement_period(empty) is True
    assert is_meaningful_closed_period(empty) is False
    assert is_empty_settlement_period(meaningful) is False
    assert is_meaningful_closed_period(meaningful) is True


def test_delete_empty_period_requires_confirm_and_blocks_meaningful_period():
    empty = make_period("empty", "closed", date(2026, 6, 30), empty=True)
    meaningful = make_period("meaningful", "closed", date(2026, 6, 30))
    periods = [empty, meaningful]

    with pytest.raises(ValueError, match=DELETE_EMPTY_PERIOD_CONFIRM):
        delete_empty_settlement_period(periods, empty.id, "delete")
    with pytest.raises(ValueError, match="нельзя удалить"):
        delete_empty_settlement_period(periods, meaningful.id, DELETE_EMPTY_PERIOD_CONFIRM)

    deleted = delete_empty_settlement_period(periods, empty.id, DELETE_EMPTY_PERIOD_CONFIRM)

    assert deleted.id == empty.id
    assert periods == [meaningful]


def test_delete_empty_all_deletes_only_empty_periods():
    empty = make_period("empty", "closed", date(2026, 6, 30), empty=True)
    reopened_empty = make_period("reopened-empty", "reopened", date(2026, 7, 1), empty=True)
    meaningful = make_period("meaningful", "closed", date(2026, 6, 30))
    periods = [empty, reopened_empty, meaningful]

    with pytest.raises(ValueError, match=DELETE_EMPTY_PERIODS_CONFIRM):
        delete_empty_settlement_periods(periods, "delete")

    deleted = delete_empty_settlement_periods(periods, DELETE_EMPTY_PERIODS_CONFIRM)

    assert {period.id for period in deleted} == {"empty", "reopened-empty"}
    assert periods == [meaningful]


def test_update_metadata_preserves_snapshot_fields_and_blocks_dates_for_meaningful_period():
    period = make_period("meaningful", "closed", date(2026, 6, 30))
    original_snapshot = (list(period.purchase_ids), period.total_amount, list(period.settlements))

    updated = update_settlement_period_metadata(
        [period],
        period.id,
        name="Renamed",
        notes="note",
    )

    assert updated.name == "Renamed"
    assert updated.notes == "note"
    assert (period.purchase_ids, period.total_amount, period.settlements) == original_snapshot
    with pytest.raises(ValueError, match="Даты закрытого периода"):
        update_settlement_period_metadata(
            [period],
            period.id,
            date_from=date(2026, 6, 2),
        )


def test_update_empty_period_allows_dates():
    period = make_period("empty", "closed", date(2026, 6, 30), empty=True)

    update_settlement_period_metadata(
        [period],
        period.id,
        name="Empty renamed",
        notes="technical",
        date_from=date(2026, 6, 5),
        date_to=date(2026, 6, 6),
    )

    assert period.name == "Empty renamed"
    assert period.date_from == date(2026, 6, 5)
    assert period.date_to == date(2026, 6, 6)
