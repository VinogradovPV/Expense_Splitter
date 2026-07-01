from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi")

from expense_splitter.server.app import create_app
from expense_splitter.server.config import ServerSettings
from expense_splitter.server.routes import health as health_routes


def make_app(tmp_path):
    return create_app(
        ServerSettings(
            data_dir=tmp_path / "data",
            reports_dir=tmp_path / "reports",
            report_storage_backend="temp",
        )
    )


def test_server_app_registers_mvp_routes(tmp_path):
    app = make_app(tmp_path)
    paths = route_paths(app)

    assert "/health" in paths
    assert "/health/reporting" in paths
    assert "/api/purchases" in paths
    assert "/api/balances" in paths
    assert "/api/settlements" in paths
    assert "/api/current-report" in paths
    assert "/api/analytics-report" in paths
    assert "/api/reports/{report_id}/download" in paths
    assert "/api/settlement-periods" in paths
    assert "/api/settlement-periods/close" in paths
    assert "/api/settlement-periods/{settlement_period_id}/reopen" in paths


def test_health_endpoints_are_structured(tmp_path):
    app = make_app(tmp_path)

    health = health_routes.health(SimpleNamespace(app=app))
    reporting = health_routes.reporting_health()

    assert health["ok"] is True
    assert health["repository_backend"] == "yaml"
    assert reporting["ok"] is True
    assert "pdf_font" in reporting


def route_paths(app):
    paths = set()
    for route in app.routes:
        if hasattr(route, "path"):
            paths.add(route.path)
            continue
        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            paths.update(
                nested.path
                for nested in original_router.routes
                if hasattr(nested, "path")
            )
    return paths
