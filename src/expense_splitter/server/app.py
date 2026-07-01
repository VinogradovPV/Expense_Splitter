"""FastAPI application factory."""

from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from expense_splitter.repositories import PostgresRepositoryNotImplementedError
from expense_splitter.server.config import ServerSettings
from expense_splitter.server.dependencies import create_services
from expense_splitter.server.routes import health, purchases, reports, settlement_periods
from expense_splitter.storage import StorageError


def create_app(settings: ServerSettings | None = None) -> FastAPI:
    app = FastAPI(title="Expense Splitter API", version="0.1.1")
    app.state.settings = settings or ServerSettings.from_env()
    (
        app.state.repository,
        app.state.purchase_service,
        app.state.settlement_service,
        app.state.report_service,
    ) = create_services(app.state.settings)
    app.state.report_results = {}

    app.include_router(health.router)
    app.include_router(purchases.router)
    app.include_router(reports.router)
    app.include_router(settlement_periods.router)

    app.add_exception_handler(ValueError, _value_error_handler)
    app.add_exception_handler(StorageError, _storage_error_handler)
    app.add_exception_handler(
        PostgresRepositoryNotImplementedError,
        _postgres_not_implemented_handler,
    )
    return app


async def _value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return _error_response("VALIDATION_ERROR", str(exc), status_code=400)


async def _storage_error_handler(request: Request, exc: StorageError) -> JSONResponse:
    return _error_response("STORAGE_ERROR", str(exc), status_code=500)


async def _postgres_not_implemented_handler(
    request: Request,
    exc: PostgresRepositoryNotImplementedError,
) -> JSONResponse:
    return _error_response("POSTGRES_REPOSITORY_NOT_IMPLEMENTED", str(exc), status_code=501)


def _error_response(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": str(uuid.uuid4()),
            }
        },
    )
