from types import SimpleNamespace

import expense_splitter.analytics_charts as analytics_charts
import expense_splitter.current_report as current_report
from expense_splitter.report_pdf import _compact_purchase_rows
from expense_splitter.report_tables import (
    PURCHASE_LABEL_MAX_LENGTH,
    compact_participant_list,
    full_participant_list,
    truncate_display_label,
)


def test_compact_purchase_table_keeps_all_real_participant_names():
    rows = [
        ["Дата", "Покупка", "Категория", "Сумма", "Плательщик", "Участники"],
        [
            "2026-08-01",
            "Арбуз Астрахань",
            "Еда",
            "1200.00",
            "Павел",
            "Павел, Сергей, Владимир, Елена, Эмилия, Мария, Максим",
        ],
    ]

    compact = _compact_purchase_rows(rows)

    assert compact[1][1] == "Арбуз Астрахань"
    assert compact[1][4] == "Павел"
    assert compact[1][5] == "Павел, Сергей, Владимир, Елена, Эмилия, Мария, Максим"
    assert "и еще" not in compact[1][5]


def test_long_label_truncation_preserves_source_prefix():
    label = "Очень длинное название покупки с деталями и пояснениями"

    compact = truncate_display_label(label, PURCHASE_LABEL_MAX_LENGTH, "н/д")

    assert compact.startswith("Очень длинное название")
    assert compact.endswith("…")
    assert len(compact) <= PURCHASE_LABEL_MAX_LENGTH
    assert compact_participant_list("") == "Без имени"
    assert full_participant_list("Павел, Сергей, Владимир, Максим, Елена") == (
        "Павел, Сергей, Владимир, Максим, Елена"
    )


def test_current_top_purchases_chart_uses_real_or_truncated_purchase_names(
    tmp_path,
    monkeypatch,
):
    captured = {}
    long_name = "Очень длинное название покупки с деталями и пояснениями"
    dataset = SimpleNamespace(
        top_purchases=[
            {"purchase_name": "Арбуз Астрахань", "amount": 1200, "rank": 1},
            {"purchase_name": long_name, "amount": 900, "rank": 2},
        ]
    )

    def fake_save_barh(path, labels, values, colors, title, xlabel, **kwargs):
        captured["labels"] = labels

    monkeypatch.setattr(current_report, "_save_barh", fake_save_barh)

    current_report._chart_top_purchases(dataset, tmp_path / "top_purchases.png")

    assert captured["labels"][0] == "Арбуз Астрахань"
    assert captured["labels"][1].startswith("Очень длинное название")
    assert captured["labels"][1].endswith("…")


def test_analytics_participant_chart_keeps_real_names(tmp_path, monkeypatch):
    captured = {}
    dataset = SimpleNamespace(
        by_participant=[
            {"participant": "Павел", "total_share": 100},
            {"participant": "Сергей", "total_share": 90},
            {"participant": "Владимир", "total_share": 80},
        ]
    )

    def fake_save_barh(path, labels, values, colors, title, xlabel, **kwargs):
        captured["labels"] = labels

    monkeypatch.setattr(analytics_charts, "_save_barh", fake_save_barh)

    analytics_charts._participant_share(dataset, tmp_path / "participant_share.png")

    assert captured["labels"] == ["Павел", "Сергей", "Владимир"]
