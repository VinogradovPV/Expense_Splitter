from datetime import date
from decimal import Decimal

import pytest

from expense_splitter.gui import actions
from expense_splitter.gui.state import GuiState
from expense_splitter.models import Purchase
from expense_splitter.storage import save_purchases


def test_gui_generates_current_state_report_and_resolves_fixed_paths(tmp_path):
    state = GuiState(
        data_dir=tmp_path / "data",
        reports_dir=tmp_path / "reports",
        analytics_dir=tmp_path / "reports" / "analytics",
        current_state_dir=tmp_path / "reports" / "current_state",
    )
    state.ensure_data_files()
    names = actions.participant_names(state)
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
            )
        ],
    )

    report_dir = actions.generate_current_state_report(state)

    assert report_dir.parent == state.current_state_dir
    assert actions.current_report_path(report_dir, "html").name == "current_state_dashboard.html"
    assert actions.current_report_path(report_dir, "xlsx").name == "current_state.xlsx"
    assert actions.current_report_path(report_dir, "markdown").name == "current_state_report.md"


def test_gui_current_report_path_handles_missing_files(tmp_path):
    report_dir = tmp_path / "missing"
    report_dir.mkdir()

    with pytest.raises(FileNotFoundError, match="Сначала создайте отчет текущих взаиморасчетов"):
        actions.current_report_path(report_dir, "html")

    with pytest.raises(FileNotFoundError, match="Сначала создайте отчет текущих взаиморасчетов"):
        actions.current_report_path(report_dir, "pdf")

    with pytest.raises(ValueError, match="Неизвестный тип"):
        actions.current_report_path(report_dir, "unknown")
