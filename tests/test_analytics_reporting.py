import csv
import json
from datetime import date
from decimal import Decimal

from expense_splitter.analytics import build_analytics_dataset, parse_period
from expense_splitter.analytics_reporting import generate_analytics_report
from expense_splitter.models import Participant, Purchase


def sample_dataset():
    participants = [Participant("Алиса"), Participant("Боб")]
    purchases = [
        Purchase(
            id="p1",
            date=date(2026, 6, 10),
            amount=Decimal("120.50"),
            payer="Алиса",
            participants=["Алиса", "Боб"],
            purchase_name="Обед",
            category="Еда",
        )
    ]
    return build_analytics_dataset(
        participants,
        [],
        purchases,
        parse_period("month", 2026, month=6),
    )


def test_all_report_creates_markdown_csv_png_and_metadata(tmp_path):
    report_dir = generate_analytics_report(sample_dataset(), tmp_path, "all")

    assert report_dir == tmp_path / "2026" / "2026-06"
    assert (report_dir / "analytics_report.md").is_file()
    assert (report_dir / "metadata.json").is_file()
    assert {path.name for path in (report_dir / "tables").glob("*.csv")} == {
        "summary.csv",
        "purchases.csv",
        "by_category.csv",
        "by_payer.csv",
        "by_participant.csv",
        "balances.csv",
        "settlements.csv",
        "top_purchases.csv",
        "warnings.csv",
    }
    assert len(list((report_dir / "charts").glob("*.png"))) == 6

    metadata = json.loads((report_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["period"]["id"] == "2026-06"
    assert metadata["summary"]["total_amount"] == "120.50"
    assert metadata["palette"]["name"] == "expense_splitter_default"


def test_csv_is_utf8_sig_with_russian_headers_and_decimal_strings(tmp_path):
    report_dir = generate_analytics_report(sample_dataset(), tmp_path, "csv")
    purchases_path = report_dir / "tables" / "purchases.csv"

    assert purchases_path.read_bytes().startswith(b"\xef\xbb\xbf")
    with purchases_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.reader(stream))

    assert rows[0][2] == "Наименование покупки"
    assert rows[1][3] == "120.50"
    assert rows[1][5] == "Алиса, Боб"


def test_markdown_only_does_not_create_csv_or_png(tmp_path):
    report_dir = generate_analytics_report(sample_dataset(), tmp_path, "markdown")

    text = (report_dir / "analytics_report.md").read_text(encoding="utf-8")
    assert "# Аналитика расходов: 2026-06" in text
    assert "Обед" in text
    assert not (report_dir / "tables").exists()
    assert not (report_dir / "charts").exists()


def test_all_report_documents_missing_charts_for_empty_period(tmp_path):
    dataset = build_analytics_dataset(
        [Participant("Алиса"), Participant("Боб")],
        [],
        [],
        parse_period("month", 2026, month=6),
    )

    report_dir = generate_analytics_report(dataset, tmp_path, "all")

    assert list((report_dir / "charts").glob("*.png")) == []
    warnings = (report_dir / "tables" / "warnings.csv").read_text(encoding="utf-8-sig")
    assert warnings.count("chart_no_data") == 6
    metadata = json.loads((report_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["warning_count"] == 6
