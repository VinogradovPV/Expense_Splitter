from expense_splitter.ui_labels import (
    label_for_period_filter,
    label_for_period_status,
    label_for_purchase_status,
    label_for_report_field,
    label_for_report_format,
    label_for_report_sheet,
    label_for_scope,
)


def test_scope_and_status_labels_are_russian():
    assert label_for_scope("open") == "Открытые покупки"
    assert label_for_scope("all") == "Все покупки с историей"
    assert label_for_period_status("closed") == "Закрыт"
    assert label_for_period_status("reopened") == "Переоткрыт"
    assert label_for_period_filter("with_purchases") == "Периоды с покупками"


def test_purchase_report_and_format_labels_are_russian():
    assert label_for_purchase_status("open") == "Открыта"
    assert label_for_purchase_status("settled", "Июнь") == "Закрыта: Июнь"
    assert label_for_report_field("Scope") == "Какие покупки включены"
    assert label_for_report_field("Snapshot") == "Дата формирования отчета"
    assert label_for_report_sheet("By Payer") == "По плательщикам"
    assert label_for_report_format("png") == "PNG-графики"
