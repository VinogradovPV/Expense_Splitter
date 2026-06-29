import csv
import json
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from openpyxl import load_workbook
from typer.testing import CliRunner

from expense_splitter.cli import app
from expense_splitter.models import Participant, Purchase, Settlement, SettlementPeriod
from expense_splitter.settlement_period_report import (
    SettlementPeriodReportError,
    build_settlement_period_report_dataset,
    generate_settlement_period_report,
)
from expense_splitter.storage import (
    initialize_data_files,
    save_participants,
    save_purchases,
    save_settlement_periods,
)

runner = CliRunner()


def sample_participants():
    return [Participant("Alice"), Participant("Bob"), Participant("Cara")]


def sample_purchases():
    return [
        Purchase(
            id="p1",
            date=date(2026, 6, 1),
            amount=Decimal("120.00"),
            payer="Alice",
            participants=["Alice", "Bob", "Cara"],
            purchase_name="Lunch",
            category="Food",
            comment="team",
            settled=True,
            settlement_period_id="settlement_2026_06_30_001",
        ),
        Purchase(
            id="p2",
            date=date(2026, 6, 2),
            amount=Decimal("60.00"),
            payer="Bob",
            participants=["Alice", "Bob"],
            purchase_name="Taxi",
            category="Transport",
            settled=True,
            settlement_period_id="settlement_2026_06_30_001",
        ),
        Purchase(
            id="open-1",
            date=date(2026, 7, 1),
            amount=Decimal("20.00"),
            payer="Cara",
            participants=["Cara"],
            purchase_name="Coffee",
            category="Food",
        ),
    ]


def sample_period(status="closed"):
    return SettlementPeriod(
        id="settlement_2026_06_30_001",
        name="June",
        status=status,
        date_from=date(2026, 6, 1),
        date_to=date(2026, 6, 30),
        closed_at=datetime(2026, 6, 30, 20, 0, 0),
        reopened_at=datetime(2026, 7, 2, 9, 0, 0) if status == "reopened" else None,
        purchase_ids=["p1", "p2"],
        total_amount=Decimal("180.00"),
        settlements=[
            Settlement("Bob", "Alice", Decimal("70.00")),
            Settlement("Cara", "Alice", Decimal("40.00")),
        ],
    )


def test_report_dataset_uses_period_snapshot_and_purchase_ids():
    dataset = build_settlement_period_report_dataset(
        [sample_period()],
        sample_purchases(),
        sample_participants(),
        "settlement_2026_06_30_001",
    )

    assert [purchase.id for purchase in dataset.purchases] == ["p1", "p2"]
    assert dataset.summary["total_amount"] == Decimal("180.00")
    assert dataset.summary["purchase_count"] == 2
    assert dataset.summary["settlement_count"] == 2
    settlement_rows = [
        (row.from_participant, row.to_participant, row.amount) for row in dataset.settlements
    ]
    assert settlement_rows == [
        ("Bob", "Alice", Decimal("70.00")),
        ("Cara", "Alice", Decimal("40.00")),
    ]
    assert dataset.settlement_source == "snapshot"
    assert dataset.balance_source == "recomputed_from_period_purchases"
    assert {row["category"] for row in dataset.by_category} == {"Food", "Transport"}
    assert {row["payer"] for row in dataset.by_payer} == {"Alice", "Bob"}
    assert {row["participant"] for row in dataset.by_participant} == {"Alice", "Bob", "Cara"}


def test_missing_settlement_period_error_is_user_friendly():
    with pytest.raises(
        SettlementPeriodReportError,
        match="Период взаиморасчетов не найден: missing",
    ):
        build_settlement_period_report_dataset([], [], sample_participants(), "missing")


def test_missing_purchase_id_adds_warning_without_failing():
    period = sample_period()
    period.purchase_ids.append("missing-purchase")

    dataset = build_settlement_period_report_dataset(
        [period],
        sample_purchases(),
        sample_participants(),
        period.id,
    )

    assert dataset.missing_purchase_ids == ["missing-purchase"]
    assert any(row["warning_type"] == "missing_purchase" for row in dataset.warnings)


def test_reopened_and_empty_period_add_warnings():
    period = sample_period(status="reopened")
    period.purchase_ids = []
    period.total_amount = Decimal("0.00")
    period.settlements = []

    dataset = build_settlement_period_report_dataset(
        [period],
        sample_purchases(),
        sample_participants(),
        period.id,
    )

    warning_types = {row["warning_type"] for row in dataset.warnings}
    assert {"period_reopened", "no_purchases", "missing_snapshot_settlements"} <= warning_types


def test_generate_settlement_period_report_writes_all_outputs(tmp_path):
    dataset = build_settlement_period_report_dataset(
        [sample_period()],
        sample_purchases(),
        sample_participants(),
        "settlement_2026_06_30_001",
        generated_at=datetime(2026, 6, 30, 21, 0, 0, tzinfo=timezone.utc),
    )

    report_dir = generate_settlement_period_report(dataset, tmp_path, "all")

    assert report_dir == tmp_path / "settlement_2026_06_30_001_2026-06-30_21-00-00"
    assert (report_dir / "settlement_period_report.md").is_file()
    assert (report_dir / "settlement_period_dashboard.html").is_file()
    assert (report_dir / "settlement_period.xlsx").is_file()
    assert (report_dir / "metadata.json").is_file()
    assert {path.name for path in (report_dir / "tables").glob("*.csv")} == {
        "summary.csv",
        "purchases.csv",
        "by_category.csv",
        "by_payer.csv",
        "by_participant.csv",
        "balances.csv",
        "settlements.csv",
        "warnings.csv",
    }
    assert {path.name for path in (report_dir / "charts").glob("*.png")} == {
        "spending_by_category.png",
        "spending_by_payer.png",
        "participant_share.png",
        "balances.png",
        "top_purchases.png",
    }

    metadata = json.loads((report_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["report_type"] == "settlement_period"
    assert metadata["settlement_period_id"] == "settlement_2026_06_30_001"
    assert metadata["snapshot_source"]["settlements"] == "snapshot"
    assert metadata["snapshot_source"]["balance_source"] == "recomputed_from_period_purchases"


def test_settlement_period_report_files_are_readable(tmp_path):
    dataset = build_settlement_period_report_dataset(
        [sample_period()],
        sample_purchases(),
        sample_participants(),
        "settlement_2026_06_30_001",
    )

    report_dir = generate_settlement_period_report(dataset, tmp_path, "all")

    purchases_path = report_dir / "tables" / "purchases.csv"
    assert purchases_path.read_bytes().startswith(b"\xef\xbb\xbf")
    with purchases_path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.reader(stream))
    assert rows[0] == [
        "ID",
        "Дата",
        "Покупка",
        "Категория",
        "Сумма",
        "Плательщик",
        "Участники",
        "Статус",
        "Комментарий",
    ]
    assert any(row[2] == "Lunch" for row in rows[1:])

    markdown = (report_dir / "settlement_period_report.md").read_text(encoding="utf-8")
    assert "# Отчет по периоду взаиморасчетов" in markdown
    html = (report_dir / "settlement_period_dashboard.html").read_text(encoding="utf-8")
    assert '<meta charset="utf-8">' in html
    assert "Отчет по периоду взаиморасчетов" in html

    workbook = load_workbook(report_dir / "settlement_period.xlsx")
    assert workbook.sheetnames == [
        "Summary",
        "Purchases",
        "By Category",
        "By Payer",
        "By Participant",
        "Balances",
        "Settlements",
        "Warnings",
        "Charts",
    ]


def test_empty_period_does_not_fail_and_writes_warning(tmp_path):
    period = sample_period()
    period.purchase_ids = []
    period.total_amount = Decimal("0.00")
    period.settlements = []
    dataset = build_settlement_period_report_dataset(
        [period],
        sample_purchases(),
        sample_participants(),
        period.id,
    )

    report_dir = generate_settlement_period_report(dataset, tmp_path, "all")

    warnings_text = (report_dir / "tables" / "warnings.csv").read_text(encoding="utf-8-sig")
    assert "Период не содержит покупок" in warnings_text
    assert list((report_dir / "charts").glob("*.png")) == []


def test_cli_settlement_period_report_generates_requested_outputs(tmp_path):
    data_dir = tmp_path / "data"
    output_root = tmp_path / "reports"
    initialize_data_files(data_dir, [], [])
    save_participants(data_dir / "participants.yaml", sample_participants())
    save_purchases(data_dir / "purchases.yaml", sample_purchases())
    save_settlement_periods(data_dir / "settlement_periods.yaml", [sample_period()])

    result = runner.invoke(
        app,
        [
            "settlement-period",
            "report",
            "settlement_2026_06_30_001",
            "--format",
            "html",
            "--output-root",
            str(output_root),
            "--data-dir",
            str(data_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Settlement period report generated" in result.stdout
    report_dirs = list(output_root.glob("settlement_2026_06_30_001_*"))
    assert len(report_dirs) == 1
    assert (report_dirs[0] / "settlement_period_dashboard.html").is_file()
    assert not (report_dirs[0] / "settlement_period.xlsx").exists()


def test_cli_missing_settlement_period_has_no_traceback(tmp_path):
    data_dir = tmp_path / "data"
    initialize_data_files(data_dir, [], [])

    result = runner.invoke(
        app,
        [
            "settlement-period",
            "report",
            "missing",
            "--data-dir",
            str(data_dir),
        ],
    )

    assert result.exit_code != 0
    assert "Период взаиморасчетов не найден: missing" in result.stdout
    assert "Traceback" not in result.stdout
