from datetime import date
from decimal import Decimal

import pytest

from expense_splitter.gui import actions
from expense_splitter.gui.app import ExpenseSplitterGui, build_parser, main
from expense_splitter.gui.dialogs import SETTLEMENT_WARNING
from expense_splitter.gui.state import GuiState
from expense_splitter.storage import load_purchases


def test_gui_modules_import_without_starting_event_loop():
    assert ExpenseSplitterGui is not None
    assert "Покупки не будут удалены" in SETTLEMENT_WARNING


def test_gui_help_exits_without_tk_event_loop(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])

    assert exc.value.code == 0
    assert "Desktop GUI launcher" in capsys.readouterr().out


def test_gui_parser_accepts_data_and_reports_dirs():
    args = build_parser().parse_args(["--data-dir", "custom-data", "--reports-dir", "out"])

    assert args.data_dir == "custom-data"
    assert args.reports_dir == "out"


def test_gui_actions_add_purchase_and_close_period_without_deleting_history(tmp_path):
    state = GuiState(data_dir=tmp_path / "data", reports_dir=tmp_path / "reports")
    state.ensure_data_files()
    names = actions.participant_names(state)

    purchase = actions.add_purchase(
        state,
        purchase_name="Coffee",
        amount="120.00",
        payer=names[0],
        participants=names[:2],
        purchase_date=date(2026, 6, 19).isoformat(),
    )
    assert purchase.amount == Decimal("120.00")

    preview = actions.preview_close_period(state, "2026-06-01", "2026-06-19")
    assert preview.purchase_count == 1
    assert preview.total_amount == Decimal("120.00")

    period = actions.close_period(state, "2026-06-01", "2026-06-19", "GUI smoke")
    purchases = load_purchases(state.data_dir / "purchases.yaml")

    assert period.id.startswith("settlement_2026_06_19_")
    assert len(purchases) == 1
    assert purchases[0].settled is True
    assert purchases[0].settlement_period_id == period.id
    assert all(balance.net == Decimal("0.00") for balance in actions.current_balances(state))
