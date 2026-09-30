"""FastAPI dependency factories."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Header, Request

from expense_splitter.defaults import DEFAULT_GROUPS, DEFAULT_PARTICIPANTS
from expense_splitter.reports.output_adapters import (
    LocalReportOutputAdapter,
    ObjectStorageReportOutputAdapter,
    ReportOutputAdapter,
    TempReportOutputAdapter,
)
from expense_splitter.repositories import (
    PostgresExpenseRepository,
    PostgresRepositoryConfig,
    YamlExpenseRepository,
)
from expense_splitter.repositories.protocols import (
    CategoryRepository,
    ParticipantRepository,
    PurchaseRepository,
    SettlementPeriodRepository,
)
from expense_splitter.server.config import ServerSettings
from expense_splitter.services import PurchaseService, ReportService, SettlementService
from expense_splitter.storage import initialize_data_files


@lru_cache
def get_settings() -> ServerSettings:
    return ServerSettings.from_env()


def get_tenant_id(
    request: Request,
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
) -> str:
    tenant_id = (x_tenant_id or request.app.state.settings.default_tenant_id).strip()
    if not tenant_id:
        raise ValueError("tenant_id is required.")
    return tenant_id


def get_repository(request: Request):
    return request.app.state.repository


def get_purchase_service(request: Request) -> PurchaseService:
    return request.app.state.purchase_service


def get_settlement_service(request: Request) -> SettlementService:
    return request.app.state.settlement_service


def get_report_service(request: Request) -> ReportService:
    return request.app.state.report_service


def create_repository(settings: ServerSettings):
    if settings.repository_backend == "yaml":
        initialize_data_files(settings.data_dir, DEFAULT_PARTICIPANTS, DEFAULT_GROUPS)
        return YamlExpenseRepository(settings.data_dir)
    if not settings.database_url:
        raise ValueError("DATABASE_URL is required when repository backend is postgres.")
    return PostgresExpenseRepository(PostgresRepositoryConfig(settings.database_url))


def create_report_output_adapter(settings: ServerSettings) -> ReportOutputAdapter:
    if settings.report_storage_backend == "local":
        return LocalReportOutputAdapter()
    if settings.report_storage_backend == "object_storage":
        if not settings.object_storage_bucket:
            raise ValueError(
                "YANDEX_OBJECT_STORAGE_BUCKET is required for object_storage reports."
            )
        return ObjectStorageReportOutputAdapter(
            bucket=settings.object_storage_bucket,
            key_prefix=settings.object_storage_prefix,
            base_dir=settings.reports_dir,
        )
    return TempReportOutputAdapter(base_dir=settings.reports_dir)


def create_services(settings: ServerSettings):
    repository = create_repository(settings)
    purchase_service = PurchaseService(
        _purchase_repository(repository),
        _participant_repository(repository),
    )
    settlement_service = SettlementService(
        _purchase_repository(repository),
        _participant_repository(repository),
        _settlement_period_repository(repository),
    )
    report_service = ReportService(
        _purchase_repository(repository),
        _participant_repository(repository),
        _settlement_period_repository(repository),
        output_adapter=create_report_output_adapter(settings),
    )
    return repository, purchase_service, settlement_service, report_service


def _purchase_repository(repository) -> PurchaseRepository:
    return repository


def _participant_repository(repository) -> ParticipantRepository:
    return repository


def _category_repository(repository) -> CategoryRepository:
    return repository


def _settlement_period_repository(repository) -> SettlementPeriodRepository:
    return repository
