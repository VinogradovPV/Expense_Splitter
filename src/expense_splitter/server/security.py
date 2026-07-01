"""Small server security helpers for cloud hardening."""

from __future__ import annotations

import hmac
from urllib.parse import SplitResult, urlsplit, urlunsplit

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


def validate_webhook_secret(expected: str | None, provided: str | None) -> bool:
    if not expected or not provided:
        return False
    return hmac.compare_digest(expected, provided)


def mask_secret_value(value: str | None) -> str | None:
    if value is None:
        return None
    if not value:
        return ""
    if len(value) <= 6:
        return "***"
    return f"{value[:2]}***{value[-2:]}"


def mask_database_url(database_url: str | None) -> str | None:
    if not database_url:
        return database_url
    parts = urlsplit(database_url)
    if not parts.password:
        return database_url

    username = parts.username or ""
    hostname = parts.hostname or ""
    port = f":{parts.port}" if parts.port is not None else ""
    netloc = f"{username}:***@{hostname}{port}"
    if "@" not in parts.netloc:
        return database_url

    return urlunsplit(
        SplitResult(
            scheme=parts.scheme,
            netloc=netloc,
            path=parts.path,
            query=parts.query,
            fragment=parts.fragment,
        )
    )


def safe_settings_snapshot(settings) -> dict[str, object]:
    return {
        "repository_backend": settings.repository_backend,
        "report_storage_backend": settings.report_storage_backend,
        "default_tenant_id": settings.default_tenant_id,
        "object_storage_bucket": mask_secret_value(settings.object_storage_bucket),
        "object_storage_prefix": settings.object_storage_prefix,
        "database_url": mask_database_url(settings.database_url),
        "telegram_webhook_secret_configured": bool(settings.telegram_webhook_secret),
        "rate_limit_per_minute": settings.rate_limit_per_minute,
    }
