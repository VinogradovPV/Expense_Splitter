"""Conversation state for the Telegram bot MVP."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import StrEnum


class BotState(StrEnum):
    IDLE = "idle"
    AWAITING_PURCHASE_NAME = "awaiting_purchase_name"
    AWAITING_AMOUNT = "awaiting_amount"
    AWAITING_PAYER = "awaiting_payer"
    AWAITING_PARTICIPANTS = "awaiting_participants"
    AWAITING_CATEGORY = "awaiting_category"
    AWAITING_DATE = "awaiting_date"
    AWAITING_COMMENT = "awaiting_comment"
    CONFIRM_PURCHASE = "confirm_purchase"
    CONFIRM_DELETE_PURCHASE = "confirm_delete_purchase"


@dataclass
class PurchaseDraft:
    purchase_name: str = ""
    amount: Decimal | None = None
    payer: str | None = None
    participants: list[str] = field(default_factory=list)
    category: str | None = None
    purchase_date: date | None = None
    comment: str | None = None


@dataclass
class BotSession:
    telegram_user_id: int
    tenant_id: str
    participant_name: str | None = None
    state: BotState = BotState.IDLE
    draft: PurchaseDraft = field(default_factory=PurchaseDraft)
    pending_delete_purchase_id: str | None = None

    def reset_flow(self) -> None:
        self.state = BotState.IDLE
        self.draft = PurchaseDraft()
        self.pending_delete_purchase_id = None
