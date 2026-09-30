"""Purchase use cases implemented above repository protocols."""

from __future__ import annotations

import uuid
from datetime import date

from expense_splitter.models import DEFAULT_PURCHASE_NAME, Purchase
from expense_splitter.repositories.protocols import (
    AddPurchaseCommand,
    ParticipantRepository,
    PurchasePatch,
    PurchaseRepository,
)

DELETE_PURCHASE_CONFIRM = "DELETE_PURCHASE"


class PurchaseService:
    """Thin purchase orchestration layer with no CLI or GUI dependencies."""

    def __init__(
        self,
        purchases: PurchaseRepository,
        participants: ParticipantRepository,
    ) -> None:
        self.purchases = purchases
        self.participants = participants

    def list_purchases(self, tenant_id: str) -> list[Purchase]:
        return self.purchases.list_purchases(tenant_id)

    def add_purchase(
        self,
        tenant_id: str,
        command: AddPurchaseCommand,
    ) -> Purchase:
        self._validate_people(tenant_id, command.payer, command.participants)
        purchase = Purchase(
            id=str(uuid.uuid4())[:8],
            date=command.purchase_date or date.today(),
            amount=command.amount,
            payer=command.payer,
            participants=list(command.participants),
            purchase_name=command.purchase_name.strip() or DEFAULT_PURCHASE_NAME,
            category=command.category or None,
            comment=command.comment or None,
        )
        return self.purchases.add_purchase(tenant_id, purchase)

    def update_purchase(
        self,
        tenant_id: str,
        purchase_id: str,
        patch: PurchasePatch,
    ) -> Purchase:
        current = self._get_existing_purchase(tenant_id, purchase_id)
        self._ensure_purchase_is_open(current)
        self._validate_people(
            tenant_id,
            patch.payer or current.payer,
            patch.participants or current.participants,
        )
        return self.purchases.update_purchase(tenant_id, purchase_id, patch)

    def delete_purchase(
        self,
        tenant_id: str,
        purchase_id: str,
        confirm: str,
    ) -> Purchase:
        if confirm != DELETE_PURCHASE_CONFIRM:
            raise ValueError("Для удаления введите DELETE_PURCHASE без изменений.")

        existing = self._get_existing_purchase(tenant_id, purchase_id)
        self._ensure_purchase_is_open(existing)
        remaining = [
            purchase
            for purchase in self.purchases.list_purchases(tenant_id)
            if purchase.id != purchase_id
        ]
        self.purchases.replace_purchases(tenant_id, remaining)
        return existing

    def _get_existing_purchase(self, tenant_id: str, purchase_id: str) -> Purchase:
        purchase = self.purchases.get_purchase(tenant_id, purchase_id)
        if purchase is None:
            raise ValueError(f"Покупка не найдена: {purchase_id}")
        return purchase

    @staticmethod
    def _ensure_purchase_is_open(purchase: Purchase) -> None:
        if purchase.settled or purchase.settlement_period_id:
            raise ValueError(
                "Покупка относится к закрытому периоду взаиморасчетов. "
                "Сначала переоткройте период или создайте корректирующую покупку."
            )

    def _validate_people(
        self,
        tenant_id: str,
        payer: str,
        participants: list[str],
    ) -> None:
        known_names = {
            participant.name
            for participant in self.participants.list_participants(tenant_id)
        }
        if payer not in known_names:
            raise ValueError(f"Участник-плательщик не найден: {payer}")
        missing = [participant for participant in participants if participant not in known_names]
        if missing:
            raise ValueError(f"Участники не найдены: {', '.join(missing)}")
