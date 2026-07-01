"""Report endpoints backed by ReportService."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from expense_splitter.analytics import parse_period
from expense_splitter.reports.result import ReportResult
from expense_splitter.server.dependencies import get_report_service, get_tenant_id
from expense_splitter.server.schemas import (
    AnalyticsReportRequest,
    CurrentReportRequest,
    ReportResultResponse,
    SettlementPeriodReportRequest,
    report_result_response,
)
from expense_splitter.services import ReportService

router = APIRouter(prefix="/api", tags=["reports"])


@router.post("/current-report", response_model=ReportResultResponse)
def create_current_report(
    payload: CurrentReportRequest,
    request: Request,
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    service: Annotated[ReportService, Depends(get_report_service)],
) -> ReportResultResponse:
    result = service.create_current_report(tenant_id, payload.scope, payload.formats)
    _store_report_result(request, result)
    return report_result_response(result)


@router.post("/analytics-report", response_model=ReportResultResponse)
def create_analytics_report(
    payload: AnalyticsReportRequest,
    request: Request,
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    service: Annotated[ReportService, Depends(get_report_service)],
) -> ReportResultResponse:
    period_spec = parse_period(
        payload.period.kind,
        payload.period.year,
        month=payload.period.month,
        quarter=payload.period.quarter,
    )
    result = service.create_analytics_report(
        tenant_id,
        period_spec,
        payload.formats,
        include_undated=payload.include_undated,
    )
    _store_report_result(request, result)
    return report_result_response(result)


@router.post("/settlement-period-report", response_model=ReportResultResponse)
def create_settlement_period_report(
    payload: SettlementPeriodReportRequest,
    request: Request,
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    service: Annotated[ReportService, Depends(get_report_service)],
) -> ReportResultResponse:
    result = service.create_settlement_period_report(
        tenant_id,
        payload.settlement_period_id,
        payload.formats,
    )
    _store_report_result(request, result)
    return report_result_response(result)


@router.get("/reports/{report_id}/download")
def download_report(
    report_id: str,
    request: Request,
    filename: str | None = None,
):
    result = request.app.state.report_results.get(report_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Report not found.")

    candidates = result.files
    if filename is not None:
        candidates = [file for file in candidates if file.filename == filename]
    for file in candidates:
        if file.local_path is not None and Path(file.local_path).is_file():
            return FileResponse(
                file.local_path,
                filename=file.filename,
                media_type=file.content_type,
            )
    raise HTTPException(status_code=404, detail="Report file not found.")


def _store_report_result(request: Request, result: ReportResult) -> None:
    request.app.state.report_results[result.report_id] = result
