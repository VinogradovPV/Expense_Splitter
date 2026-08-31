"""Repository contracts for future storage adapters."""

from expense_splitter.repositories.postgres_repository import (
    PostgresExpenseRepository,
    PostgresRepositoryConfig,
    PostgresRepositoryNotImplementedError,
)
from expense_splitter.repositories.protocols import (
    AddPurchaseCommand,
    CategoryRepository,
    ClosePeriodCommand,
    ExpenseUnitOfWork,
    ParticipantRepository,
    PurchasePatch,
    PurchaseRepository,
    ReportRequest,
    SettlementPeriodRepository,
)
from expense_splitter.repositories.yaml_repository import (
    LOCAL_TENANT_ID,
    YamlExpenseRepository,
    YamlRepositoryTenantError,
)

__all__ = [
    "AddPurchaseCommand",
    "CategoryRepository",
    "ClosePeriodCommand",
    "ExpenseUnitOfWork",
    "LOCAL_TENANT_ID",
    "ParticipantRepository",
    "PostgresExpenseRepository",
    "PostgresRepositoryConfig",
    "PostgresRepositoryNotImplementedError",
    "PurchasePatch",
    "PurchaseRepository",
    "ReportRequest",
    "SettlementPeriodRepository",
    "YamlExpenseRepository",
    "YamlRepositoryTenantError",
]
