from expense_splitter.report_tables import chart_display_title, rows_for_visual_table


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


def test_participant_share_chart_has_user_facing_title():
    assert chart_display_title("participant_share.png") == "Объем расходов на человека"
    assert chart_display_title("spending_by_category.png") == "spending_by_category"
