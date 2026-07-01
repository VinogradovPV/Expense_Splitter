"""YAML-backed repository adapter for the local desktop/offline mode."""

from dataclasses import replace
from pathlib import Path

from expense_splitter.models import CategoryEntry, Participant, Purchase, SettlementPeriod
from expense_splitter.repositories.protocols import PurchasePatch
from expense_splitter.storage import (
    load_category_entries,
    load_participants,
    load_purchases,
    load_settlement_periods,
    save_category_entries,
    save_participants,
    save_purchases,
    save_settlement_periods,
)

LOCAL_TENANT_ID = "local"


class YamlRepositoryTenantError(ValueError):
    """Raised when the local YAML repository is used for a non-local tenant."""


class YamlExpenseRepository:
    """Repository adapter that preserves the current YAML storage behavior."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)

    def list_purchases(self, tenant_id: str) -> list[Purchase]:
        self._validate_tenant(tenant_id)
        return load_purchases(self._purchases_path)

    def get_purchase(self, tenant_id: str, purchase_id: str) -> Purchase | None:
        self._validate_tenant(tenant_id)
        return next(
            (
                purchase
                for purchase in load_purchases(self._purchases_path)
                if purchase.id == purchase_id
            ),
            None,
        )

    def add_purchase(self, tenant_id: str, purchase: Purchase) -> Purchase:
        self._validate_tenant(tenant_id)
        purchases = load_purchases(self._purchases_path)
        purchases.append(purchase)
        save_purchases(self._purchases_path, purchases)
        return purchase

    def update_purchase(
        self,
        tenant_id: str,
        purchase_id: str,
        patch: PurchasePatch,
    ) -> Purchase:
        self._validate_tenant(tenant_id)
        purchases = load_purchases(self._purchases_path)
        for index, purchase in enumerate(purchases):
            if purchase.id != purchase_id:
                continue
            updated = self._apply_purchase_patch(purchase, patch)
            purchases[index] = updated
            save_purchases(self._purchases_path, purchases)
            return updated
        raise KeyError(f"Purchase not found: {purchase_id}")

    def replace_purchases(self, tenant_id: str, purchases: list[Purchase]) -> None:
        self._validate_tenant(tenant_id)
        save_purchases(self._purchases_path, purchases)

    def list_participants(self, tenant_id: str) -> list[Participant]:
        self._validate_tenant(tenant_id)
        return load_participants(self._participants_path)

    def save_participants(self, tenant_id: str, participants: list[Participant]) -> None:
        self._validate_tenant(tenant_id)
        save_participants(self._participants_path, participants)

    def list_categories(self, tenant_id: str) -> list[CategoryEntry]:
        self._validate_tenant(tenant_id)
        return load_category_entries(self._categories_path)

    def save_categories(self, tenant_id: str, categories: list[CategoryEntry]) -> None:
        self._validate_tenant(tenant_id)
        save_category_entries(self._categories_path, categories)

    def list_periods(self, tenant_id: str) -> list[SettlementPeriod]:
        self._validate_tenant(tenant_id)
        return load_settlement_periods(self._periods_path)

    def get_period(self, tenant_id: str, period_id: str) -> SettlementPeriod | None:
        self._validate_tenant(tenant_id)
        return next(
            (
                period
                for period in load_settlement_periods(self._periods_path)
                if period.id == period_id
            ),
            None,
        )

    def save_period(self, tenant_id: str, period: SettlementPeriod) -> SettlementPeriod:
        self._validate_tenant(tenant_id)
        periods = load_settlement_periods(self._periods_path)
        for index, existing in enumerate(periods):
            if existing.id == period.id:
                periods[index] = period
                save_settlement_periods(self._periods_path, periods)
                return period
        periods.append(period)
        save_settlement_periods(self._periods_path, periods)
        return period

    def replace_periods(self, tenant_id: str, periods: list[SettlementPeriod]) -> None:
        self._validate_tenant(tenant_id)
        save_settlement_periods(self._periods_path, periods)

    @property
    def _participants_path(self) -> Path:
        return self.data_dir / "participants.yaml"

    @property
    def _purchases_path(self) -> Path:
        return self.data_dir / "purchases.yaml"

    @property
    def _categories_path(self) -> Path:
        return self.data_dir / "categories.yaml"

    @property
    def _periods_path(self) -> Path:
        return self.data_dir / "settlement_periods.yaml"

    def _validate_tenant(self, tenant_id: str) -> None:
        if tenant_id != LOCAL_TENANT_ID:
            raise YamlRepositoryTenantError(
                f"YAML repository supports only tenant_id='{LOCAL_TENANT_ID}': {tenant_id}"
            )

    @staticmethod
    def _apply_purchase_patch(purchase: Purchase, patch: PurchasePatch) -> Purchase:
        updates = {
            "purchase_name": patch.purchase_name,
            "date": patch.purchase_date,
            "amount": patch.amount,
            "payer": patch.payer,
            "participants": patch.participants,
            "category": patch.category,
            "comment": patch.comment,
            "settled": patch.settled,
            "settlement_period_id": patch.settlement_period_id,
        }
        return replace(
            purchase,
            **{field: value for field, value in updates.items() if value is not None},
        )
