import json
from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi")

from fastapi.responses import JSONResponse

from expense_splitter.server.app import create_app
from expense_splitter.server.config import ServerSettings
from expense_splitter.server.routes import telegram as telegram_routes
from expense_splitter.server.security import (
    SECURITY_HEADERS,
    mask_database_url,
    safe_settings_snapshot,
    validate_webhook_secret,
)


def make_request(settings: ServerSettings):
    app = SimpleNamespace(state=SimpleNamespace(settings=settings))
    return SimpleNamespace(app=app)


def test_webhook_secret_validation_uses_constant_time_compare():
    assert validate_webhook_secret("secret", "secret")
    assert not validate_webhook_secret("secret", "wrong")
    assert not validate_webhook_secret("secret", None)
    assert not validate_webhook_secret(None, "secret")


def test_telegram_webhook_rejects_missing_or_invalid_secret():
    missing = telegram_routes.telegram_webhook(make_request(ServerSettings()))
    invalid = telegram_routes.telegram_webhook(
        make_request(ServerSettings(telegram_webhook_secret="secret")),
        x_telegram_bot_api_secret_token="wrong",
    )

    assert isinstance(missing, JSONResponse)
    assert missing.status_code == 503
    assert _payload(missing)["error"]["code"] == "WEBHOOK_SECRET_NOT_CONFIGURED"
    assert isinstance(invalid, JSONResponse)
    assert invalid.status_code == 401
    assert _payload(invalid)["error"]["code"] == "WEBHOOK_SECRET_INVALID"


def test_telegram_webhook_accepts_valid_secret_without_handling_update_body():
    response = telegram_routes.telegram_webhook(
        make_request(ServerSettings(telegram_webhook_secret="secret")),
        x_telegram_bot_api_secret_token="secret",
    )

    assert response == {
        "ok": True,
        "status": "webhook_validated",
        "handled": False,
    }


def test_settings_snapshot_masks_database_url_and_secret_values():
    settings = ServerSettings(
        database_url="postgresql+psycopg://user:password@example.net:5432/db",
        object_storage_bucket="expense-splitter-private",
        telegram_webhook_secret="secret",
        rate_limit_per_minute=30,
    )

    snapshot = safe_settings_snapshot(settings)

    assert snapshot["database_url"] == "postgresql+psycopg://user:***@example.net:5432/db"
    assert snapshot["object_storage_bucket"] == "ex***te"
    assert snapshot["telegram_webhook_secret_configured"] is True
    assert snapshot["rate_limit_per_minute"] == 30
    assert "password" not in str(snapshot)
    assert "telegram_webhook_secret" not in snapshot


def test_server_app_exposes_security_headers_configuration(tmp_path):
    app = create_app(
        ServerSettings(
            data_dir=tmp_path / "data",
            reports_dir=tmp_path / "reports",
        )
    )

    assert "/telegram/webhook" in _route_paths(app)
    assert SECURITY_HEADERS["X-Content-Type-Options"] == "nosniff"
    assert SECURITY_HEADERS["X-Frame-Options"] == "DENY"


def test_mask_database_url_keeps_urls_without_password_unchanged():
    value = "postgresql+psycopg://example.net/db"

    assert mask_database_url(value) == value


def _payload(response: JSONResponse) -> dict[str, object]:
    return json.loads(response.body.decode("utf-8"))


def _route_paths(app) -> set[str]:
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
