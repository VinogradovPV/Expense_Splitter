from expense_splitter.report_tables import (
    BALANCE_EXPLANATION,
    BALANCE_RESULT_HEADER,
    chart_display_title,
    rows_for_visual_table,
    visual_table_note,
)


def test_purchase_visual_rows_hide_service_columns():
    rows = [
        ["ID", "Дата", "Покупка", "Сумма", "payer_total", "payer_rank"],
        ["p-1", "2026-06-30", "Кофе", "100.00", "500.00", "1"],
    ]

    assert rows_for_visual_table("purchases.csv", rows) == [
        ["Дата", "Покупка", "Сумма"],
        ["2026-06-30", "Кофе", "100.00"],
    ]


def test_non_purchase_visual_rows_are_unchanged():
    rows = [["ID", "Значение"], ["summary", "ok"]]

    assert rows_for_visual_table("summary.csv", rows) == rows


def test_visual_rows_rename_money_share_headers():
    assert rows_for_visual_table(
        "by_participant.csv",
        [["Участник", "Покупок", "Доля расходов"], ["Alice", "2", "50.00"]],
    ) == [["Участник", "Покупок", "Объем расходов на человека"], ["Alice", "2", "50.00"]]
    assert rows_for_visual_table(
        "balances.csv",
        [["Участник", "Оплачено", "Доля", "Баланс"], ["Alice", "100.00", "50.00", "50.00"]],
    ) == [
        ["Участник", "Оплачено", "Объем расходов на человека", BALANCE_RESULT_HEADER],
        ["Alice", "100.00", "50.00", "50.00"],
    ]


def test_empty_warnings_visual_rows_show_message():
    assert rows_for_visual_table("warnings.csv", [["Тип", "ID", "Сообщение"]]) == [
        ["Предупреждений нет."]
    ]


def test_participant_share_chart_has_user_facing_title():
    assert chart_display_title("participant_share.png") == "Объем расходов на человека"
    assert chart_display_title("spending_by_category.png") == "Расходы по категориям"
    assert chart_display_title("spending_by_payer.png") == "Расходы по плательщикам"
    assert chart_display_title("top_purchases.png") == "Крупнейшие покупки"
    assert chart_display_title("balances.png") == "Кто должен и кому должны"
    assert chart_display_title("period_trend.png") == "Динамика расходов за период"


def test_balance_table_has_user_facing_note():
    assert visual_table_note("balances.csv") == BALANCE_EXPLANATION
    assert visual_table_note("summary.csv") is None
