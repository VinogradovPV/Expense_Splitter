import pytest

import expense_splitter.report_pdf as report_pdf
from expense_splitter.report_pdf import (
    PdfTableSpec,
    _column_widths_for_table,
    _format_kpi_value,
    _format_pdf_table_cell,
)


def test_report_manifest_preserves_requested_chart_order_and_ignores_stale_files(tmp_path):
    charts_dir = tmp_path / "charts"
    charts_dir.mkdir()
    paths = [charts_dir / "top_purchases.png", charts_dir / "balances.png"]
    for path in [*paths, charts_dir / "period_trend.png"]:
        path.write_bytes(b"png")

    manifest = report_pdf._build_manifest([], paths, charts_dir, "current")

    assert [chart.key for chart in manifest.charts] == ["balances", "top_purchases"]
    assert "period_trend" not in {chart.key for chart in manifest.charts}


def test_compact_purchase_rows_hide_service_fields_and_count_participants():
    rows = [
        ["ID", "Дата", "Покупка", "Категория", "Сумма", "Плательщик", "Участники", "Статус"],
        ["p-1", "2026-06-30", "Кофе", "Еда", "100.00", "Alice", "Alice, Bob", "Открыта"],
    ]

    compact = report_pdf._compact_purchase_rows(rows)

    assert compact == [
        ["Дата", "Покупка", "Категория", "Сумма", "Плательщик", "Участников"],
        ["2026-06-30", "Кофе", "Еда", "100.00", "Alice", "Alice, Bob"],
    ]


def test_summary_is_split_into_context_and_kpis():
    context, kpis = report_pdf._split_summary_rows(
        [
            ["Отчетный период", "2026 год"],
            ["Общая сумма", "1200.00"],
            ["Количество покупок", 3],
            ["Количество участников", 2],
        ]
    )

    assert context == [["Отчетный период", "2026 год"]]
    assert [row[0] for row in kpis] == [
        "Общая сумма",
        "Количество покупок",
        "Количество участников",
    ]


def test_analytics_specs_use_appendix_instead_of_duplicate_summary():
    from expense_splitter.analytics_reporting import ANALYTICS_PDF_TABLES

    assert "summary.csv" not in {spec.filename for spec in ANALYTICS_PDF_TABLES}
    appendix = [spec for spec in ANALYTICS_PDF_TABLES if spec.section == "appendix"]
    assert appendix == [
        PdfTableSpec(
            "purchases.csv",
            "Все покупки",
            display_mode="appendix",
            section="appendix",
        )
    ]


def test_balance_table_reserves_single_line_width_for_first_headers():
    width = 360
    rows = [
        ["Участник", "Оплачено", "Объем расходов на человека", "Итог: + получит, − должен"],
        ["Владимир", "10022.00", "9054.97", "967.03"],
    ]

    widths = _column_widths_for_table(rows, width, "balances.csv")

    assert widths == pytest.approx([64.8, 61.2, 108.0, 126.0])
    assert sum(widths) == pytest.approx(width)


def test_pdf_money_values_round_up_without_decimal_fraction():
    assert _format_pdf_table_cell("10378.67", "Оплачено") == "10 379"
    assert _format_pdf_table_cell("-2998.02", "Итог: + получит, − должен") == "-2 998"
    assert _format_pdf_table_cell("15.39", "Доля оплат, %") == "15.39"
    assert _format_kpi_value(1200.01, "Общая сумма") == "1 201"
    assert _format_kpi_value(63, "Покупок") == "63"
