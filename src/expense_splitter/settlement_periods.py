from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Iterable, Literal

from expense_splitter.calculator import calculate_balances
from expense_splitter.models import Balance, Purchase, Settlement, SettlementPeriod
from expense_splitter.settlement import calculate_settlements

SettlementScope = Literal["open", "all"]
DELETE_EMPTY_PERIOD_CONFIRM = "DELETE_EMPTY_PERIOD"
DELETE_EMPTY_PERIODS_CONFIRM = "DELETE_EMPTY_PERIODS"


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


@dataclass(frozen=True)
class SuggestedPeriod:
    date_from: date
    date_to: date
    name: str
    reason: str


def parse_period_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid date '{value}'. Expected YYYY-MM-DD.") from exc


def validate_date_range(date_from: date, date_to: date) -> None:
    if date_from > date_to:
        raise ValueError("--from must not be after --to.")


def default_period_name(date_from: date, date_to: date) -> str:
    if date_from == date_to:
        return f"Период за {date_from.isoformat()}"
    return f"Период с {date_from.isoformat()} по {date_to.isoformat()}"


def is_empty_settlement_period(period: SettlementPeriod) -> bool:
    return (
        len(period.purchase_ids) == 0
        and period.total_amount == Decimal("0.00")
        and len(period.settlements) == 0
    )


def is_meaningful_closed_period(period: SettlementPeriod) -> bool:
    return (
        period.status == "closed"
        and len(period.purchase_ids) > 0
        and period.total_amount > 0
    )


def suggest_next_settlement_period(
    purchases: Iterable[Purchase],
    settlement_periods: Iterable[SettlementPeriod],
    today: date | None = None,
) -> SuggestedPeriod:
    current_date = today or date.today()
    meaningful = [
        period for period in settlement_periods if is_meaningful_closed_period(period)
    ]
    if meaningful:
        last_period = max(meaningful, key=lambda period: (period.date_to, period.id))
        date_from = last_period.date_to + timedelta(days=1)
        return SuggestedPeriod(
            date_from=date_from,
            date_to=current_date,
            name=default_period_name(date_from, current_date),
            reason="last_meaningful_closed_period",
        )

    dated_open = [
        purchase.date
        for purchase in purchases
        if not purchase.settled and purchase.date is not None
    ]
    if dated_open:
        date_from = min(dated_open)
        return SuggestedPeriod(
            date_from=date_from,
            date_to=current_date,
            name=default_period_name(date_from, current_date),
            reason="first_open_purchase_date",
        )

    return SuggestedPeriod(
        date_from=current_date,
        date_to=current_date,
        name=default_period_name(current_date, current_date),
        reason="no_open_purchases",
    )


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
    if preview.purchase_count == 0:
        raise ValueError(
            "Период без покупок не создается обычным close flow. "
            "Скорректируйте даты или используйте отдельный advanced-flow."
        )
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


def update_settlement_period_metadata(
    periods: list[SettlementPeriod],
    settlement_period_id: str,
    *,
    name: str | None = None,
    notes: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> SettlementPeriod:
    period = get_settlement_period(periods, settlement_period_id)
    has_new_dates = date_from is not None or date_to is not None
    if has_new_dates and not is_empty_settlement_period(period):
        raise ValueError(
            "Даты закрытого периода с покупками нельзя изменить напрямую. "
            "Переоткройте период и закройте новый диапазон."
        )

    new_date_from = date_from or period.date_from
    new_date_to = date_to or period.date_to
    validate_date_range(new_date_from, new_date_to)
    period.name = (name or "").strip() or period.name
    period.notes = notes.strip() if notes is not None else period.notes
    if is_empty_settlement_period(period):
        period.date_from = new_date_from
        period.date_to = new_date_to
    return period


def delete_empty_settlement_period(
    periods: list[SettlementPeriod],
    settlement_period_id: str,
    confirm: str,
) -> SettlementPeriod:
    if confirm != DELETE_EMPTY_PERIOD_CONFIRM:
        raise ValueError("Для удаления введите DELETE_EMPTY_PERIOD без изменений.")
    period = get_settlement_period(periods, settlement_period_id)
    if not is_empty_settlement_period(period):
        raise ValueError(
            "Период содержит покупки или переводы. Для сохранения истории его нельзя удалить. "
            "Используйте переоткрытие периода или отчет периода."
        )
    periods.remove(period)
    return period


def delete_empty_settlement_periods(
    periods: list[SettlementPeriod],
    confirm: str,
) -> list[SettlementPeriod]:
    if confirm != DELETE_EMPTY_PERIODS_CONFIRM:
        raise ValueError("Для удаления введите DELETE_EMPTY_PERIODS без изменений.")
    deleted = [period for period in periods if is_empty_settlement_period(period)]
    if not deleted:
        return []
    remaining = [period for period in periods if not is_empty_settlement_period(period)]
    periods[:] = remaining
    return deleted
