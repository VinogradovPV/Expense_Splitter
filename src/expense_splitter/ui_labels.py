from __future__ import annotations

SCOPE_LABELS = {
    "scope": "Какие покупки включены",
    "open": "Открытые покупки",
    "all": "Все покупки с историей",
}

SHORT_SCOPE_LABELS = {
    "open": "Открытые",
    "all": "Все",
}

PURCHASE_STATUS_LABELS = {
    "open": "Открыта",
    "settled": "Закрыта",
    "closed": "Закрыта",
}

PERIOD_STATUS_LABELS = {
    "open": "Открыт",
    "closed": "Закрыт",
    "reopened": "Переоткрыт",
}

PERIOD_FILTER_LABELS = {
    "all": "Все периоды",
    "closed": "Закрытые периоды",
    "reopened": "Переоткрытые периоды",
    "empty": "Пустые периоды",
    "with_purchases": "Периоды с покупками",
}

PURCHASE_FILTER_LABELS = {
    "all": "Все",
    "open": "Открытые",
    "settled": "Закрытые",
}

REPORT_FIELD_LABELS = {
    "Scope": "Какие покупки включены",
    "scope": "Какие покупки включены",
    "Snapshot": "Дата формирования отчета",
    "snapshot": "Дата формирования отчета",
    "generated_at": "Дата формирования отчета",
    "Total amount": "Общая сумма",
    "Purchase count": "Количество покупок",
    "Average purchase": "Средний чек",
    "Participants": "Количество участников",
    "Transfer count": "Итоговые переводы",
    "Payer": "Плательщик",
    "Amount": "Сумма",
    "Category": "Категория",
    "Participant": "Участник",
    "Paid": "Оплатил",
    "Share": "Доля",
    "Balance": "Баланс",
    "From": "От",
    "To": "Кому",
    "Settlement period ID": "ID периода взаиморасчетов",
    "Closed at": "Дата закрытия",
    "Reopened at": "Дата переоткрытия",
}

REPORT_SHEET_LABELS = {
    "Summary": "Сводка",
    "Purchases": "Покупки",
    "By Category": "По категориям",
    "By Payer": "По плательщикам",
    "By Participant": "Объем расходов на человека",
    "Balances": "Балансы участников",
    "Settlements": "Итоговые переводы",
    "Top Purchases": "Крупнейшие покупки",
    "Warnings": "Предупреждения",
    "Charts": "Графики",
    "Metadata": "Служебная информация",
}

REPORT_FORMAT_LABELS = {
    "markdown": "Markdown",
    "csv": "CSV",
    "png": "PNG-графики",
    "html": "HTML",
    "xlsx": "Excel XLSX",
    "pdf": "PDF",
    "all": "Все форматы",
}


def label_for_scope(value: str, *, short: bool = False) -> str:
    key = value.strip().casefold()
    labels = SHORT_SCOPE_LABELS if short else SCOPE_LABELS
    return labels.get(key, value)


def label_for_purchase_status(
    value: str,
    settlement_period_name: str | None = None,
) -> str:
    key = value.strip().casefold()
    if key == "open":
        return PURCHASE_STATUS_LABELS["open"]
    if key in {"settled", "closed"}:
        if settlement_period_name:
            return f"Закрыта: {settlement_period_name}"
        return "Закрыта"
    return PURCHASE_STATUS_LABELS.get(key, value)


def label_for_missing_purchase_period() -> str:
    return "Закрыта: период не найден"


def label_for_period_status(value: str) -> str:
    return PERIOD_STATUS_LABELS.get(value.strip().casefold(), value)


def label_for_period_filter(value: str) -> str:
    return PERIOD_FILTER_LABELS.get(value.strip().casefold(), value)


def label_for_purchase_filter(value: str) -> str:
    return PURCHASE_FILTER_LABELS.get(value.strip().casefold(), value)


def label_for_report_field(value: str) -> str:
    return REPORT_FIELD_LABELS.get(value, REPORT_FIELD_LABELS.get(value.strip().casefold(), value))


def label_for_report_sheet(value: str) -> str:
    return REPORT_SHEET_LABELS.get(value, value)


def label_for_report_format(value: str) -> str:
    return REPORT_FORMAT_LABELS.get(value.strip().casefold(), value)
