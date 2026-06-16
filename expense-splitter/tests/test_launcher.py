# import pytest (removed unused)


def test_launcher_import():
    import importlib.util
    spec = importlib.util.find_spec("expense_splitter.launcher")
    assert spec is not None, "Failed to find expense_splitter.launcher"

def test_launcher_main_exists():
    import expense_splitter.launcher
    assert hasattr(expense_splitter.launcher, "main")
    assert callable(expense_splitter.launcher.main)

def test_launcher_entry_point():
    from pathlib import Path

    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"

    # We will just read it as text to avoid adding tomli dependency
    content = pyproject_path.read_text(encoding="utf-8")
    assert "expense-splitter-launcher" in content
    assert "expense_splitter.launcher:main" in content
