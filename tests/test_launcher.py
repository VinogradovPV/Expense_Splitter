# import pytest (removed unused)


def test_launcher_import():
    import importlib.util
    spec = importlib.util.find_spec("expense_splitter.launcher")
    assert spec is not None, "Failed to find expense_splitter.launcher"

def test_launcher_main_exists():
    import expense_splitter.launcher
    assert hasattr(expense_splitter.launcher, "main")
    assert callable(expense_splitter.launcher.main)

def test_launcher_help_does_not_start_menu(monkeypatch, capsys):
    import expense_splitter.launcher

    monkeypatch.setattr("sys.argv", ["expense-splitter-launcher", "--help"])

    expense_splitter.launcher.main()

    output = capsys.readouterr().out
    assert "Usage: expense-splitter-launcher" in output
    assert "Interactive launcher" in output

def test_launcher_entry_point():
    from pathlib import Path

    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"

    # We will just read it as text to avoid adding tomli dependency
    content = pyproject_path.read_text(encoding="utf-8")
    assert "expense-splitter-launcher" in content
    assert "expense_splitter.launcher:main" in content


def test_launcher_blank_purchase_name_defaults_to_not_available(tmp_path, monkeypatch):
    from expense_splitter.models import Participant
    from expense_splitter.storage import load_purchases, save_participants
    import expense_splitter.launcher as launcher

    data_dir = tmp_path / "data"
    save_participants(data_dir / "participants.yaml", [Participant(name="Alice")])
    monkeypatch.setattr(launcher, "DATA_DIR", data_dir)
    monkeypatch.setattr(launcher, "get_participant_names", lambda: ["Alice"])
    monkeypatch.setattr(launcher, "get_group_names", lambda: [])

    answers = iter(["   ", "10.00", "Alice", "Alice", "2026-06-18", "", ""])
    monkeypatch.setattr(launcher.Prompt, "ask", lambda *args, **kwargs: next(answers))

    launcher.add_purchase_interactive()

    purchases = load_purchases(data_dir / "purchases.yaml")
    assert purchases[0].purchase_name == "н/д"
