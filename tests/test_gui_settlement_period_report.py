from datetime import date, datetime
from decimal import Decimal

import pytest

from expense_splitter.gui import actions
from expense_splitter.gui.state import GuiState
from expense_splitter.models import Purchase, Settlement, SettlementPeriod
from expense_splitter.storage import save_purchases, save_settlement_periods


def make_state(tmp_path):
    state = GuiState(
        data_dir=tmp_path / "data",
        reports_dir=tmp_path / "reports",
        analytics_dir=tmp_path / "reports" / "analytics",
        current_state_dir=tmp_path / "reports" / "current_state",
    )
    state.ensure_data_files()
    return state


def test_gui_generates_settlement_period_report_and_resolves_fixed_paths(tmp_path):
    state = make_state(tmp_path)
    names = actions.participant_names(state)
    period_id = "settlement_2026_06_30_001"
    save_purchases(
        state.data_dir / "purchases.yaml",
        [
            Purchase(
                id="p1",
                date=date(2026, 6, 25),
                amount=Decimal("100.00"),
                payer=names[0],
                participants=names[:2],
                purchase_name="Lunch",
                category="Food",
                settled=True,
                settlement_period_id=period_id,
            )
        ],
    )
    save_settlement_periods(
        state.data_dir / "settlement_periods.yaml",
        [
            SettlementPeriod(
                id=period_id,
                name="June",
                status="closed",
                date_from=date(2026, 6, 1),
                date_to=date(2026, 6, 30),
                closed_at=datetime(2026, 6, 30, 20, 0, 0),
                purchase_ids=["p1"],
                total_amount=Decimal("100.00"),
                settlements=[Settlement(names[1], names[0], Decimal("50.00"))],
            )
        ],
    )

    report_dir = actions.generate_settlement_period_snapshot_report(state, period_id)

    assert report_dir.parent == state.reports_dir / "settlement_periods"
    assert (
        actions.settlement_period_report_path(report_dir, "html").name
        == "settlement_period_dashboard.html"
    )
    assert (
        actions.settlement_period_report_path(report_dir, "xlsx").name
        == "settlement_period.xlsx"
    )
    assert (
        actions.settlement_period_report_path(report_dir, "markdown").name
        == "settlement_period_report.md"
    )


def test_gui_settlement_period_report_path_handles_missing_files(tmp_path):
    report_dir = tmp_path / "missing"
    report_dir.mkdir()

    with pytest.raises(FileNotFoundError, match="Сначала создайте отчет периода"):
        actions.settlement_period_report_path(report_dir, "html")

    with pytest.raises(ValueError, match="Неизвестный тип"):
        actions.settlement_period_report_path(report_dir, "pdf")
