from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Sequence

from expense_splitter.models import Purchase


@dataclass(frozen=True)
class SortedPurchase:
    purchase: Purchase
    payer_total: Decimal
    payer_rank: int


def sorted_purchases_with_payer_totals(purchases: Sequence[Purchase]) -> list[SortedPurchase]:
    payer_totals: dict[str, Decimal] = {}
    for purchase in purchases:
        payer_totals[purchase.payer] = (
            payer_totals.get(purchase.payer, Decimal("0.00")) + purchase.amount
        )

    payer_ranks = {
        payer: index
        for index, payer in enumerate(
            sorted(payer_totals, key=lambda payer: (-payer_totals[payer], payer.casefold())),
            start=1,
        )
    }

    sorted_purchases = sorted(
        purchases,
        key=lambda purchase: (
            payer_ranks[purchase.payer],
            -purchase.amount,
            _descending_date_key(purchase.date),
            (purchase.purchase_name or "").casefold(),
            purchase.id,
        ),
    )
    return [
        SortedPurchase(
            purchase=purchase,
            payer_total=payer_totals[purchase.payer],
            payer_rank=payer_ranks[purchase.payer],
        )
        for purchase in sorted_purchases
    ]


def sort_purchases_by_payer_total_then_amount(purchases: Sequence[Purchase]) -> list[Purchase]:
    return [row.purchase for row in sorted_purchases_with_payer_totals(purchases)]


def _descending_date_key(value: date | None) -> tuple[int, int]:
    if value is None:
        return (1, 0)
    return (0, -value.toordinal())
