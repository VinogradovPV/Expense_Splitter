"""Future PostgreSQL repository adapter contract.

CLOUD.5 adds schema and migration foundations. The live adapter will be implemented after
SQLAlchemy/Alembic wiring is introduced; until then this class fails explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass

from expense_splitter.models import CategoryEntry, Participant, Purchase, SettlementPeriod
from expense_splitter.repositories.protocols import PurchasePatch


class PostgresRepositoryNotImplementedError(NotImplementedError):
    """Raised when the PostgreSQL repository stub is used before CLOUD.6+ implementation."""


@dataclass(frozen=True)
class PostgresRepositoryConfig:
    database_url: str


class PostgresExpenseRepository:
    """Placeholder that documents the repository boundary for PostgreSQL mode."""

    def __init__(self, config: PostgresRepositoryConfig) -> None:
        self.config = config

    def list_purchases(self, tenant_id: str) -> list[Purchase]:
        self._not_implemented()

    def get_purchase(self, tenant_id: str, purchase_id: str) -> Purchase | None:
        self._not_implemented()

    def add_purchase(self, tenant_id: str, purchase: Purchase) -> Purchase:
        self._not_implemented()

    def update_purchase(
        self,
        tenant_id: str,
        purchase_id: str,
        patch: PurchasePatch,
    ) -> Purchase:
        self._not_implemented()

    def replace_purchases(self, tenant_id: str, purchases: list[Purchase]) -> None:
        self._not_implemented()

    def list_participants(self, tenant_id: str) -> list[Participant]:
        self._not_implemented()

    def save_participants(self, tenant_id: str, participants: list[Participant]) -> None:
        self._not_implemented()

    def list_categories(self, tenant_id: str) -> list[CategoryEntry]:
        self._not_implemented()

    def save_categories(self, tenant_id: str, categories: list[CategoryEntry]) -> None:
        self._not_implemented()

    def list_periods(self, tenant_id: str) -> list[SettlementPeriod]:
        self._not_implemented()

    def get_period(self, tenant_id: str, period_id: str) -> SettlementPeriod | None:
        self._not_implemented()

    def save_period(self, tenant_id: str, period: SettlementPeriod) -> SettlementPeriod:
        self._not_implemented()

    def replace_periods(self, tenant_id: str, periods: list[SettlementPeriod]) -> None:
        self._not_implemented()

    def _not_implemented(self):
        raise PostgresRepositoryNotImplementedError(
            "PostgreSQL repository execution is planned for CLOUD.6+. "
            "CLOUD.5 only defines schema, migration, and repository contract."
        )
