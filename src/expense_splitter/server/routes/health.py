"""Health endpoints."""

from __future__ import annotations

import importlib.util

import matplotlib
from fastapi import APIRouter, Request

from expense_splitter.reports.output_adapters import pdf_font_healthcheck

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict[str, object]:
    settings = request.app.state.settings
    return {
        "ok": True,
        "repository_backend": settings.repository_backend,
        "report_storage_backend": settings.report_storage_backend,
    }


@router.get("/health/reporting")
def reporting_health() -> dict[str, object]:
    return {
        "ok": True,
        "reportlab": importlib.util.find_spec("reportlab") is not None,
        "matplotlib_backend": matplotlib.get_backend(),
        "openpyxl": importlib.util.find_spec("openpyxl") is not None,
        "pdf_font": pdf_font_healthcheck(),
    }
