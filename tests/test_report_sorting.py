from datetime import date
from decimal import Decimal

from expense_splitter.models import Purchase
from expense_splitter.report_sorting import (
    sort_purchases_by_payer_total_then_amount,
    sorted_purchases_with_payer_totals,
)


def purchase(
    purchase_id: str,
    payer: str,
    amount: str,
    purchase_date: date,
    name: str,
) -> Purchase:
    return Purchase(
        id=purchase_id,
        date=purchase_date,
        amount=Decimal(amount),
        payer=payer,
        participants=[payer],
        purchase_name=name,
    )


def test_payer_with_largest_total_goes_first_and_purchases_sort_inside_payer():
    purchases = [
        purchase("b-small", "Bob", "20.00", date(2026, 6, 1), "B small"),
        purchase("a-large", "Alice", "70.00", date(2026, 6, 1), "A large"),
        purchase("b-large", "Bob", "90.00", date(2026, 6, 2), "B large"),
        purchase("a-small", "Alice", "30.00", date(2026, 6, 3), "A small"),
    ]

    sorted_rows = sorted_purchases_with_payer_totals(purchases)

    assert [row.purchase.id for row in sorted_rows] == [
        "b-large",
        "b-small",
        "a-large",
        "a-small",
    ]
    assert [row.payer_total for row in sorted_rows] == [
        Decimal("110.00"),
        Decimal("110.00"),
        Decimal("100.00"),
        Decimal("100.00"),
    ]
    assert [row.payer_rank for row in sorted_rows] == [1, 1, 2, 2]


def test_tie_breakers_are_deterministic():
    purchases = [
        purchase("z", "Bob", "10.00", date(2026, 6, 1), "Zoo"),
        purchase("a", "Alice", "10.00", date(2026, 6, 1), "Alpha"),
        purchase("b", "Alice", "10.00", date(2026, 6, 2), "Beta"),
        purchase("c", "Alice", "10.00", date(2026, 6, 2), "Alpha"),
    ]

    assert [purchase.id for purchase in sort_purchases_by_payer_total_then_amount(purchases)] == [
        "c",
        "b",
        "a",
        "z",
    ]
