"""Schema metadata for the PostgreSQL cloud model.

This module intentionally avoids importing SQLAlchemy. CLOUD.5 defines the stable relational
contract and SQL migration while keeping the default desktop installation dependency-light.
"""

from __future__ import annotations

from dataclasses import dataclass

SCHEMA_VERSION = "0001_initial"
STABLE_ID_STRATEGY = "uuid"


@dataclass(frozen=True)
class TableSpec:
    name: str
    primary_key: str
    tenant_scoped: bool
    columns: tuple[str, ...]
    foreign_keys: tuple[str, ...] = ()


TABLES: tuple[TableSpec, ...] = (
    TableSpec(
        name="tenants",
        primary_key="tenant_id",
        tenant_scoped=False,
        columns=(
            "tenant_id",
            "name",
            "status",
            "default_currency",
            "created_at",
            "updated_at",
        ),
    ),
    TableSpec(
        name="users",
        primary_key="user_id",
        tenant_scoped=False,
        columns=("user_id", "display_name", "status", "created_at", "updated_at"),
    ),
    TableSpec(
        name="telegram_accounts",
        primary_key="telegram_account_id",
        tenant_scoped=False,
        columns=(
            "telegram_account_id",
            "telegram_user_id",
            "user_id",
            "username",
            "first_name",
            "last_name",
            "language_code",
            "created_at",
            "last_seen_at",
        ),
        foreign_keys=("user_id",),
    ),
    TableSpec(
        name="participants",
        primary_key="participant_id",
        tenant_scoped=True,
        columns=(
            "participant_id",
            "tenant_id",
            "linked_user_id",
            "display_name",
            "normalized_display_name",
            "status",
            "legacy_name",
            "created_at",
            "updated_at",
        ),
        foreign_keys=("tenant_id", "linked_user_id"),
    ),
    TableSpec(
        name="participant_aliases",
        primary_key="participant_alias_id",
        tenant_scoped=True,
        columns=(
            "participant_alias_id",
            "tenant_id",
            "participant_id",
            "alias",
            "normalized_alias",
            "created_at",
        ),
        foreign_keys=("tenant_id", "participant_id"),
    ),
    TableSpec(
        name="categories",
        primary_key="category_id",
        tenant_scoped=True,
        columns=(
            "category_id",
            "tenant_id",
            "display_name",
            "normalized_display_name",
            "status",
            "legacy_name",
            "created_at",
            "updated_at",
        ),
        foreign_keys=("tenant_id",),
    ),
    TableSpec(
        name="purchases",
        primary_key="purchase_id",
        tenant_scoped=True,
        columns=(
            "purchase_id",
            "tenant_id",
            "purchase_date",
            "purchase_name",
            "amount",
            "currency",
            "payer_participant_id",
            "payer_display_name_snapshot",
            "category_id",
            "category_display_name_snapshot",
            "comment",
            "status",
            "settlement_period_id",
            "legacy_id",
            "created_by_user_id",
            "created_at",
            "updated_at",
        ),
        foreign_keys=(
            "tenant_id",
            "payer_participant_id",
            "category_id",
            "settlement_period_id",
            "created_by_user_id",
        ),
    ),
    TableSpec(
        name="purchase_participants",
        primary_key="purchase_participant_id",
        tenant_scoped=True,
        columns=(
            "purchase_participant_id",
            "tenant_id",
            "purchase_id",
            "participant_id",
            "participant_display_name_snapshot",
            "share_amount",
            "created_at",
        ),
        foreign_keys=("tenant_id", "purchase_id", "participant_id"),
    ),
    TableSpec(
        name="settlement_periods",
        primary_key="settlement_period_id",
        tenant_scoped=True,
        columns=(
            "settlement_period_id",
            "tenant_id",
            "period_code",
            "name",
            "status",
            "date_from",
            "date_to",
            "closed_at",
            "reopened_at",
            "total_amount",
            "currency",
            "settlements_snapshot",
            "balances_snapshot",
            "created_by_user_id",
            "notes",
            "created_at",
            "updated_at",
        ),
        foreign_keys=("tenant_id", "created_by_user_id"),
    ),
    TableSpec(
        name="settlement_period_purchases",
        primary_key="settlement_period_purchase_id",
        tenant_scoped=True,
        columns=(
            "settlement_period_purchase_id",
            "tenant_id",
            "settlement_period_id",
            "purchase_id",
            "purchase_name_snapshot",
            "amount_snapshot",
            "payer_display_name_snapshot",
            "category_display_name_snapshot",
            "created_at",
        ),
        foreign_keys=("tenant_id", "settlement_period_id", "purchase_id"),
    ),
    TableSpec(
        name="reports",
        primary_key="report_id",
        tenant_scoped=True,
        columns=(
            "report_id",
            "tenant_id",
            "report_type",
            "report_scope",
            "settlement_period_id",
            "period_kind",
            "period_id",
            "formats",
            "storage_backend",
            "storage_key_prefix",
            "metadata",
            "warnings",
            "created_by_user_id",
            "created_at",
            "expires_at",
        ),
        foreign_keys=("tenant_id", "settlement_period_id", "created_by_user_id"),
    ),
    TableSpec(
        name="audit_log",
        primary_key="audit_log_id",
        tenant_scoped=True,
        columns=(
            "audit_log_id",
            "tenant_id",
            "actor_user_id",
            "action",
            "entity_type",
            "entity_id",
            "before_data",
            "after_data",
            "metadata",
            "created_at",
        ),
        foreign_keys=("tenant_id", "actor_user_id"),
    ),
    TableSpec(
        name="bot_sessions",
        primary_key="bot_session_id",
        tenant_scoped=True,
        columns=(
            "bot_session_id",
            "tenant_id",
            "telegram_account_id",
            "state",
            "payload",
            "last_report_id",
            "created_at",
            "updated_at",
            "expires_at",
        ),
        foreign_keys=("tenant_id", "telegram_account_id", "last_report_id"),
    ),
)

MVP_TABLES = tuple(table.name for table in TABLES)
DOMAIN_TABLES = tuple(table.name for table in TABLES if table.tenant_scoped)


def table_by_name(name: str) -> TableSpec:
    for table in TABLES:
        if table.name == name:
            return table
    raise KeyError(f"Unknown table: {name}")
