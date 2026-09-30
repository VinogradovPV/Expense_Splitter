"""Settlement period endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from expense_splitter.repositories.protocols import ClosePeriodCommand
from expense_splitter.server.dependencies import (
    get_repository,
    get_settlement_service,
    get_tenant_id,
)
from expense_splitter.server.schemas import (
    ClosePeriodRequest,
    SettlementPeriodListResponse,
    SettlementPeriodResponse,
    settlement_period_response,
)
from expense_splitter.services import SettlementService

router = APIRouter(prefix="/api", tags=["settlement-periods"])


@router.get("/settlement-periods", response_model=SettlementPeriodListResponse)
def list_settlement_periods(
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    repository=Depends(get_repository),
) -> SettlementPeriodListResponse:
    return SettlementPeriodListResponse(
        items=[
            settlement_period_response(period)
            for period in repository.list_periods(tenant_id)
        ]
    )


@router.post("/settlement-periods/close", response_model=SettlementPeriodResponse)
def close_settlement_period(
    payload: ClosePeriodRequest,
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    service: Annotated[SettlementService, Depends(get_settlement_service)],
) -> SettlementPeriodResponse:
    period = service.close_period(
        tenant_id,
        ClosePeriodCommand(
            date_from=payload.date_from,
            date_to=payload.date_to,
            name=payload.name,
            created_by=payload.created_by,
        ),
    )
    return settlement_period_response(period)


@router.post(
    "/settlement-periods/{settlement_period_id}/reopen",
    response_model=SettlementPeriodResponse,
)
def reopen_settlement_period(
    settlement_period_id: str,
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    service: Annotated[SettlementService, Depends(get_settlement_service)],
) -> SettlementPeriodResponse:
    return settlement_period_response(service.reopen_period(tenant_id, settlement_period_id))
