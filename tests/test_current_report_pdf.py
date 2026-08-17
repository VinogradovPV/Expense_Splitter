from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

import expense_splitter.current_report as current_report
import expense_splitter.report_pdf as report_pdf
from expense_splitter.current_report import build_current_report_dataset, generate_current_report
from expense_splitter.models import Purchase
from expense_splitter.report_pdf import PdfTableSpec, discover_cyrillic_font
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

    pypdf = pytest.importorskip("pypdf")
    reader = pypdf.PdfReader(str(report_dir / "current_state.pdf"))
    assert len(reader.pages) <= 4
    assert all((page.extract_text() or "").strip() for page in reader.pages)


def test_current_report_format_all_includes_pdf(tmp_path):
    require_pdf_font()
    dataset = build_current_report_dataset(sample_participants(), sample_purchases(), scope="open")

    report_dir = generate_current_report(dataset, tmp_path, "all")

    assert_pdf_created(report_dir / "current_state.pdf")


def test_current_report_pdf_tables_start_with_settlements_without_duplicate_summary(
    tmp_path,
    monkeypatch,
):
    dataset = build_current_report_dataset(sample_participants(), sample_purchases(), scope="open")
    captured = {}

    def fake_write_pdf_report(output_path, **kwargs):
        captured["table_specs"] = kwargs["table_specs"]
        output_path.write_bytes(b"%PDF smoke")
        return output_path

    monkeypatch.setattr(current_report, "write_pdf_report", fake_write_pdf_report)

    generate_current_report(dataset, tmp_path, "pdf")

    table_filenames = [spec.filename for spec in captured["table_specs"]]
    assert table_filenames[0] == "settlements.csv"
    assert "summary.csv" not in table_filenames


def test_current_report_pdf_receives_operations_by_day_chart_manifest(tmp_path, monkeypatch):
    purchases = [
        Purchase(
            id="p1",
            date=date(2026, 7, 1),
            amount=Decimal("619.00"),
            payer="Alice",
            participants=["Alice", "Bob"],
            purchase_name="Hotel",
            category="Travel",
        ),
        Purchase(
            id="p2",
            date=date(2026, 7, 1),
            amount=Decimal("550.00"),
            payer="Bob",
            participants=["Alice", "Bob"],
            purchase_name="Dinner",
            category="Food",
        ),
        Purchase(
            id="p3",
            date=date(2026, 7, 3),
            amount=Decimal("90.00"),
            payer="Alice",
            participants=["Alice", "Bob"],
            purchase_name="Taxi",
            category="Transport",
        ),
    ]
    dataset = build_current_report_dataset(sample_participants(), purchases, scope="open")
    captured = {}

    def fake_write_pdf_report(output_path, **kwargs):
        captured["chart_paths"] = kwargs["chart_paths"]
        output_path.write_bytes(b"%PDF smoke")
        return output_path

    monkeypatch.setattr(current_report, "write_pdf_report", fake_write_pdf_report)

    generate_current_report(dataset, tmp_path, "pdf")

    assert "operations_by_day.png" in {path.name for path in captured["chart_paths"]}


def test_pdf_renderer_hides_purchase_service_columns(tmp_path, monkeypatch):
    require_pdf_font()
    tables_dir = tmp_path / "tables"
    tables_dir.mkdir()
    (tables_dir / "purchases.csv").write_text(
        "ID,Дата,Покупка,Сумма,payer_total,payer_rank\n"
        "p-1,2026-06-30,Кофе,100.00,500.00,1\n",
        encoding="utf-8-sig",
    )
    captured = {}
    original_filter = report_pdf.rows_for_visual_table

    def spy_rows_for_visual_table(filename, rows):
        filtered = original_filter(filename, rows)
        captured["rows"] = filtered
        return filtered

    monkeypatch.setattr(report_pdf, "rows_for_visual_table", spy_rows_for_visual_table)

    report_pdf.write_pdf_report(
        tmp_path / "report.pdf",
        title="Smoke",
        metadata_rows=[["Показатель", "Значение"]],
        tables_dir=tables_dir,
        table_specs=[PdfTableSpec("purchases.csv", "Покупки")],
    )

    assert captured["rows"] == [
        ["Дата", "Покупка", "Сумма"],
        ["2026-06-30", "Кофе", "100.00"],
    ]
