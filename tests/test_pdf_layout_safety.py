from datetime import date, timedelta
from decimal import Decimal

import pytest
from reportlab.platypus import Table

import expense_splitter.report_pdf as report_pdf
from expense_splitter.current_report import build_current_report_dataset, generate_current_report
from expense_splitter.models import Participant, Purchase
from expense_splitter.report_pdf import PdfDesignTokens, PdfTableSpec


def _layout_context():
    tools = report_pdf._load_reportlab_layout_tools()
    styles = report_pdf._styles(report_pdf.ensure_pdf_font(), tools)
    return tools, styles


def test_large_two_column_block_falls_back_to_splittable_vertical_layout():
    tools, styles = _layout_context()
    rows = [["Участник", "Сумма"], *[[f"Участник {index}", index] for index in range(12)]]
    specs = [
        PdfTableSpec("by_participant.csv", "Объем расходов на человека"),
        PdfTableSpec("balances.csv", "Балансы", display_mode="financial"),
    ]

    flowables = report_pdf._table_grid(
        specs,
        {spec.filename: rows for spec in specs},
        styles,
        700,
        500,
        tools,
        PdfDesignTokens(),
    )

    tables = [flowable for flowable in flowables if isinstance(flowable, Table)]
    assert len(tables) == 2
    assert all(table._ncols == 2 for table in tables)
    assert all(table.splitByRow for table in tables)


def test_small_tables_keep_two_column_layout():
    tools, styles = _layout_context()
    specs = [
        PdfTableSpec("by_payer.csv", "Расходы по плательщикам"),
        PdfTableSpec("by_category.csv", "Расходы по категориям"),
    ]
    rows = [["Название", "Сумма"], ["Короткое значение", "100.00"]]

    flowables = report_pdf._table_grid(
        specs,
        {spec.filename: rows for spec in specs},
        styles,
        700,
        500,
        tools,
        PdfDesignTokens(),
    )

    assert len(flowables) == 1
    assert isinstance(flowables[0], Table)
    assert flowables[0]._ncols == 2


def test_wrapped_purchase_participants_and_large_balance_sections_do_not_crash(tmp_path):
    if report_pdf.discover_cyrillic_font() is None:
        pytest.skip("No Cyrillic-capable PDF font available.")
    pypdf = pytest.importorskip("pypdf")
    names = [f"Участник с длинным именем {index}" for index in range(1, 8)]
    purchases = [
        Purchase(
            id=f"purchase-{index}",
            date=date(2026, 9, 1) + timedelta(days=index),
            amount=Decimal("1234.56") + index,
            payer=names[index % len(names)],
            participants=names,
            purchase_name=f"Очень длинное название покупки для проверки переноса {index}",
            category="Совместные расходы",
        )
        for index in range(10)
    ]
    dataset = build_current_report_dataset(
        [Participant(name) for name in names],
        purchases,
        scope="open",
    )

    report_dir = generate_current_report(dataset, tmp_path, "pdf")
    pdf_path = report_dir / "current_state.pdf"
    reader = pypdf.PdfReader(str(pdf_path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    compact_text = "".join(text.split())

    assert pdf_path.stat().st_size > 0
    assert "Покупки" in text
    assert all("".join(name.split()) in compact_text for name in names)
    assert all((page.extract_text() or "").strip() for page in reader.pages)
