from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Iterable, Literal

from expense_splitter.calculator import calculate_balances
from expense_splitter.models import Balance, Purchase, Settlement, SettlementPeriod
from expense_splitter.settlement import calculate_settlements

SettlementScope = Literal["open", "all"]


@dataclass
class SettlementPeriodPreview:
    date_from: date
    date_to: date
    purchases: list[Purchase]
    balances: list[Balance]
    settlements: list[Settlement]
    total_amount: Decimal

    @property
    def purchase_count(self) -> int:
        return len(self.purchases)


def parse_period_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid date '{value}'. Expected YYYY-MM-DD.") from exc


def validate_date_range(date_from: date, date_to: date) -> None:
    if date_from > date_to:
        raise ValueError("--from must not be after --to.")


def filter_purchases_by_settlement_scope(
    purchases: Iterable[Purchase],
    scope: SettlementScope = "open",
    settlement_period_id: str | None = None,
) -> list[Purchase]:
    if settlement_period_id:
        return [p for p in purchases if p.settlement_period_id == settlement_period_id]
    if scope == "open":
        return [p for p in purchases if not p.settled]
    if scope == "all":
        return list(purchases)
    raise ValueError("Scope must be 'open' or 'all'.")


def select_open_purchases_for_period(
    purchases: Iterable[Purchase],
    date_from: date,
    date_to: date,
) -> list[Purchase]:
    validate_date_range(date_from, date_to)
    return [
        purchase
        for purchase in purchases
        if not purchase.settled
        and purchase.date is not None
        and date_from <= purchase.date <= date_to
    ]


def preview_settlement_period(
    purchases: Iterable[Purchase],
    all_participants: list[str],
    date_from: date,
    date_to: date,
) -> SettlementPeriodPreview:
    selected = select_open_purchases_for_period(purchases, date_from, date_to)
    balances = calculate_balances(selected, all_participants)
    settlements = calculate_settlements(balances)
    total_amount = sum((purchase.amount for purchase in selected), Decimal("0.00"))
    return SettlementPeriodPreview(
        date_from=date_from,
        date_to=date_to,
        purchases=selected,
        balances=balances,
        settlements=settlements,
        total_amount=total_amount,
    )


def generate_settlement_period_id(
    existing_periods: Iterable[SettlementPeriod],
    date_to: date,
) -> str:
    prefix = f"settlement_{date_to:%Y_%m_%d}"
    existing_ids = {period.id for period in existing_periods}
    counter = 1
    while True:
        candidate = f"{prefix}_{counter:03d}"
        if candidate not in existing_ids:
            return candidate
        counter += 1


def get_settlement_period(
    periods: Iterable[SettlementPeriod],
    settlement_period_id: str,
) -> SettlementPeriod:
    for period in periods:
        if period.id == settlement_period_id:
            return period
    raise ValueError(f"Settlement period '{settlement_period_id}' not found.")


def close_settlement_period(
    purchases: list[Purchase],
    periods: list[SettlementPeriod],
    all_participants: list[str],
    date_from: date,
    date_to: date,
    name: str,
    closed_at: datetime | None = None,
    created_by: str = "cli",
) -> SettlementPeriod:
    preview = preview_settlement_period(purchases, all_participants, date_from, date_to)
    period_id = generate_settlement_period_id(periods, date_to)
    period = SettlementPeriod(
        id=period_id,
        name=name.strip() or period_id,
        status="closed",
        date_from=date_from,
        date_to=date_to,
        closed_at=closed_at or datetime.now(),
        purchase_ids=[purchase.id for purchase in preview.purchases],
        total_amount=preview.total_amount,
        settlements=preview.settlements,
        created_by=created_by,
        notes="Period closed without deleting purchases.",
    )

    selected_ids = set(period.purchase_ids)
    for purchase in purchases:
        if purchase.id in selected_ids:
            purchase.settled = True
            purchase.settlement_period_id = period.id

    periods.append(period)
    return period


def reopen_settlement_period(
    purchases: list[Purchase],
    periods: list[SettlementPeriod],
    settlement_period_id: str,
    reopened_at: datetime | None = None,
) -> SettlementPeriod:
    period = get_settlement_period(periods, settlement_period_id)
    purchase_ids = set(period.purchase_ids)
    for purchase in purchases:
        if purchase.id in purchase_ids and purchase.settlement_period_id == period.id:
            purchase.settled = False
            purchase.settlement_period_id = None

    period.status = "reopened"
    period.reopened_at = reopened_at or datetime.now()
    period.notes = "Period reopened; purchases returned to open scope."
    return period
