from expense_splitter.defaults import DEFAULT_CATEGORIES, DEFAULT_GROUPS, DEFAULT_PARTICIPANTS
from expense_splitter.storage import initialize_data_files, load_categories, save_categories


def test_initialize_creates_default_categories(tmp_path):
    data_dir = tmp_path / "data"
    initialize_data_files(data_dir, DEFAULT_PARTICIPANTS, DEFAULT_GROUPS)

    assert load_categories(data_dir / "categories.yaml") == DEFAULT_CATEGORIES


def test_custom_category_is_normalized_and_persisted(tmp_path):
    path = tmp_path / "categories.yaml"
    save_categories(path, ["кофе", "  Новая  ", "новая", ""])

    assert load_categories(path) == ["кофе", "Новая"]
