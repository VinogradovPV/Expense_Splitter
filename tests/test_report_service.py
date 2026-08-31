import json
from datetime import date, datetime
from decimal import Decimal

from expense_splitter.analytics import build_analytics_dataset, parse_period
from expense_splitter.analytics_reporting import generate_analytics_report
from expense_splitter.models import Participant, Purchase, Settlement, SettlementPeriod
from expense_splitter.reports.output_adapters import (
    ObjectStorageReportOutputAdapter,
    TempReportOutputAdapter,
)
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


def make_single_day_analytics_repository(tmp_path) -> YamlExpenseRepository:
    data_dir = tmp_path / "data"
    initialize_data_files(data_dir, [Participant("Alice"), Participant("Bob")], [])
    repository = YamlExpenseRepository(data_dir)
    for purchase in (
        Purchase(
            id="p1",
            date=date(2026, 7, 3),
            amount=Decimal("619.00"),
            payer="Alice",
            participants=["Alice", "Bob"],
            purchase_name="Hotel",
            category="travel",
        ),
        Purchase(
            id="p2",
            date=date(2026, 7, 3),
            amount=Decimal("550.00"),
            payer="Bob",
            participants=["Alice", "Bob"],
            purchase_name="Dinner",
            category="food",
        ),
    ):
        repository.add_purchase(LOCAL_TENANT_ID, purchase)
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
    assert result.storage_backend == "local"
    assert result.telegram_caption
    assert any(file.filename == "current_state_report.md" for file in result.files)
    assert all(file.local_path is not None for file in result.files)


def test_report_service_skips_single_day_current_operations_chart(tmp_path):
    repository = make_single_day_analytics_repository(tmp_path)
    service = ReportService(repository, repository, repository)

    result = service.build_current_report(
        LOCAL_TENANT_ID,
        scope="open",
        formats={"png"},
        output_root=tmp_path / "reports" / "current",
    )

    assert any(warning["warning_type"] == "chart_not_enough_data" for warning in result.warnings)
    assert "operations_by_day" not in result.metadata["charts_generated"]
    assert not any(file.filename == "operations_by_day.png" for file in result.files)


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
    assert result.formats == {"markdown"}
    assert any(file.filename == "analytics_report.md" for file in result.files)


def test_report_service_skips_single_day_period_trend_and_ignores_stale_png(tmp_path):
    repository = make_single_day_analytics_repository(tmp_path)
    service = ReportService(repository, repository, repository)
    stale_chart_dir = tmp_path / "reports" / "analytics" / "2026" / "2026-07" / "charts"
    stale_chart_dir.mkdir(parents=True)
    (stale_chart_dir / "period_trend.png").write_bytes(b"stale")

    period_spec = parse_period("month", 2026, month=7)
    local_dataset = build_analytics_dataset(
        repository.list_participants(LOCAL_TENANT_ID),
        [],
        repository.list_purchases(LOCAL_TENANT_ID),
        period_spec,
    )
    local_report_dir = generate_analytics_report(
        local_dataset,
        tmp_path / "local_reports" / "analytics",
        "png",
    )

    result = service.build_analytics_report(
        LOCAL_TENANT_ID,
        period_spec,
        formats={"png"},
        output_root=tmp_path / "reports" / "analytics",
    )

    local_metadata = json.loads((local_report_dir / "metadata.json").read_text(encoding="utf-8"))
    assert not (local_report_dir / "charts" / "period_trend.png").exists()
    assert "period_trend" not in local_metadata["charts_generated"]
    assert any(
        item["reason"] == "chart_not_enough_data"
        for item in local_metadata["charts_skipped"]
    )
    assert any(warning["warning_type"] == "chart_not_enough_data" for warning in result.warnings)
    assert "period_trend" not in result.metadata["charts_generated"]
    assert not any(file.filename == "period_trend.png" for file in result.files)
    assert not (stale_chart_dir / "period_trend.png").exists()


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
    assert result.metadata["settlement_source"] == "snapshot"
    assert any(file.filename == "settlement_period_report.md" for file in result.files)


def test_report_service_uses_temp_output_adapter(tmp_path):
    repository = make_repository(tmp_path)
    service = ReportService(
        repository,
        repository,
        repository,
        output_adapter=TempReportOutputAdapter(base_dir=tmp_path / "tmp_reports"),
    )

    result = service.create_current_report(LOCAL_TENANT_ID, scope="open", formats={"html"})

    assert result.storage_backend == "temp"
    assert len(result.files) == 1
    assert result.files[0].format == "html"
    assert result.files[0].local_path is not None
    assert result.files[0].local_path.is_file()


def test_report_service_returns_object_storage_keys_for_cloud_stub(tmp_path):
    repository = make_repository(tmp_path)
    service = ReportService(
        repository,
        repository,
        repository,
        output_adapter=ObjectStorageReportOutputAdapter(
            bucket="expense-splitter-reports",
            base_dir=tmp_path / "object_workspace",
        ),
    )

    result = service.create_current_report(LOCAL_TENANT_ID, scope="open", formats={"xlsx"})

    assert result.storage_backend == "object_storage"
    assert result.metadata["bucket"] == "expense-splitter-reports"
    assert result.files
    assert all(file.storage_key is not None for file in result.files)
    assert {file.format for file in result.files} == {"xlsx"}
