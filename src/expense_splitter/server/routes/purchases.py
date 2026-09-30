"""Purchase, balance, and settlement endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from expense_splitter.repositories.protocols import AddPurchaseCommand
from expense_splitter.server.dependencies import (
    get_purchase_service,
    get_repository,
    get_settlement_service,
    get_tenant_id,
)
from expense_splitter.server.schemas import (
    BalanceListResponse,
    PurchaseCreateRequest,
    PurchaseListResponse,
    PurchaseResponse,
    SettlementListResponse,
    balance_response,
    purchase_response,
    settlement_response,
)
from expense_splitter.services import PurchaseService, SettlementService

router = APIRouter(prefix="/api", tags=["purchases"])


@router.get("/purchases", response_model=PurchaseListResponse)
def list_purchases(
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    repository=Depends(get_repository),
) -> PurchaseListResponse:
    return PurchaseListResponse(
        items=[purchase_response(purchase) for purchase in repository.list_purchases(tenant_id)]
    )


@router.post(
    "/purchases",
    response_model=PurchaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_purchase(
    request: PurchaseCreateRequest,
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    service: Annotated[PurchaseService, Depends(get_purchase_service)],
) -> PurchaseResponse:
    purchase = service.add_purchase(
        tenant_id,
        AddPurchaseCommand(
            purchase_name=request.purchase_name,
            amount=request.amount,
            payer=request.payer,
            participants=request.participants,
            purchase_date=request.purchase_date,
            category=request.category,
            comment=request.comment,
        ),
    )
    return purchase_response(purchase)


@router.get("/balances", response_model=BalanceListResponse)
def balances(
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    service: Annotated[SettlementService, Depends(get_settlement_service)],
    scope: str = "open",
) -> BalanceListResponse:
    return BalanceListResponse(
        items=[balance_response(balance) for balance in service.balances(tenant_id, scope=scope)]
    )


@router.get("/settlements", response_model=SettlementListResponse)
def settlements(
    tenant_id: Annotated[str, Depends(get_tenant_id)],
    service: Annotated[SettlementService, Depends(get_settlement_service)],
    scope: str = "open",
) -> SettlementListResponse:
    return SettlementListResponse(
        items=[
            settlement_response(settlement)
            for settlement in service.settlements(tenant_id, scope=scope)
        ]
    )
