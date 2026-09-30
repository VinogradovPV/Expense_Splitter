from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi")

from expense_splitter.server.app import create_app
from expense_splitter.server.config import ServerSettings
from expense_splitter.server.routes import purchases as purchase_routes
from expense_splitter.server.routes import reports as report_routes
from expense_splitter.server.routes import settlement_periods as period_routes
from expense_splitter.server.schemas import (
    AnalyticsPeriodRequest,
    AnalyticsReportRequest,
    ClosePeriodRequest,
    CurrentReportRequest,
    PurchaseCreateRequest,
    SettlementPeriodReportRequest,
)


def make_app(tmp_path):
    return create_app(
        ServerSettings(
            data_dir=tmp_path / "data",
            reports_dir=tmp_path / "reports",
            report_storage_backend="temp",
        )
    )


def seed_purchase(app):
    payer, second = [
        participant.name for participant in app.state.repository.list_participants("local")
    ][:2]
    return purchase_routes.create_purchase(
        PurchaseCreateRequest(
            purchase_name="Server report seed",
            amount=Decimal("100.00"),
            payer=payer,
            participants=[payer, second],
            purchase_date=date(2026, 7, 1),
            category="food",
        ),
        tenant_id="local",
        service=app.state.purchase_service,
    )


def test_current_report_endpoint_returns_delivery_contract(tmp_path):
    app = make_app(tmp_path)
    seed_purchase(app)
    request = SimpleNamespace(app=app)

    result = report_routes.create_current_report(
        CurrentReportRequest(scope="open", formats={"xlsx"}),
        request=request,
        tenant_id="local",
        service=app.state.report_service,
    )

    assert result.report_type == "current"
    assert result.storage_backend == "temp"
    assert result.files[0].format == "xlsx"
    assert app.state.report_results[result.report_id]


def test_analytics_report_endpoint_returns_delivery_contract(tmp_path):
    app = make_app(tmp_path)
    seed_purchase(app)

    result = report_routes.create_analytics_report(
        AnalyticsReportRequest(
            period=AnalyticsPeriodRequest(kind="month", year=2026, month=7),
            formats={"xlsx"},
        ),
        request=SimpleNamespace(app=app),
        tenant_id="local",
        service=app.state.report_service,
    )

    assert result.report_type == "analytics"
    assert result.report_id == "2026-07"
    assert result.files[0].filename.endswith(".xlsx")


def test_settlement_period_close_reopen_and_report_endpoint(tmp_path):
    app = make_app(tmp_path)
    seed_purchase(app)

    closed = period_routes.close_settlement_period(
        ClosePeriodRequest(
            date_from=date(2026, 7, 1),
            date_to=date(2026, 7, 31),
            name="July",
        ),
        tenant_id="local",
        service=app.state.settlement_service,
    )
    periods = period_routes.list_settlement_periods("local", app.state.repository)
    period_report = report_routes.create_settlement_period_report(
        SettlementPeriodReportRequest(
            settlement_period_id=closed.settlement_period_id,
            formats={"xlsx"},
        ),
        request=SimpleNamespace(app=app),
        tenant_id="local",
        service=app.state.report_service,
    )
    reopened = period_routes.reopen_settlement_period(
        closed.settlement_period_id,
        tenant_id="local",
        service=app.state.settlement_service,
    )

    assert periods.items[0].settlement_period_id == closed.settlement_period_id
    assert period_report.report_type == "settlement_period"
    assert period_report.files[0].format == "xlsx"
    assert reopened.status == "reopened"


def test_download_endpoint_returns_file_response(tmp_path):
    app = make_app(tmp_path)
    seed_purchase(app)
    request = SimpleNamespace(app=app)
    result = report_routes.create_current_report(
        CurrentReportRequest(scope="open", formats={"xlsx"}),
        request=request,
        tenant_id="local",
        service=app.state.report_service,
    )

    response = report_routes.download_report(result.report_id, request)

    assert str(response.path).endswith(".xlsx")
