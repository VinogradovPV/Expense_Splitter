from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

MONEY_DECIMAL_PLACES = Decimal("0.01")

PDF_MONEY_HEADERS = frozenset(
    {
        "Сумма",
        "Оплачено",
        "Объем расходов на человека",
        "Итог: + получит, - должен",
        "Итог: + получит, − должен",
        "Итоговый баланс",
        "Баланс",
        "Доля расходов",
        "Доля",
        "Средний чек",
        "Общая сумма",
        "payer_total",
    }
)

PDF_PERCENT_HEADERS = frozenset({"Доля, %", "Доля оплат, %"})


def format_money_for_pdf(value: object, *, decimal_separator: str = ",") -> str:
    amount = _to_decimal(value)
    if amount is None:
        return "" if value is None else str(value)

    amount = amount.quantize(MONEY_DECIMAL_PLACES, rounding=ROUND_HALF_UP)
    if amount == 0:
        amount = abs(amount)
    result = f"{amount:,.2f}".replace(",", " ")
    return result.replace(".", decimal_separator)


def format_percent_for_pdf(value: object, *, decimal_separator: str = ",") -> str:
    amount = _to_decimal(value)
    if amount is None:
        return "" if value is None else str(value)

    amount = amount.quantize(MONEY_DECIMAL_PLACES, rounding=ROUND_HALF_UP)
    if amount == 0:
        amount = abs(amount)
    return f"{amount:.2f}".replace(".", decimal_separator)


def format_pdf_cell(value: object, header: str, *, is_header: bool = False) -> str:
    if is_header:
        return serialize_pdf_value(value)

    normalized_header = str(header).strip()
    if normalized_header in PDF_PERCENT_HEADERS:
        return format_percent_for_pdf(value)
    if normalized_header in PDF_MONEY_HEADERS:
        return format_money_for_pdf(value)
    return serialize_pdf_value(value)


def is_money_pdf_label(label: str) -> bool:
    normalized = str(label).strip().casefold()
    return any(
        marker in normalized
        for marker in ("сумма", "средний чек", "средняя покупка")
    )


def serialize_pdf_value(value: object) -> str:
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    return "" if value is None else str(value)


def _to_decimal(value: object) -> Decimal | None:
    raw = str(value).strip().replace(" ", "").replace(",", ".")
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return None
