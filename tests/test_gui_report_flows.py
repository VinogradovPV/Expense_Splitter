from datetime import date
from decimal import Decimal

import pytest

from expense_splitter.gui import actions
from expense_splitter.gui.state import GuiState
from expense_splitter.models import Purchase


def purchase(
    purchase_id: str,
    name: str,
    amount: str,
    category: str,
    payer: str,
    purchase_date: date,
    settled: bool = False,
):
    return Purchase(
        id=purchase_id,
        date=purchase_date,
        amount=Decimal(amount),
        payer=payer,
        participants=[payer],
        purchase_name=name,
        category=category,
        settled=settled,
        settlement_period_id="period-1" if settled else None,
    )


def test_purchase_filters_and_sorting_are_gui_independent():
    purchases = [
        purchase("1", "Кофе", "100", "кофе", "Павел", date(2026, 6, 2)),
        purchase("2", "Обед", "250", "еда", "Елена", date(2026, 6, 3), True),
        purchase("3", "Кофе зерно", "300", "кофе", "Сергей", date(2026, 5, 31)),
    ]

    filtered = actions.filter_and_sort_purchases(
        purchases,
        status="open",
        category="кофе",
        date_from="2026-06-01",
        date_to="2026-06-30",
        search="коф",
        sort_by="amount",
    )
    assert [item.id for item in filtered] == ["1"]
    assert [
        item.id
        for item in actions.filter_and_sort_purchases(
            purchases, status="all", sort_by="amount", descending=True
        )
    ] == ["3", "2", "1"]


def test_report_paths_and_missing_messages(tmp_path):
    report_dir = tmp_path / "2026-06"
    report_dir.mkdir()
    (report_dir / "analytics_dashboard.html").write_text("<html></html>", encoding="utf-8")
    (report_dir / "analytics_report.md").write_text("# Report", encoding="utf-8")
    (report_dir / "expense_analytics_2026-06.xlsx").write_bytes(b"xlsx")

    assert actions.report_path(report_dir, "html").name == "analytics_dashboard.html"
    assert actions.report_path(report_dir, "markdown").name == "analytics_report.md"
    assert actions.report_path(report_dir, "xlsx").suffix == ".xlsx"
    with pytest.raises(FileNotFoundError, match="Сначала создайте отчёт"):
        actions.report_path(tmp_path / "missing", "html")


def test_backup_preserves_all_yaml_files(tmp_path):
    state = GuiState(data_dir=tmp_path / "data", reports_dir=tmp_path / "reports")
    state.ensure_data_files()
    backup_dir = actions.create_data_backup(state)

    assert (backup_dir / "participants.yaml").is_file()
    assert (backup_dir / "purchases.yaml").is_file()
    assert (backup_dir / "settlement_periods.yaml").is_file()
    assert (backup_dir / "categories.yaml").is_file()
