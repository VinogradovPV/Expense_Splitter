from pathlib import Path

import pytest

from expense_splitter.analytics_reporting import generate_analytics_report
from expense_splitter.report_pdf import discover_cyrillic_font
from tests.test_analytics_reporting import sample_dataset


def require_pdf_font() -> None:
    if discover_cyrillic_font() is None:
        pytest.skip("No Cyrillic-capable PDF font available.")


def assert_pdf_created(path: Path) -> None:
    assert path.is_file()
    assert path.stat().st_size > 0


def test_analytics_format_pdf_creates_pdf(tmp_path):
    require_pdf_font()

    report_dir = generate_analytics_report(sample_dataset(), tmp_path, "pdf")

    assert_pdf_created(report_dir / "expense_analytics_2026-06.pdf")
    assert not (report_dir / "analytics_dashboard.html").exists()


def test_analytics_format_all_includes_pdf(tmp_path):
    require_pdf_font()

    report_dir = generate_analytics_report(sample_dataset(), tmp_path, "all")

    assert_pdf_created(report_dir / "expense_analytics_2026-06.pdf")
