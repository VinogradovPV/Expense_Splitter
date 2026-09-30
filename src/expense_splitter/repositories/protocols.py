"""Storage-neutral repository protocols for cloud-ready adapters.

These contracts intentionally do not import CLI, GUI, SQL, or YAML modules.
They describe the boundary that future YAML and PostgreSQL repositories should implement.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol

from expense_splitter.models import CategoryEntry, Participant, Purchase, SettlementPeriod


@dataclass(frozen=True)
class PurchasePatch:
    purchase_name: str | None = None
    purchase_date: date | None = None
    amount: Decimal | None = None
    payer: str | None = None
    participants: list[str] | None = None
    category: str | None = None
    comment: str | None = None
    settled: bool | None = None
    settlement_period_id: str | None = None


@dataclass(frozen=True)
class AddPurchaseCommand:
    purchase_name: str
    amount: Decimal
    payer: str
    participants: list[str]
    purchase_date: date | None = None
    category: str | None = None
    comment: str | None = None


@dataclass(frozen=True)
class ClosePeriodCommand:
    date_from: date
    date_to: date
    name: str
    created_by: str = "service"


@dataclass(frozen=True)
class ReportRequest:
    report_type: str
    formats: set[str]
    scope: str | None = None
    settlement_period_id: str | None = None
    period_kind: str | None = None
    year: int | None = None
    month: int | None = None
    quarter: int | None = None


class PurchaseRepository(Protocol):
    def list_purchases(self, tenant_id: str) -> list[Purchase]: ...

    def get_purchase(self, tenant_id: str, purchase_id: str) -> Purchase | None: ...

    def add_purchase(self, tenant_id: str, purchase: Purchase) -> Purchase: ...

    def update_purchase(
        self,
        tenant_id: str,
        purchase_id: str,
        patch: PurchasePatch,
    ) -> Purchase: ...

    def replace_purchases(self, tenant_id: str, purchases: list[Purchase]) -> None: ...


class ParticipantRepository(Protocol):
    def list_participants(self, tenant_id: str) -> list[Participant]: ...

    def save_participants(self, tenant_id: str, participants: list[Participant]) -> None: ...


class CategoryRepository(Protocol):
    def list_categories(self, tenant_id: str) -> list[CategoryEntry]: ...

    def save_categories(self, tenant_id: str, categories: list[CategoryEntry]) -> None: ...


class SettlementPeriodRepository(Protocol):
    def list_periods(self, tenant_id: str) -> list[SettlementPeriod]: ...

    def get_period(self, tenant_id: str, period_id: str) -> SettlementPeriod | None: ...

    def save_period(self, tenant_id: str, period: SettlementPeriod) -> SettlementPeriod: ...

    def replace_periods(self, tenant_id: str, periods: list[SettlementPeriod]) -> None: ...


class ExpenseUnitOfWork(Protocol):
    purchases: PurchaseRepository
    participants: ParticipantRepository
    categories: CategoryRepository
    settlement_periods: SettlementPeriodRepository

    def __enter__(self) -> "ExpenseUnitOfWork": ...

    def __exit__(self, exc_type, exc, tb) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
