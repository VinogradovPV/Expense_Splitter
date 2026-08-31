"""User-facing Telegram bot messages."""

from __future__ import annotations

from decimal import Decimal

from expense_splitter.models import Purchase, SettlementPeriod
from expense_splitter.reports.result import ReportFile, ReportResult
from expense_splitter.services import DELETE_PURCHASE_CONFIRM
from expense_splitter.telegram_bot.states import PurchaseDraft

CLOSE_PERIOD_CONFIRM = "CLOSE_PERIOD"

START_MESSAGE = (
    "Привет! Я помогу добавить покупки и получить отчеты Expense Splitter.\n"
    "Данные меняются только через серверный service layer."
)

HELP_MESSAGE = "\n".join(
    [
        "Команды:",
        "/add_purchase - добавить покупку",
        "/purchases - показать открытые покупки",
        "/edit_purchase <id> amount=1250 category=еда - исправить открытую покупку",
        f"/delete_purchase <id> {DELETE_PURCHASE_CONFIRM} - удалить открытую покупку",
        "/close_period from=2026-07-01 to=2026-07-31 "
        f"name=Июль confirm={CLOSE_PERIOD_CONFIRM} - закрыть период",
        "/current_pdf - текущие взаиморасчеты PDF",
        "/current_xlsx - текущие взаиморасчеты XLSX",
        "/analytics month 2026 7 pdf - аналитический отчет",
        "/periods - список периодов взаиморасчетов",
        "/period_report <id> pdf - отчет по периоду",
        "/cancel - отменить текущий диалог",
    ]
)

CANCEL_MESSAGE = "Действие отменено."
UNKNOWN_COMMAND_MESSAGE = "Команда не распознана. Введите /help."
GENERIC_ERROR_MESSAGE = (
    "Не удалось выполнить действие. Проверьте данные и попробуйте еще раз."
)


def prompt_purchase_name() -> str:
    return "Введите название покупки или '-' для значения н/д."


def prompt_amount() -> str:
    return "Введите сумму, например 1250 или 1250.50."


def prompt_payer(default_payer: str | None) -> str:
    if default_payer:
        return f"Введите плательщика или '-' для {default_payer}."
    return "Введите плательщика."


def prompt_participants() -> str:
    return "Введите участников через запятую или 'all' для всех активных участников."


def prompt_category() -> str:
    return "Введите категорию или '-' без категории."


def prompt_date() -> str:
    return "Введите дату YYYY-MM-DD или '-' для сегодняшней даты."


def prompt_comment() -> str:
    return "Введите комментарий или '-' без комментария."


def purchase_preview(draft: PurchaseDraft) -> str:
    return "\n".join(
        [
            "Проверьте покупку:",
            f"{draft.purchase_name or 'н/д'} - {_money(draft.amount)}",
            f"Плательщик: {draft.payer or 'н/д'}",
            f"Участники: {', '.join(draft.participants) or 'н/д'}",
            f"Категория: {draft.category or 'без категории'}",
            f"Дата: {draft.purchase_date or 'сегодня'}",
            f"Комментарий: {draft.comment or '-'}",
            "",
            "Сохранить? Ответьте yes или no.",
        ]
    )


def purchase_saved(purchase: Purchase) -> str:
    return f"Покупка добавлена: {purchase.id} - {purchase.purchase_name}."


def purchase_updated(purchase: Purchase) -> str:
    return f"Покупка обновлена: {purchase.id} - {purchase.purchase_name}."


def purchase_delete_preview(purchase_id: str) -> str:
    return (
        "Удаление открытой покупки требует подтверждения.\n"
        f"Введите: /delete_purchase {purchase_id} {DELETE_PURCHASE_CONFIRM}"
    )


def purchase_deleted(purchase: Purchase) -> str:
    return f"Покупка удалена: {purchase.id} - {purchase.purchase_name}."


def close_period_confirm_hint() -> str:
    return (
        "Закрытие периода изменит статус открытых покупок и сохранит snapshot.\n"
        "Повторите команду с точным маркером: confirm=CLOSE_PERIOD"
    )


def period_closed(period: SettlementPeriod) -> str:
    return (
        f"Период закрыт: {period.id} - {period.name}. "
        f"Покупок: {len(period.purchase_ids)}, сумма {_money(period.total_amount)}."
    )


def purchase_list(purchases: list[Purchase]) -> str:
    open_purchases = [purchase for purchase in purchases if not purchase.settled]
    if not open_purchases:
        return "Открытых покупок нет."
    rows = ["Открытые покупки:"]
    rows.extend(_purchase_row(purchase) for purchase in open_purchases[:20])
    if len(open_purchases) > 20:
        rows.append(f"...и еще {len(open_purchases) - 20}")
    return "\n".join(rows)


def report_ready(result: ReportResult) -> str:
    files = ", ".join(file.filename for file in result.files) or "нет файлов"
    return f"{result.telegram_caption}\nГотово: {files}"


def no_report_file(format_name: str) -> str:
    return f"Отчет создан, но файл формата {format_name} не найден."


def periods_list(periods: list[SettlementPeriod]) -> str:
    if not periods:
        return "Периодов взаиморасчетов пока нет."
    rows = ["Периоды взаиморасчетов:"]
    for period in sorted(periods, key=lambda item: item.closed_at, reverse=True)[:20]:
        rows.append(
            f"{period.id}: {period.name} ({period.status}), "
            f"{period.date_from} - {period.date_to}, сумма {_money(period.total_amount)}"
        )
    return "\n".join(rows)


def _purchase_row(purchase: Purchase) -> str:
    participants = ", ".join(purchase.participants)
    return (
        f"{purchase.id}: {purchase.date or '-'} | {purchase.purchase_name} | "
        f"{_money(purchase.amount)} | {purchase.payer} -> {participants}"
    )


def _money(value: Decimal | None) -> str:
    if value is None:
        return "0.00"
    return f"{value:.2f}"


def file_caption(file: ReportFile, result: ReportResult) -> str:
    return f"{result.telegram_caption}\nФайл: {file.filename}"
