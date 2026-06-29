from pathlib import Path

import pytest

from expense_splitter.current_report import build_current_report_dataset, generate_current_report
from expense_splitter.report_pdf import discover_cyrillic_font
from tests.test_current_report import sample_participants, sample_purchases


def require_pdf_font() -> None:
    if discover_cyrillic_font() is None:
        pytest.skip("No Cyrillic-capable PDF font available.")


def assert_pdf_created(path: Path) -> None:
    assert path.is_file()
    assert path.stat().st_size > 0


def test_current_report_format_pdf_creates_pdf(tmp_path):
    require_pdf_font()
    dataset = build_current_report_dataset(sample_participants(), sample_purchases(), scope="open")

    report_dir = generate_current_report(dataset, tmp_path, "pdf")

    assert_pdf_created(report_dir / "current_state.pdf")
    assert not (report_dir / "current_state_dashboard.html").exists()


def test_current_report_format_all_includes_pdf(tmp_path):
    require_pdf_font()
    dataset = build_current_report_dataset(sample_participants(), sample_purchases(), scope="open")

    report_dir = generate_current_report(dataset, tmp_path, "all")

    assert_pdf_created(report_dir / "current_state.pdf")
