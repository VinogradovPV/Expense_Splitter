"""Telegram webhook endpoint stub with secret validation."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from expense_splitter.server.security import validate_webhook_secret

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/webhook")
def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Annotated[
        str | None,
        Header(alias="X-Telegram-Bot-Api-Secret-Token"),
    ] = None,
):
    settings = request.app.state.settings
    if not settings.telegram_webhook_secret:
        return _error_response(
            "WEBHOOK_SECRET_NOT_CONFIGURED",
            "Telegram webhook secret is not configured.",
            status_code=503,
        )
    if not validate_webhook_secret(
        settings.telegram_webhook_secret,
        x_telegram_bot_api_secret_token,
    ):
        return _error_response(
            "WEBHOOK_SECRET_INVALID",
            "Telegram webhook secret is invalid.",
            status_code=401,
        )
    return {
        "ok": True,
        "status": "webhook_validated",
        "handled": False,
    }


def _error_response(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": False,
            "error": {
                "code": code,
                "message": message,
            },
        },
    )
