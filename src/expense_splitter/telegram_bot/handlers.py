"""Command handlers for the Telegram bot MVP."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from expense_splitter.analytics import parse_period
from expense_splitter.models import DEFAULT_PURCHASE_NAME, Purchase
from expense_splitter.reports.result import ReportFile, ReportResult
from expense_splitter.repositories.protocols import (
    AddPurchaseCommand,
    ClosePeriodCommand,
    PurchasePatch,
)
from expense_splitter.services import DELETE_PURCHASE_CONFIRM
from expense_splitter.telegram_bot import messages
from expense_splitter.telegram_bot.adapter import (
    BotReply,
    BotServices,
    BotSessionStore,
    TelegramContext,
)
from expense_splitter.telegram_bot.states import BotSession, BotState


class TelegramBotHandler:
    """Telegram command handler that delegates all business actions to services."""

    def __init__(self, services: BotServices, sessions: BotSessionStore) -> None:
        self.services = services
        self.sessions = sessions

    def handle_text(self, context: TelegramContext, text: str) -> BotReply:
        message = text.strip()
        session = self.sessions.get(context)

        try:
            if message.startswith("/"):
                return self._handle_command(context, session, message)
            if session.state != BotState.IDLE:
                return self._handle_flow(context, session, message)
            return BotReply(messages.UNKNOWN_COMMAND_MESSAGE)
        except ValueError as exc:
            return BotReply(str(exc) or messages.GENERIC_ERROR_MESSAGE)

    def _handle_command(
        self,
        context: TelegramContext,
        session: BotSession,
        message: str,
    ) -> BotReply:
        parts = message.split()
        command = parts[0].lower()
        args = parts[1:]

        if command == "/start":
            session.reset_flow()
            self.sessions.save(session)
            return BotReply(messages.START_MESSAGE)
        if command == "/help":
            return BotReply(messages.HELP_MESSAGE)
        if command == "/cancel":
            session.reset_flow()
            self.sessions.save(session)
            return BotReply(messages.CANCEL_MESSAGE)
        if command == "/add_purchase":
            session.reset_flow()
            session.state = BotState.AWAITING_PURCHASE_NAME
            self.sessions.save(session)
            return BotReply(messages.prompt_purchase_name())
        if command == "/purchases":
            return BotReply(
                messages.purchase_list(
                    self.services.purchase_service.list_purchases(context.tenant_id)
                )
            )
        if command == "/edit_purchase":
            return self._edit_purchase(context, args)
        if command == "/delete_purchase":
            return self._delete_purchase(context, session, args)
        if command == "/confirm_delete_purchase":
            return self._confirm_delete_purchase(context, session, args)
        if command == "/current_pdf":
            return self._current_report(context, "pdf")
        if command == "/current_xlsx":
            return self._current_report(context, "xlsx")
        if command == "/analytics":
            return self._analytics_report(context, args)
        if command == "/periods":
            return BotReply(
                messages.periods_list(
                    self.services.settlement_period_repository.list_periods(context.tenant_id)
                )
            )
        if command == "/period_report":
            return self._period_report(context, args)
        if command == "/close_period":
            return self._close_period(context, args)
        return BotReply(messages.UNKNOWN_COMMAND_MESSAGE)

    def _handle_flow(
        self,
        context: TelegramContext,
        session: BotSession,
        message: str,
    ) -> BotReply:
        if session.state == BotState.AWAITING_PURCHASE_NAME:
            session.draft.purchase_name = _optional_value(message) or DEFAULT_PURCHASE_NAME
            session.state = BotState.AWAITING_AMOUNT
            self.sessions.save(session)
            return BotReply(messages.prompt_amount())
        if session.state == BotState.AWAITING_AMOUNT:
            session.draft.amount = _parse_amount(message)
            session.state = BotState.AWAITING_PAYER
            self.sessions.save(session)
            return BotReply(messages.prompt_payer(session.participant_name))
        if session.state == BotState.AWAITING_PAYER:
            session.draft.payer = _optional_value(message) or session.participant_name
            if not session.draft.payer:
                raise ValueError("Введите плательщика.")
            session.state = BotState.AWAITING_PARTICIPANTS
            self.sessions.save(session)
            return BotReply(messages.prompt_participants())
        if session.state == BotState.AWAITING_PARTICIPANTS:
            session.draft.participants = self._parse_participants(context.tenant_id, message)
            session.state = BotState.AWAITING_CATEGORY
            self.sessions.save(session)
            return BotReply(messages.prompt_category())
        if session.state == BotState.AWAITING_CATEGORY:
            session.draft.category = _optional_value(message)
            session.state = BotState.AWAITING_DATE
            self.sessions.save(session)
            return BotReply(messages.prompt_date())
        if session.state == BotState.AWAITING_DATE:
            session.draft.purchase_date = _parse_date_or_today(message)
            session.state = BotState.AWAITING_COMMENT
            self.sessions.save(session)
            return BotReply(messages.prompt_comment())
        if session.state == BotState.AWAITING_COMMENT:
            session.draft.comment = _optional_value(message)
            session.state = BotState.CONFIRM_PURCHASE
            self.sessions.save(session)
            return BotReply(messages.purchase_preview(session.draft))
        if session.state == BotState.CONFIRM_PURCHASE:
            return self._confirm_purchase(context, session, message)
        if session.state == BotState.CONFIRM_DELETE_PURCHASE:
            return self._confirm_delete_purchase(
                context,
                session,
                [session.pending_delete_purchase_id or "", message],
            )
        return BotReply(messages.UNKNOWN_COMMAND_MESSAGE)

    def _confirm_purchase(
        self,
        context: TelegramContext,
        session: BotSession,
        message: str,
    ) -> BotReply:
        value = message.strip().casefold()
        if value not in {"yes", "y", "да", "д"}:
            session.reset_flow()
            self.sessions.save(session)
            return BotReply(messages.CANCEL_MESSAGE)

        draft = session.draft
        purchase = self.services.purchase_service.add_purchase(
            context.tenant_id,
            AddPurchaseCommand(
                purchase_name=draft.purchase_name,
                amount=draft.amount or Decimal("0"),
                payer=draft.payer or "",
                participants=draft.participants,
                purchase_date=draft.purchase_date,
                category=draft.category,
                comment=draft.comment,
            ),
        )
        session.reset_flow()
        self.sessions.save(session)
        return BotReply(messages.purchase_saved(purchase))

    def _edit_purchase(self, context: TelegramContext, args: list[str]) -> BotReply:
        if len(args) < 2:
            return BotReply(
                "Формат: /edit_purchase <id> amount=1250 category=еда comment=текст"
            )
        purchase_id = args[0]
        patch = _parse_purchase_patch(args[1:])
        purchase = self.services.purchase_service.update_purchase(
            context.tenant_id,
            purchase_id,
            patch,
        )
        return BotReply(messages.purchase_updated(purchase))

    def _delete_purchase(
        self,
        context: TelegramContext,
        session: BotSession,
        args: list[str],
    ) -> BotReply:
        if not args:
            return BotReply(f"Формат: /delete_purchase <id> {DELETE_PURCHASE_CONFIRM}")
        purchase_id = args[0]
        if len(args) < 2 or args[1] != DELETE_PURCHASE_CONFIRM:
            session.pending_delete_purchase_id = purchase_id
            session.state = BotState.CONFIRM_DELETE_PURCHASE
            self.sessions.save(session)
            return BotReply(messages.purchase_delete_preview(purchase_id))

        purchase = self.services.purchase_service.delete_purchase(
            context.tenant_id,
            purchase_id,
            args[1],
        )
        session.reset_flow()
        self.sessions.save(session)
        return BotReply(messages.purchase_deleted(purchase))

    def _confirm_delete_purchase(
        self,
        context: TelegramContext,
        session: BotSession,
        args: list[str],
    ) -> BotReply:
        if len(args) < 2 or not args[0] or args[1] != DELETE_PURCHASE_CONFIRM:
            return BotReply(messages.purchase_delete_preview(args[0] if args else ""))
        purchase = self.services.purchase_service.delete_purchase(
            context.tenant_id,
            args[0],
            args[1],
        )
        session.reset_flow()
        self.sessions.save(session)
        return BotReply(messages.purchase_deleted(purchase))

    def _current_report(self, context: TelegramContext, format_name: str) -> BotReply:
        result = self.services.report_service.create_current_report(
            context.tenant_id,
            scope="open",
            formats={format_name},
        )
        return _reply_with_report(result, format_name)

    def _analytics_report(self, context: TelegramContext, args: list[str]) -> BotReply:
        if len(args) < 3:
            return BotReply("Формат: /analytics month 2026 7 pdf или /analytics year 2026 xlsx")
        period = args[0]
        year = int(args[1])
        format_name = args[-1].lower()
        month = int(args[2]) if period == "month" and len(args) >= 4 else None
        quarter = int(args[2]) if period == "quarter" and len(args) >= 4 else None
        if period == "year":
            format_name = args[2].lower()
        period_spec = parse_period(period, year, month=month, quarter=quarter)
        result = self.services.report_service.create_analytics_report(
            context.tenant_id,
            period_spec,
            formats={format_name},
        )
        return _reply_with_report(result, format_name)

    def _period_report(self, context: TelegramContext, args: list[str]) -> BotReply:
        if len(args) < 2:
            return BotReply("Формат: /period_report <period_id> pdf|xlsx")
        period_id = args[0]
        format_name = args[1].lower()
        result = self.services.report_service.create_settlement_period_report(
            context.tenant_id,
            period_id,
            formats={format_name},
        )
        return _reply_with_report(result, format_name)

    def _close_period(self, context: TelegramContext, args: list[str]) -> BotReply:
        values = _parse_key_values(args)
        required = {"from", "to", "name"}
        missing = sorted(required - values.keys())
        if missing:
            return BotReply(
                "Формат: /close_period from=2026-07-01 to=2026-07-31 "
                "name=Июль confirm=CLOSE_PERIOD"
            )
        if values.get("confirm") != messages.CLOSE_PERIOD_CONFIRM:
            return BotReply(messages.close_period_confirm_hint())

        period = self.services.settlement_service.close_period(
            context.tenant_id,
            ClosePeriodCommand(
                date_from=_parse_date(values["from"]),
                date_to=_parse_date(values["to"]),
                name=values["name"],
                created_by="telegram",
            ),
        )
        return BotReply(messages.period_closed(period))

    def _parse_participants(self, tenant_id: str, message: str) -> list[str]:
        if message.strip().casefold() == "all":
            return [
                participant.name
                for participant in self.services.participant_repository.list_participants(tenant_id)
                if participant.status == "active"
            ]
        participants = [item.strip() for item in message.split(",") if item.strip()]
        if not participants:
            raise ValueError("Введите хотя бы одного участника.")
        return participants


def _reply_with_report(result: ReportResult, format_name: str) -> BotReply:
    files = _select_report_files(result, format_name)
    if not files:
        return BotReply(messages.no_report_file(format_name))
    return BotReply(messages.report_ready(result), documents=files)


def _select_report_files(result: ReportResult, format_name: str) -> list[ReportFile]:
    return [file for file in result.files if file.format == format_name]


def _parse_purchase_patch(tokens: list[str]) -> PurchasePatch:
    values = _parse_key_values(tokens)
    if not values:
        raise ValueError("Укажите хотя бы одно поле для изменения.")
    return PurchasePatch(
        purchase_name=values.get("name") or values.get("purchase_name"),
        purchase_date=_parse_date(values["date"]) if "date" in values else None,
        amount=_parse_amount(values["amount"]) if "amount" in values else None,
        payer=values.get("payer"),
        participants=_parse_participant_value(values["participants"])
        if "participants" in values
        else None,
        category=values.get("category"),
        comment=values.get("comment"),
    )


def _parse_key_values(tokens: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for token in tokens:
        if "=" not in token:
            raise ValueError(f"Поле должно быть в формате key=value: {token}")
        key, value = token.split("=", 1)
        clean_key = key.strip().casefold()
        if clean_key in {"название", "имя"}:
            clean_key = "name"
        values[clean_key] = value.strip()
    return values


def _parse_participant_value(value: str) -> list[str]:
    participants = [item.strip() for item in value.replace(";", ",").split(",") if item.strip()]
    if not participants:
        raise ValueError("Список участников не должен быть пустым.")
    return participants


def _optional_value(value: str) -> str | None:
    stripped = value.strip()
    if not stripped or stripped in {"-", "—"}:
        return None
    return stripped


def _parse_amount(value: str) -> Decimal:
    try:
        amount = Decimal(value.replace(",", ".").strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError("Не понял сумму. Введите число, например 1250 или 1250.50.") from exc
    if amount <= 0:
        raise ValueError("Сумма должна быть больше нуля.")
    return amount


def _parse_date_or_today(value: str) -> date:
    if _optional_value(value) is None:
        return date.today()
    return _parse_date(value)


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError("Дата должна быть в формате YYYY-MM-DD.") from exc


def _find_purchase(purchases: list[Purchase], purchase_id: str) -> Purchase | None:
    return next((purchase for purchase in purchases if purchase.id == purchase_id), None)
