"""Settlement use cases implemented above repository protocols."""

from __future__ import annotations

from expense_splitter.calculator import calculate_balances
from expense_splitter.models import Balance, Settlement, SettlementPeriod
from expense_splitter.repositories.protocols import (
    ClosePeriodCommand,
    ParticipantRepository,
    PurchaseRepository,
    SettlementPeriodRepository,
)
from expense_splitter.settlement import calculate_settlements
from expense_splitter.settlement_periods import (
    SettlementPeriodPreview,
    SettlementScope,
    SuggestedPeriod,
    close_settlement_period,
    delete_empty_settlement_period,
    delete_empty_settlement_periods,
    filter_purchases_by_settlement_scope,
    preview_settlement_period,
    reopen_settlement_period,
    suggest_next_settlement_period,
    update_settlement_period_metadata,
)


class SettlementService:
    """Thin settlement orchestration layer prepared for future transactions."""

    def __init__(
        self,
        purchases: PurchaseRepository,
        participants: ParticipantRepository,
        settlement_periods: SettlementPeriodRepository,
    ) -> None:
        self.purchases = purchases
        self.participants = participants
        self.settlement_periods = settlement_periods

    def balances(
        self,
        tenant_id: str,
        scope: SettlementScope = "open",
        settlement_period_id: str | None = None,
    ) -> list[Balance]:
        selected = filter_purchases_by_settlement_scope(
            self.purchases.list_purchases(tenant_id),
            scope=scope,
            settlement_period_id=settlement_period_id,
        )
        return calculate_balances(selected, self._participant_names(tenant_id))

    def settlements(
        self,
        tenant_id: str,
        scope: SettlementScope = "open",
        settlement_period_id: str | None = None,
    ) -> list[Settlement]:
        return calculate_settlements(
            self.balances(
                tenant_id,
                scope=scope,
                settlement_period_id=settlement_period_id,
            )
        )

    def preview_period(
        self,
        tenant_id: str,
        command: ClosePeriodCommand,
    ) -> SettlementPeriodPreview:
        return preview_settlement_period(
            self.purchases.list_purchases(tenant_id),
            self._participant_names(tenant_id),
            command.date_from,
            command.date_to,
        )

    def suggest_next_period(self, tenant_id: str) -> SuggestedPeriod:
        return suggest_next_settlement_period(
            self.purchases.list_purchases(tenant_id),
            self.settlement_periods.list_periods(tenant_id),
        )

    def close_period(
        self,
        tenant_id: str,
        command: ClosePeriodCommand,
    ) -> SettlementPeriod:
        purchases = self.purchases.list_purchases(tenant_id)
        periods = self.settlement_periods.list_periods(tenant_id)
        period = close_settlement_period(
            purchases,
            periods,
            self._participant_names(tenant_id),
            command.date_from,
            command.date_to,
            command.name,
            created_by=command.created_by,
        )
        self.purchases.replace_purchases(tenant_id, purchases)
        self.settlement_periods.replace_periods(tenant_id, periods)
        return period

    def reopen_period(
        self,
        tenant_id: str,
        settlement_period_id: str,
    ) -> SettlementPeriod:
        purchases = self.purchases.list_purchases(tenant_id)
        periods = self.settlement_periods.list_periods(tenant_id)
        period = reopen_settlement_period(purchases, periods, settlement_period_id)
        self.purchases.replace_purchases(tenant_id, purchases)
        self.settlement_periods.replace_periods(tenant_id, periods)
        return period

    def rename_period(
        self,
        tenant_id: str,
        settlement_period_id: str,
        *,
        name: str | None = None,
        notes: str | None = None,
    ) -> SettlementPeriod:
        periods = self.settlement_periods.list_periods(tenant_id)
        period = update_settlement_period_metadata(
            periods,
            settlement_period_id,
            name=name,
            notes=notes,
        )
        self.settlement_periods.replace_periods(tenant_id, periods)
        return period

    def delete_empty_period(
        self,
        tenant_id: str,
        settlement_period_id: str,
        confirm: str,
    ) -> SettlementPeriod:
        periods = self.settlement_periods.list_periods(tenant_id)
        deleted = delete_empty_settlement_period(periods, settlement_period_id, confirm)
        self.settlement_periods.replace_periods(tenant_id, periods)
        return deleted

    def delete_empty_periods(
        self,
        tenant_id: str,
        confirm: str,
    ) -> list[SettlementPeriod]:
        periods = self.settlement_periods.list_periods(tenant_id)
        deleted = delete_empty_settlement_periods(periods, confirm)
        self.settlement_periods.replace_periods(tenant_id, periods)
        return deleted

    def _participant_names(self, tenant_id: str) -> list[str]:
        return [
            participant.name
            for participant in self.participants.list_participants(tenant_id)
            if participant.status == "active"
        ]
