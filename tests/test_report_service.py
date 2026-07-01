from datetime import date, datetime
from decimal import Decimal

from expense_splitter.analytics import parse_period
from expense_splitter.models import Participant, Purchase, Settlement, SettlementPeriod
from expense_splitter.repositories import LOCAL_TENANT_ID, YamlExpenseRepository
from expense_splitter.services.report_service import ReportService
from expense_splitter.storage import initialize_data_files


def make_repository(tmp_path) -> YamlExpenseRepository:
    data_dir = tmp_path / "data"
    initialize_data_files(data_dir, [Participant("Alice"), Participant("Bob")], [])
    repository = YamlExpenseRepository(data_dir)
    repository.add_purchase(
        LOCAL_TENANT_ID,
        Purchase(
            id="p1",
            date=date(2026, 7, 1),
            amount=Decimal("100.00"),
            payer="Alice",
            participants=["Alice", "Bob"],
            purchase_name="Dinner",
            category="food",
        ),
    )
    return repository


def test_report_service_builds_current_report_result(tmp_path):
    repository = make_repository(tmp_path)
    service = ReportService(repository, repository, repository)

    result = service.build_current_report(
        LOCAL_TENANT_ID,
        scope="open",
        formats={"markdown"},
        output_root=tmp_path / "reports" / "current",
    )

    assert result.report_type == "current"
    assert result.report_id == "open"
    assert result.output_dir.exists()
    assert any(path.name == "current_state_report.md" for path in result.files)


def test_report_service_builds_analytics_report_result(tmp_path):
    repository = make_repository(tmp_path)
    service = ReportService(repository, repository, repository)

    result = service.build_analytics_report(
        LOCAL_TENANT_ID,
        parse_period("month", 2026, month=7),
        formats={"markdown"},
        output_root=tmp_path / "reports" / "analytics",
    )

    assert result.report_type == "analytics"
    assert result.report_id == "2026-07"
    assert any(path.name == "analytics_report.md" for path in result.files)


def test_report_service_builds_settlement_period_report_result(tmp_path):
    repository = make_repository(tmp_path)
    repository.save_period(
        LOCAL_TENANT_ID,
        SettlementPeriod(
            id="period-1",
            name="July",
            status="closed",
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 31),
            closed_at=datetime(2026, 8, 1, 10, 0, 0),
            purchase_ids=["p1"],
            total_amount=Decimal("100.00"),
            settlements=[Settlement("Bob", "Alice", Decimal("50.00"))],
        ),
    )
    service = ReportService(repository, repository, repository)

    result = service.build_settlement_period_report(
        LOCAL_TENANT_ID,
        "period-1",
        formats={"markdown"},
        output_root=tmp_path / "reports" / "periods",
    )

    assert result.report_type == "settlement_period"
    assert result.report_id == "period-1"
    assert any(path.name == "settlement_period_report.md" for path in result.files)
