from pathlib import Path

import pytest

from expense_splitter.report_pdf import discover_cyrillic_font
from expense_splitter.settlement_period_report import (
    build_settlement_period_report_dataset,
    generate_settlement_period_report,
)
from tests.test_settlement_period_report import (
    sample_participants,
    sample_period,
    sample_purchases,
)


def require_pdf_font() -> None:
    if discover_cyrillic_font() is None:
        pytest.skip("No Cyrillic-capable PDF font available.")


def assert_pdf_created(path: Path) -> None:
    assert path.is_file()
    assert path.stat().st_size > 0


def test_settlement_period_report_format_pdf_creates_pdf(tmp_path):
    require_pdf_font()
    dataset = build_settlement_period_report_dataset(
        [sample_period()],
        sample_purchases(),
        sample_participants(),
        "settlement_2026_06_30_001",
    )

    report_dir = generate_settlement_period_report(dataset, tmp_path, "pdf")

    assert_pdf_created(report_dir / "settlement_period.pdf")
    assert not (report_dir / "settlement_period_dashboard.html").exists()


def test_settlement_period_report_format_all_includes_pdf(tmp_path):
    require_pdf_font()
    dataset = build_settlement_period_report_dataset(
        [sample_period()],
        sample_purchases(),
        sample_participants(),
        "settlement_2026_06_30_001",
    )

    report_dir = generate_settlement_period_report(dataset, tmp_path, "all")

    assert_pdf_created(report_dir / "settlement_period.pdf")
