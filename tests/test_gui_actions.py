from datetime import date, datetime
from decimal import Decimal

import pytest

from expense_splitter.gui import actions
from expense_splitter.gui.dialogs import (
    normalize_known_values,
    parse_comma_separated,
    purchase_input_from_purchase,
)
from expense_splitter.gui.state import GuiState
from expense_splitter.models import SettlementPeriod
from expense_splitter.storage import (
    load_categories,
    load_groups,
    load_participants,
    load_purchases,
    load_settlement_periods,
    save_purchases,
    save_settlement_periods,
)


def make_state(tmp_path):
    state = GuiState(data_dir=tmp_path / "data", reports_dir=tmp_path / "reports")
    state.ensure_data_files()
    return state


def test_manual_participant_parser_and_category_multi_select_values():
    assert parse_comma_separated("Павел, Сергей, павел, ") == ["Павел", "Сергей"]
    assert parse_comma_separated("кофе, еда") == ["кофе", "еда"]


def test_manual_participants_are_normalized_and_unknown_values_are_rejected():
    normalized, unknown = normalize_known_values(
        ["павел", "Сергей", "Новый"],
        ["Павел", "Сергей"],
    )

    assert normalized == ["Павел", "Сергей"]
    assert unknown == ["Новый"]


def test_add_and_edit_purchase_with_category(tmp_path):
    state = make_state(tmp_path)
    names = actions.participant_names(state)
    purchase = actions.add_purchase(
        state,
        "Кофе",
        "100",
        names[0],
        names[:2],
        date(2026, 6, 19).isoformat(),
        "кофе",
    )

    updated = actions.edit_purchase(
        state,
        purchase.id,
        "Кофе и еда",
        "150.50",
        names[1],
        names[:3],
        "2026-06-20",
        "кофе, еда",
        "исправлено",
    )

    assert updated.purchase_name == "Кофе и еда"
    assert updated.category == "кофе, еда"
    assert actions.purchase_row(updated)[5] == "кофе, еда"
    assert load_purchases(state.data_dir / "purchases.yaml") == [updated]

    initial = purchase_input_from_purchase(updated)
    assert initial.purchase_name == "Кофе и еда"
    assert initial.amount == "150.50"
    assert initial.payer == names[1]
    assert initial.participants == names[:3]
    assert initial.purchase_date == "2026-06-20"
    assert initial.category == "кофе, еда"
    assert initial.comment == "исправлено"


def test_purchase_row_shows_uncategorized_fallback(tmp_path):
    state = make_state(tmp_path)
    names = actions.participant_names(state)
    purchase = actions.add_purchase(state, "Вода", "50", names[0], names[:2], "2026-06-19")

    row = actions.purchase_row(purchase)

    assert row[1] == "Вода"
    assert row[5] == "Без категории"
    assert len(row) == 7


@pytest.mark.parametrize(
    ("settled", "period_id"),
    [(True, None), (False, "period-1")],
)
def test_edit_settled_purchase_is_blocked(tmp_path, settled, period_id):
    state = make_state(tmp_path)
    names = actions.participant_names(state)
    purchase = actions.add_purchase(state, "Кофе", "100", names[0], names[:2], "2026-06-19")
    stored = load_purchases(state.data_dir / "purchases.yaml")
    stored[0].settled = settled
    stored[0].settlement_period_id = period_id
    save_purchases(state.data_dir / "purchases.yaml", stored)

    with pytest.raises(ValueError, match="закрытому периоду"):
        actions.edit_purchase(
            state,
            purchase.id,
            "Другое",
            "120",
            names[0],
            names[:2],
            "2026-06-19",
        )
    assert load_purchases(state.data_dir / "purchases.yaml") == stored


def test_edit_purchase_validation_does_not_replace_original(tmp_path):
    state = make_state(tmp_path)
    names = actions.participant_names(state)
    purchase = actions.add_purchase(state, "Кофе", "100", names[0], names[:2], "2026-06-19")

    with pytest.raises(ValueError, match="Участники не найдены"):
        actions.edit_purchase(
            state,
            purchase.id,
            "Ошибка",
            "120",
            names[0],
            ["Неизвестный"],
            "2026-06-20",
        )

    assert load_purchases(state.data_dir / "purchases.yaml") == [purchase]


def test_delete_open_purchase_requires_typed_confirmation_and_creates_backup(tmp_path):
    state = make_state(tmp_path)
    names = actions.participant_names(state)
    purchase = actions.add_purchase(state, "Ошибка ввода", "100", names[0], names[:2], "2026-06-19")
    with pytest.raises(ValueError, match="DELETE_PURCHASE"):
        actions.delete_purchase(state, purchase.id, "delete")

    deleted = actions.delete_purchase(state, purchase.id, "DELETE_PURCHASE")

    assert deleted.id == purchase.id
    assert load_purchases(state.data_dir / "purchases.yaml") == []
    assert list(state.data_dir.glob("purchases.yaml.*.bak"))


def test_delete_settled_purchase_is_blocked(tmp_path):
    state = make_state(tmp_path)
    names = actions.participant_names(state)
    purchase = actions.add_purchase(state, "Закрытая", "100", names[0], names[:2], "2026-06-19")
    stored = load_purchases(state.data_dir / "purchases.yaml")
    stored[0].settled = True
    stored[0].settlement_period_id = "period-1"
    save_purchases(state.data_dir / "purchases.yaml", stored)

    with pytest.raises(ValueError, match="Закрытую покупку"):
        actions.delete_purchase(state, purchase.id, "DELETE_PURCHASE")


def test_custom_category_and_reset_preserve_reference_data(tmp_path):
    state = make_state(tmp_path)
    actions.add_category(state, "офис")
    names = actions.participant_names(state)
    purchase = actions.add_purchase(
        state, "Бумага", "200", names[0], names[:2], "2026-06-19", "офис"
    )
    period = actions.close_period(state, "2026-06-19", "2026-06-19", "Тестовый период")

    participants_before = load_participants(state.data_dir / "participants.yaml")
    groups_before = load_groups(state.data_dir / "participants.yaml")
    categories_before = load_categories(state.data_dir / "categories.yaml")
    result = actions.reset_test_data(state, "RESET_TEST_DATA")

    assert len(result.backup_paths) == 2
    assert all(path.exists() for path in result.backup_paths)
    backed_up_purchases = load_purchases(result.backup_paths[0])
    backed_up_periods = load_settlement_periods(result.backup_paths[1])
    assert [item.id for item in backed_up_purchases] == [purchase.id]
    assert backed_up_purchases[0].settled is True
    assert [item.id for item in backed_up_periods] == [period.id]
    assert load_purchases(state.data_dir / "purchases.yaml") == []
    assert load_settlement_periods(state.data_dir / "settlement_periods.yaml") == []
    assert load_participants(state.data_dir / "participants.yaml") == participants_before
    assert load_groups(state.data_dir / "participants.yaml") == groups_before
    assert load_categories(state.data_dir / "categories.yaml") == categories_before


def test_reset_requires_exact_typed_confirmation(tmp_path):
    state = make_state(tmp_path)
    with pytest.raises(ValueError, match="RESET_TEST_DATA"):
        actions.reset_test_data(state, "reset")


def test_directory_actions_manage_participants_and_hide_archived_from_new_purchases(tmp_path):
    state = make_state(tmp_path)

    actions.add_participant(state, "Alice")
    actions.archive_participant(state, "Alice")

    assert "Alice" not in actions.participant_names(state)
    assert "Alice" in actions.all_participant_names(state)
    rows = actions.participant_directory_rows(state, include_archived=True)
    assert any(row.name == "Alice" and row.status == "archived" for row in rows)


def test_directory_actions_rename_category_and_update_purchase_filters(tmp_path):
    state = make_state(tmp_path)
    actions.add_category(state, "Food")
    names = actions.participant_names(state)
    purchase = actions.add_purchase(
        state,
        "Lunch",
        "100",
        names[0],
        names[:2],
        "2026-06-25",
        "Food",
    )

    actions.rename_category(state, "Food", "Meals")

    assert "Meals" in actions.category_names(state)
    assert "Food" not in actions.category_names(state)
    assert load_purchases(state.data_dir / "purchases.yaml")[0].category == "Meals"
    rows = actions.category_directory_rows(state)
    assert any(row.name == "Meals" and row.total_count == 1 for row in rows)
    assert purchase.id == load_purchases(state.data_dir / "purchases.yaml")[0].id


def test_settlement_period_ux_actions_suggest_edit_and_delete_empty(tmp_path):
    state = make_state(tmp_path)
    names = actions.participant_names(state)
    actions.add_purchase(state, "Lunch", "100", names[0], names[:2], "2026-06-25")
    empty_period = SettlementPeriod(
        id="empty",
        name="Empty",
        status="closed",
        date_from=date(2026, 6, 1),
        date_to=date(2026, 6, 1),
        closed_at=datetime(2026, 6, 1, 12, 0, 0),
        purchase_ids=[],
        total_amount=Decimal("0.00"),
        settlements=[],
    )
    save_settlement_periods(state.data_dir / "settlement_periods.yaml", [empty_period])

    suggestion = actions.suggest_close_period(state)

    assert suggestion.date_from == date(2026, 6, 25)
    assert suggestion.reason == "first_open_purchase_date"
    updated = actions.edit_period_metadata(
        state,
        "empty",
        "Empty renamed",
        "technical",
        "2026-06-02",
        "2026-06-03",
    )
    assert updated.name == "Empty renamed"
    assert updated.date_from == date(2026, 6, 2)
    assert list(state.data_dir.glob("settlement_periods.yaml.*.bak"))

    with pytest.raises(ValueError, match=actions.DELETE_EMPTY_PERIOD_CONFIRM):
        actions.delete_empty_period(state, "empty", "delete")

    deleted = actions.delete_empty_period(state, "empty", actions.DELETE_EMPTY_PERIOD_CONFIRM)

    assert deleted.id == "empty"
    assert load_settlement_periods(state.data_dir / "settlement_periods.yaml") == []
