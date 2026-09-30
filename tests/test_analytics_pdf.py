from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from expense_splitter.analytics import build_analytics_dataset, parse_period
from expense_splitter.analytics_reporting import generate_analytics_report
from expense_splitter.models import Participant, Purchase
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


def test_analytics_pdf_shows_single_day_warning_without_period_trend(tmp_path):
    require_pdf_font()
    pypdf = pytest.importorskip("pypdf")

    report_dir = generate_analytics_report(sample_dataset(), tmp_path, "pdf")
    pdf_path = report_dir / "expense_analytics_2026-06.pdf"
    reader = pypdf.PdfReader(str(pdf_path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    assert "Недостаточно дат для построения динамики расходов." in text
    assert "Динамика расходов за период" not in text
    assert "period_trend" not in text


def test_analytics_format_all_includes_pdf(tmp_path):
    require_pdf_font()

    report_dir = generate_analytics_report(sample_dataset(), tmp_path, "all")

    assert_pdf_created(report_dir / "expense_analytics_2026-06.pdf")


def test_analytics_pdf_moves_full_purchase_list_to_appendix(tmp_path):
    require_pdf_font()
    pypdf = pytest.importorskip("pypdf")
    participant_names = ["Павел", "Сергей", "Владимир", "Елена", "Эмилия", "Мария", "Максим"]
    participants = [Participant(name) for name in participant_names]
    purchases = [
        Purchase(
            id=f"p-{index:02d}",
            date=date(2026, 1, 1) + timedelta(days=index % 180),
            amount=Decimal(index * 10),
            payer=participants[index % 7].name,
            participants=[participant.name for participant in participants],
            purchase_name=f"Арбуз Астрахань - партия {index:02d}",
            category=f"Категория {index % 4}",
        )
        for index in range(1, 64)
    ]
    dataset = build_analytics_dataset(
        participants,
        [],
        purchases,
        parse_period("year", 2026),
    )

    report_dir = generate_analytics_report(dataset, tmp_path, "pdf")
    pdf_path = report_dir / "expense_analytics_2026.pdf"
    reader = pypdf.PdfReader(str(pdf_path))
    page_texts = [(page.extract_text() or "").strip() for page in reader.pages]
    text = "\n".join(page_texts)

    assert "Приложение: все покупки" in text
    assert "Арбуз Астрахань - партия 63" in text
    assert all(name in text for name in participant_names)
    assert not any(f"Участник {index}" in text for index in range(1, 8))
    assert not any(f"Покупка {index}" in text for index in range(1, 64))
    assert all(page_texts)
