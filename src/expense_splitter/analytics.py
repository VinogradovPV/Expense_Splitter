from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Sequence

from expense_splitter.calculator import calculate_balances
from expense_splitter.models import DEFAULT_PURCHASE_NAME, Balance, Group, Participant, Purchase, Settlement
from expense_splitter.settlement import calculate_settlements


UNCATEGORIZED = "Без категории"


@dataclass(frozen=True)
class PeriodSpec:
    period: str
    year: int
    start_date: date
    end_date: date
    period_id: str
    month: int | None = None
    quarter: int | None = None


@dataclass(frozen=True)
class AnalyticsDataset:
    period_spec: PeriodSpec
    participants: list[str]
    groups: list[Group]
    purchases: list[Purchase]
    balances: list[Balance]
    settlements: list[Settlement]
    summary: dict[str, object]
    by_category: list[dict[str, object]]
    by_payer: list[dict[str, object]]
    by_participant: list[dict[str, object]]
    top_purchases: list[dict[str, object]]
    warnings: list[dict[str, object]]


def parse_period(
    period: str,
    year: int,
    month: int | None = None,
    quarter: int | None = None,
) -> PeriodSpec:
    period_key = period.lower()

    if period_key == "month":
        if month is None or not 1 <= month <= 12:
            raise ValueError("Month period requires month in range 1..12.")
        last_day = calendar.monthrange(year, month)[1]
        return PeriodSpec(
            period=period_key,
            year=year,
            month=month,
            start_date=date(year, month, 1),
            end_date=date(year, month, last_day),
            period_id=f"{year:04d}-{month:02d}",
        )

    if period_key == "quarter":
        if quarter is None or not 1 <= quarter <= 4:
            raise ValueError("Quarter period requires quarter in range 1..4.")
        start_month = (quarter - 1) * 3 + 1
        end_month = start_month + 2
        last_day = calendar.monthrange(year, end_month)[1]
        return PeriodSpec(
            period=period_key,
            year=year,
            quarter=quarter,
            start_date=date(year, start_month, 1),
            end_date=date(year, end_month, last_day),
            period_id=f"{year:04d}-Q{quarter}",
        )

    if period_key == "year":
        return PeriodSpec(
            period=period_key,
            year=year,
            start_date=date(year, 1, 1),
            end_date=date(year, 12, 31),
            period_id=f"{year:04d}",
        )

    raise ValueError("Period must be one of: month, quarter, year.")


def filter_purchases_by_period(
    purchases: Sequence[Purchase],
    period_spec: PeriodSpec,
    include_undated: bool = False,
) -> list[Purchase]:
    filtered: list[Purchase] = []
    for purchase in purchases:
        if purchase.date is None:
            if include_undated:
                filtered.append(purchase)
            continue
        if period_spec.start_date <= purchase.date <= period_spec.end_date:
            filtered.append(purchase)
    return filtered


def build_analytics_dataset(
    participants: Sequence[Participant | str],
    groups: Sequence[Group],
    purchases: Sequence[Purchase],
    period_spec: PeriodSpec,
    include_undated: bool = False,
) -> AnalyticsDataset:
    participant_names = _participant_names(participants)
    period_purchases = filter_purchases_by_period(purchases, period_spec, include_undated)
    balances = calculate_balances(period_purchases, participant_names)
    settlements = calculate_settlements(balances)
    warnings = build_warnings(purchases)

    return AnalyticsDataset(
        period_spec=period_spec,
        participants=participant_names,
        groups=list(groups),
        purchases=period_purchases,
        balances=balances,
        settlements=settlements,
        summary=aggregate_summary(period_purchases, participant_names, period_spec),
        by_category=aggregate_by_category(period_purchases),
        by_payer=aggregate_by_payer(period_purchases),
        by_participant=aggregate_by_participant(period_purchases, participant_names),
        top_purchases=build_top_purchases(period_purchases),
        warnings=warnings,
    )


def aggregate_summary(
    purchases: Sequence[Purchase],
    participants: Sequence[Participant | str],
    period_spec: PeriodSpec,
) -> dict[str, object]:
    total_amount = sum((purchase.amount for purchase in purchases), Decimal("0.00"))
    purchase_count = len(purchases)
    average_purchase = (
        (total_amount / Decimal(purchase_count)).quantize(Decimal("0.01"))
        if purchase_count
        else Decimal("0.00")
    )

    return {
        "period": period_spec.period,
        "period_id": period_spec.period_id,
        "start_date": period_spec.start_date,
        "end_date": period_spec.end_date,
        "total_amount": total_amount,
        "purchase_count": purchase_count,
        "average_purchase": average_purchase,
        "participant_count": len(_participant_names(participants)),
    }


def aggregate_by_category(purchases: Sequence[Purchase]) -> list[dict[str, object]]:
    totals: dict[str, dict[str, object]] = {}
    for purchase in purchases:
        category = purchase.category or UNCATEGORIZED
        row = totals.setdefault(
            category,
            {"category": category, "purchase_count": 0, "total_amount": Decimal("0.00")},
        )
        row["purchase_count"] = int(row["purchase_count"]) + 1
        row["total_amount"] = row["total_amount"] + purchase.amount
    return sorted(totals.values(), key=lambda row: (-row["total_amount"], row["category"]))


def aggregate_by_payer(purchases: Sequence[Purchase]) -> list[dict[str, object]]:
    totals: dict[str, dict[str, object]] = {}
    for purchase in purchases:
        row = totals.setdefault(
            purchase.payer,
            {"payer": purchase.payer, "purchase_count": 0, "total_paid": Decimal("0.00")},
        )
        row["purchase_count"] = int(row["purchase_count"]) + 1
        row["total_paid"] = row["total_paid"] + purchase.amount
    return sorted(totals.values(), key=lambda row: (-row["total_paid"], row["payer"]))


def aggregate_by_participant(
    purchases: Sequence[Purchase],
    participants: Sequence[Participant | str],
) -> list[dict[str, object]]:
    participant_names = _participant_names(participants)
    balances = calculate_balances(list(purchases), participant_names)
    purchase_counts = {name: 0 for name in participant_names}
    for purchase in purchases:
        for participant in purchase.participants:
            purchase_counts[participant] = purchase_counts.get(participant, 0) + 1

    rows = [
        {
            "participant": balance.participant,
            "purchase_count": purchase_counts.get(balance.participant, 0),
            "total_share": balance.share,
        }
        for balance in balances
    ]
    return sorted(rows, key=lambda row: (-row["total_share"], row["participant"]))


def build_top_purchases(
    purchases: Sequence[Purchase],
    limit: int = 10,
) -> list[dict[str, object]]:
    if limit < 1:
        raise ValueError("Top purchases limit must be greater than zero.")

    sorted_purchases = sorted(
        purchases,
        key=lambda purchase: (-purchase.amount, purchase.date or date.min, purchase.id),
    )
    return [
        {
            "rank": index,
            "id": purchase.id,
            "date": purchase.date,
            "purchase_name": purchase.purchase_name or DEFAULT_PURCHASE_NAME,
            "amount": purchase.amount,
            "payer": purchase.payer,
            "category": purchase.category or UNCATEGORIZED,
            "participants": list(purchase.participants),
        }
        for index, purchase in enumerate(sorted_purchases[:limit], start=1)
    ]


def build_warnings(purchases: Sequence[Purchase]) -> list[dict[str, object]]:
    warnings: list[dict[str, object]] = []
    for purchase in purchases:
        if purchase.date is None:
            warnings.append(
                {
                    "warning_type": "undated_purchase",
                    "purchase_id": purchase.id,
                    "purchase_name": purchase.purchase_name or DEFAULT_PURCHASE_NAME,
                    "message": "Покупка без даты не включается в периодную аналитику по умолчанию.",
                }
            )
    return warnings


def _participant_names(participants: Sequence[Participant | str]) -> list[str]:
    return [participant.name if isinstance(participant, Participant) else str(participant) for participant in participants]
