from datetime import date, datetime
from decimal import Decimal

from expense_splitter.gui import actions
from expense_splitter.gui.app import (
    PERIOD_FILTER_VALUES,
    PURCHASE_FILTER_VALUES,
    REPORT_FORMAT_VALUES,
)
from expense_splitter.models import Purchase, SettlementPeriod
from expense_splitter.ui_labels import (
    label_for_period_filter,
    label_for_purchase_filter,
    label_for_report_format,
)


def test_gui_filter_values_are_user_facing_russian_labels():
    period_labels = [label_for_period_filter(value) for value in PERIOD_FILTER_VALUES]
    purchase_labels = [label_for_purchase_filter(value) for value in PURCHASE_FILTER_VALUES]
    format_labels = [label_for_report_format(value) for value in REPORT_FORMAT_VALUES]

    assert period_labels == [
        "Все периоды",
        "Закрытые периоды",
        "Переоткрытые периоды",
        "Пустые периоды",
        "Периоды с покупками",
    ]
    assert purchase_labels == ["Все", "Открытые", "Закрытые"]
    assert format_labels[-1] == "Все форматы"


def test_purchase_status_labels_hide_raw_settlement_period_id():
    period = SettlementPeriod(
        id="settlement_2026_06_30_001",
        name="Период до 2026-06-30",
        status="closed",
        date_from=date(2026, 6, 1),
        date_to=date(2026, 6, 30),
        closed_at=datetime(2026, 6, 30, 20, 0, 0),
        purchase_ids=["p2"],
        total_amount=Decimal("200"),
    )
    open_purchase = Purchase(
        id="p1",
        date=date(2026, 6, 10),
        amount=Decimal("100"),
        payer="Алиса",
        participants=["Алиса"],
        purchase_name="Обед",
    )
    closed_purchase = Purchase(
        id="p2",
        date=date(2026, 6, 11),
        amount=Decimal("200"),
        payer="Боб",
        participants=["Алиса", "Боб"],
        purchase_name="Такси",
        settled=True,
        settlement_period_id=period.id,
    )

    assert actions.purchase_row(open_purchase)[-1] == "Открыта"
    assert actions.purchase_row(closed_purchase, {period.id: period.name})[-1] == (
        "Закрыта: Период до 2026-06-30"
    )
    assert actions.purchase_row(closed_purchase, {})[-1] == "Закрыта: период не найден"
    closed_status = actions.purchase_row(closed_purchase, {period.id: period.name})[-1]
    assert "settlement_2026" not in closed_status
