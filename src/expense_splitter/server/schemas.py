"""Pydantic schemas for the FastAPI backend MVP."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from expense_splitter.models import Balance, Purchase, Settlement, SettlementPeriod
from expense_splitter.reports.result import ReportFile, ReportResult


class ErrorPayload(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorPayload


class PurchaseCreateRequest(BaseModel):
    purchase_name: str = Field(default="н/д", min_length=1)
    amount: Decimal
    payer: str
    participants: list[str]
    purchase_date: date | None = None
    category: str | None = None
    comment: str | None = None


class PurchaseResponse(BaseModel):
    purchase_id: str
    date: date | None
    purchase_name: str
    amount: str
    payer: str
    participants: list[str]
    category: str | None
    comment: str | None
    status: str
    settlement_period_id: str | None


class PurchaseListResponse(BaseModel):
    items: list[PurchaseResponse]


class BalanceResponse(BaseModel):
    participant: str
    paid: str
    share: str
    net: str


class SettlementResponse(BaseModel):
    from_participant: str
    to_participant: str
    amount: str


class BalanceListResponse(BaseModel):
    items: list[BalanceResponse]


class SettlementListResponse(BaseModel):
    items: list[SettlementResponse]


class ClosePeriodRequest(BaseModel):
    date_from: date
    date_to: date
    name: str
    created_by: str = "server"


class SettlementPeriodResponse(BaseModel):
    settlement_period_id: str
    name: str
    status: str
    date_from: date
    date_to: date
    closed_at: datetime
    reopened_at: datetime | None
    purchase_ids: list[str]
    total_amount: str
    transfer_count: int


class SettlementPeriodListResponse(BaseModel):
    items: list[SettlementPeriodResponse]


class CurrentReportRequest(BaseModel):
    scope: str = "open"
    formats: set[str] = Field(default_factory=lambda: {"pdf"})


class AnalyticsPeriodRequest(BaseModel):
    kind: str
    year: int
    month: int | None = None
    quarter: int | None = None


class AnalyticsReportRequest(BaseModel):
    period: AnalyticsPeriodRequest
    formats: set[str] = Field(default_factory=lambda: {"pdf"})
    include_undated: bool = False


class ReportFileResponse(BaseModel):
    format: str
    filename: str
    content_type: str
    size_bytes: int | None
    storage_key: str | None
    local_path: str | None
    checksum_sha256: str | None


class ReportResultResponse(BaseModel):
    report_id: str
    report_type: str
    formats: list[str]
    files: list[ReportFileResponse]
    created_at: datetime
    expires_at: datetime | None
    storage_backend: str
    telegram_caption: str
    warnings: list[dict[str, object]]
    metadata: dict[str, object]

    model_config = ConfigDict(arbitrary_types_allowed=True)


class SettlementPeriodReportRequest(BaseModel):
    settlement_period_id: str
    formats: set[str] = Field(default_factory=lambda: {"pdf"})


def purchase_response(purchase: Purchase) -> PurchaseResponse:
    return PurchaseResponse(
        purchase_id=purchase.id,
        date=purchase.date,
        purchase_name=purchase.purchase_name,
        amount=str(purchase.amount),
        payer=purchase.payer,
        participants=list(purchase.participants),
        category=purchase.category,
        comment=purchase.comment,
        status="settled" if purchase.settled else "open",
        settlement_period_id=purchase.settlement_period_id,
    )


def balance_response(balance: Balance) -> BalanceResponse:
    return BalanceResponse(
        participant=balance.participant,
        paid=str(balance.paid),
        share=str(balance.share),
        net=str(balance.net),
    )


def settlement_response(settlement: Settlement) -> SettlementResponse:
    return SettlementResponse(
        from_participant=settlement.from_participant,
        to_participant=settlement.to_participant,
        amount=str(settlement.amount),
    )


def settlement_period_response(period: SettlementPeriod) -> SettlementPeriodResponse:
    return SettlementPeriodResponse(
        settlement_period_id=period.id,
        name=period.name,
        status=period.status,
        date_from=period.date_from,
        date_to=period.date_to,
        closed_at=period.closed_at,
        reopened_at=period.reopened_at,
        purchase_ids=list(period.purchase_ids),
        total_amount=str(period.total_amount),
        transfer_count=len(period.settlements),
    )


def report_result_response(result: ReportResult) -> ReportResultResponse:
    return ReportResultResponse(
        report_id=result.report_id,
        report_type=result.report_type,
        formats=sorted(result.formats),
        files=[report_file_response(file) for file in result.files],
        created_at=result.created_at,
        expires_at=result.expires_at,
        storage_backend=result.storage_backend,
        telegram_caption=result.telegram_caption,
        warnings=list(result.warnings),
        metadata=dict(result.metadata),
    )


def report_file_response(file: ReportFile) -> ReportFileResponse:
    return ReportFileResponse(
        format=file.format,
        filename=file.filename,
        content_type=file.content_type,
        size_bytes=file.size_bytes,
        storage_key=file.storage_key,
        local_path=_path_to_str(file.local_path),
        checksum_sha256=file.checksum_sha256,
    )


def _path_to_str(path: Path | None) -> str | None:
    return str(path) if path is not None else None
