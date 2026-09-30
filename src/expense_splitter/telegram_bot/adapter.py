"""Framework-neutral adapter objects for Telegram delivery."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from expense_splitter.reports.result import ReportFile
from expense_splitter.repositories.protocols import (
    CategoryRepository,
    ParticipantRepository,
    PurchaseRepository,
    SettlementPeriodRepository,
)
from expense_splitter.services import PurchaseService, ReportService, SettlementService
from expense_splitter.telegram_bot.states import BotSession


@dataclass(frozen=True)
class TelegramContext:
    telegram_user_id: int
    tenant_id: str = "local"
    participant_name: str | None = None


@dataclass(frozen=True)
class BotReply:
    text: str
    documents: list[ReportFile] = field(default_factory=list)


@dataclass(frozen=True)
class BotServices:
    purchase_service: PurchaseService
    settlement_service: SettlementService
    report_service: ReportService
    purchase_repository: PurchaseRepository
    participant_repository: ParticipantRepository
    category_repository: CategoryRepository
    settlement_period_repository: SettlementPeriodRepository


class BotSessionStore(Protocol):
    def get(self, context: TelegramContext) -> BotSession: ...

    def save(self, session: BotSession) -> None: ...

    def clear(self, context: TelegramContext) -> None: ...


class InMemoryBotSessionStore:
    """Small in-memory session store for tests and local MVP smoke runs."""

    def __init__(self) -> None:
        self._sessions: dict[tuple[int, str], BotSession] = {}

    def get(self, context: TelegramContext) -> BotSession:
        key = _session_key(context)
        if key not in self._sessions:
            self._sessions[key] = BotSession(
                telegram_user_id=context.telegram_user_id,
                tenant_id=context.tenant_id,
                participant_name=context.participant_name,
            )
        session = self._sessions[key]
        if context.participant_name and session.participant_name != context.participant_name:
            session.participant_name = context.participant_name
        return session

    def save(self, session: BotSession) -> None:
        self._sessions[(session.telegram_user_id, session.tenant_id)] = session

    def clear(self, context: TelegramContext) -> None:
        self._sessions.pop(_session_key(context), None)


class TelegramBotAdapter:
    """Thin callable adapter that can be connected to aiogram/webhook later."""

    def __init__(self, handler) -> None:
        self.handler = handler

    def handle_text(
        self,
        text: str,
        *,
        telegram_user_id: int,
        tenant_id: str = "local",
        participant_name: str | None = None,
    ) -> BotReply:
        return self.handler.handle_text(
            TelegramContext(
                telegram_user_id=telegram_user_id,
                tenant_id=tenant_id,
                participant_name=participant_name,
            ),
            text,
        )


def _session_key(context: TelegramContext) -> tuple[int, str]:
    return (context.telegram_user_id, context.tenant_id)
