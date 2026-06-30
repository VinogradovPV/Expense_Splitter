from datetime import date
from decimal import Decimal

from typer.testing import CliRunner

from expense_splitter.analytics import build_analytics_dataset, parse_period
from expense_splitter.analytics_reporting import generate_analytics_report
from expense_splitter.cli import app
from expense_splitter.defaults import DEFAULT_GROUPS, DEFAULT_PARTICIPANTS
from expense_splitter.models import Participant, Purchase
from expense_splitter.storage import initialize_data_files, save_purchases

runner = CliRunner()


def dataset(with_purchase: bool = True):
    purchases = []
    if with_purchase:
        purchases.append(
            Purchase(
                id="p1",
                date=date(2026, 6, 10),
                amount=Decimal("120.50"),
                payer="Алиса",
                participants=["Алиса", "Боб"],
                purchase_name="Обед",
                category="Еда",
            )
        )
    return build_analytics_dataset(
        [Participant("Алиса"), Participant("Боб")],
        [],
        purchases,
        parse_period("month", 2026, month=6),
    )


def test_html_report_is_offline_utf8_and_links_artifacts(tmp_path):
    report_dir = generate_analytics_report(dataset(), tmp_path, "html")
    path = report_dir / "analytics_dashboard.html"
    text = path.read_text(encoding="utf-8")

    assert '<meta charset="UTF-8">' in text
    assert "Expense Splitter — аналитика расходов" in text
    assert "Общая сумма" in text
    assert "Доля оплат, %" in text
    assert "Объем расходов на человека" in text
    assert "payer_total" not in text
    assert "payer_rank" not in text
    assert 'class="num"' in text
    assert 'href="tables/purchases.csv"' in text
    assert 'href="analytics_report.md"' in text
    assert 'src="charts/spending_by_category.png"' in text
    assert "cdn" not in text.lower()
    assert "http://" not in text and "https://" not in text
    assert (report_dir / "metadata.json").is_file()


def test_html_report_handles_missing_charts(tmp_path):
    report_dir = generate_analytics_report(dataset(False), tmp_path, "html")
    text = (report_dir / "analytics_dashboard.html").read_text(encoding="utf-8")

    assert text.count("График не создан: нет данных за выбранный период.") == 6


def test_all_format_includes_html(tmp_path):
    report_dir = generate_analytics_report(dataset(), tmp_path, "all")
    assert (report_dir / "analytics_dashboard.html").is_file()


def test_cli_html_format(tmp_path):
    data_dir = tmp_path / "data"
    output_root = tmp_path / "reports"
    initialize_data_files(data_dir, DEFAULT_PARTICIPANTS, DEFAULT_GROUPS)
    save_purchases(
        data_dir / "purchases.yaml",
        [
            Purchase(
                id="p1",
                date=date(2026, 6, 10),
                amount=Decimal("120.50"),
                payer=DEFAULT_PARTICIPANTS[0].name,
                participants=[item.name for item in DEFAULT_PARTICIPANTS[:2]],
                purchase_name="Обед",
            )
        ],
    )

    result = runner.invoke(
        app,
        [
            "analytics",
            "--period",
            "month",
            "--year",
            "2026",
            "--month",
            "6",
            "--format",
            "html",
            "--output-root",
            str(output_root),
            "--data-dir",
            str(data_dir),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert (output_root / "2026" / "2026-06" / "analytics_dashboard.html").is_file()
