from datetime import date
from decimal import Decimal

import pytest

from expense_splitter.defaults import DEFAULT_CATEGORIES, DEFAULT_GROUPS, DEFAULT_PARTICIPANTS
from expense_splitter.directories import (
    DELETE_CATEGORY_USAGE_CONFIRM,
    add_category,
    archive_category,
    delete_category,
    list_category_rows,
    rename_category,
)
from expense_splitter.models import CategoryEntry, Purchase
from expense_splitter.storage import (
    initialize_data_files,
    load_categories,
    load_category_entries,
    load_purchases,
    save_categories,
    save_category_entries,
    save_purchases,
)


def test_initialize_creates_default_categories(tmp_path):
    data_dir = tmp_path / "data"
    initialize_data_files(data_dir, DEFAULT_PARTICIPANTS, DEFAULT_GROUPS)

    assert load_categories(data_dir / "categories.yaml") == DEFAULT_CATEGORIES


def test_custom_category_is_normalized_and_persisted(tmp_path):
    path = tmp_path / "categories.yaml"
    save_categories(path, ["кофе", "  Новая  ", "новая", ""])

    assert load_categories(path) == ["кофе", "Новая"]


def test_category_entries_are_backward_compatible_and_archive_hides_active_list(tmp_path):
    path = tmp_path / "categories.yaml"
    save_category_entries(
        path,
        [
            CategoryEntry("Food"),
            CategoryEntry("Travel", status="archived"),
        ],
    )

    assert load_categories(path) == ["Food"]
    assert load_categories(path, include_archived=True) == ["Food", "Travel"]
    assert load_category_entries(path)[1].status == "archived"


def test_add_category_rejects_duplicate_and_blank_names(tmp_path):
    data_dir = tmp_path / "data"
    initialize_data_files(data_dir, [], [])

    add_category(data_dir, " Food ")

    assert load_categories(data_dir / "categories.yaml")[-1] == "Food"
    with pytest.raises(ValueError, match="уже существует"):
        add_category(data_dir, "food")
    with pytest.raises(ValueError, match="не может быть пустым"):
        add_category(data_dir, "")


def test_rename_category_updates_comma_separated_purchase_categories(tmp_path):
    data_dir = tmp_path / "data"
    initialize_data_files(data_dir, [], [])
    save_categories(data_dir / "categories.yaml", ["Food", "Coffee", "Transport"])
    save_purchases(
        data_dir / "purchases.yaml",
        [
            Purchase(
                id="p1",
                date=date(2026, 6, 25),
                amount=Decimal("100.00"),
                payer="Alice",
                participants=["Alice"],
                purchase_name="Lunch",
                category="Food, Coffee",
            )
        ],
    )

    rename_category(data_dir, "Food", "Meals")

    assert load_categories(data_dir / "categories.yaml") == ["Meals", "Coffee", "Transport"]
    assert load_purchases(data_dir / "purchases.yaml")[0].category == "Meals, Coffee"
    assert list(data_dir.glob("categories.yaml.*.bak"))
    assert list(data_dir.glob("purchases.yaml.*.bak"))


def test_delete_used_category_requires_typed_confirm_and_clears_purchase_usage(tmp_path):
    data_dir = tmp_path / "data"
    initialize_data_files(data_dir, [], [])
    save_categories(data_dir / "categories.yaml", ["Food", "Coffee"])
    save_purchases(
        data_dir / "purchases.yaml",
        [
            Purchase(
                id="p1",
                date=None,
                amount=Decimal("50.00"),
                payer="Alice",
                participants=["Alice"],
                purchase_name="Coffee",
                category="Food, Coffee",
            )
        ],
    )

    with pytest.raises(ValueError, match=DELETE_CATEGORY_USAGE_CONFIRM):
        delete_category(data_dir, "Food")

    delete_category(data_dir, "Food", DELETE_CATEGORY_USAGE_CONFIRM)

    assert load_categories(data_dir / "categories.yaml") == ["Coffee"]
    assert load_purchases(data_dir / "purchases.yaml")[0].category == "Coffee"


def test_archive_category_hides_from_active_list_but_directory_can_show_it(tmp_path):
    data_dir = tmp_path / "data"
    initialize_data_files(data_dir, [], [])
    save_categories(data_dir / "categories.yaml", ["Food", "Coffee"])

    archive_category(data_dir, "Coffee")

    assert load_categories(data_dir / "categories.yaml") == ["Food"]
    rows = list_category_rows(data_dir, include_archived=True)
    assert [(row.name, row.status) for row in rows] == [
        ("Food", "active"),
        ("Coffee", "archived"),
    ]
