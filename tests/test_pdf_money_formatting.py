from decimal import Decimal
from pathlib import Path

import pytest

from expense_splitter.report_formatting import (
    PDF_MONEY_HEADERS,
    format_money_for_pdf,
    format_pdf_cell,
    format_percent_for_pdf,
)
from expense_splitter.report_pdf import PdfTableSpec, discover_cyrillic_font, write_pdf_report


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("6062.00"), "6 062,00"),
        ("1567.28", "1 567,28"),
        ("4494.72", "4 494,72"),
        ("-1165.94", "-1 165,94"),
        ("0.00", "0,00"),
        ("151.30", "151,30"),
        ("619.25", "619,25"),
        ("550.75", "550,75"),
    ],
)
def test_format_money_for_pdf_preserves_cents(value, expected):
    assert format_money_for_pdf(value) == expected


@pytest.mark.parametrize("header", sorted(PDF_MONEY_HEADERS))
def test_all_pdf_money_headers_use_two_decimal_places(header):
    assert format_pdf_cell("584.5", header) == "584,50"


def test_percentages_use_percent_format_instead_of_money_format():
    assert format_pdf_cell("54.68", "Доля, %") == "54,68"
    assert format_pdf_cell("15.3", "Доля оплат, %") == "15,30"
    assert format_percent_for_pdf("54.68") == "54,68"


def test_non_financial_values_are_not_formatted_as_money():
    assert format_pdf_cell("00123", "ID") == "00123"
    assert format_pdf_cell("9", "Покупок") == "9"
    assert format_pdf_cell("2026-08-31", "Дата") == "2026-08-31"


def test_invalid_and_empty_money_values_are_preserved_safely():
    assert format_money_for_pdf(None) == ""
    assert format_money_for_pdf("нет данных") == "нет данных"


def test_redesigned_pdf_text_preserves_balance_and_kpi_cents(tmp_path: Path):
    if discover_cyrillic_font() is None:
        pytest.skip("No Cyrillic-capable PDF font available.")
    pypdf = pytest.importorskip("pypdf")
    tables_dir = tmp_path / "tables"
    tables_dir.mkdir()
    (tables_dir / "balances.csv").write_text(
        'Участник,Оплачено,Объем расходов на человека,"Итог: + получит, − должен"\n'
        "Павел,6062.00,1567.28,4494.72\n"
        "Сергей,250.00,1415.94,-1165.94\n"
        "Мария,0.00,151.30,-151.30\n",
        encoding="utf-8-sig",
    )
    (tables_dir / "purchases.csv").write_text(
        "Дата,Покупка,Сумма\n"
        "2026-08-30,Покупка 1,619.25\n"
        "2026-08-31,Покупка 2,550.75\n",
        encoding="utf-8-sig",
    )
    output_path = tmp_path / "money-smoke.pdf"

    write_pdf_report(
        output_path,
        title="Проверка денежных значений",
        metadata_rows=[
            ["Показатель", "Значение"],
            ["Общая сумма", "1169.00"],
            ["Средний чек", "584.50"],
        ],
        tables_dir=tables_dir,
        table_specs=[
            PdfTableSpec("balances.csv", "Балансы", display_mode="financial"),
            PdfTableSpec("purchases.csv", "Покупки", display_mode="full"),
        ],
    )

    reader = pypdf.PdfReader(str(output_path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    compact_text = " ".join(text.split())
    for expected in (
        "6 062,00",
        "1 567,28",
        "4 494,72",
        "250,00",
        "1 415,94",
        "-1 165,94",
        "0,00",
        "151,30",
        "-151,30",
        "619,25",
        "550,75",
        "1 169,00",
        "584,50",
    ):
        assert expected in compact_text
