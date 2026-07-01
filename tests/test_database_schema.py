from pathlib import Path

from expense_splitter.db.models import (
    DOMAIN_TABLES,
    MVP_TABLES,
    SCHEMA_VERSION,
    STABLE_ID_STRATEGY,
    TABLES,
    table_by_name,
)
from expense_splitter.db.session import PostgresSettings, planned_cloud_dependencies

MIGRATION_PATH = Path("src/expense_splitter/db/migrations/0001_initial.sql")


def test_database_schema_declares_required_mvp_tables():
    assert SCHEMA_VERSION == "0001_initial"
    assert STABLE_ID_STRATEGY == "uuid"
    assert set(MVP_TABLES) == {
        "tenants",
        "users",
        "telegram_accounts",
        "participants",
        "participant_aliases",
        "categories",
        "purchases",
        "purchase_participants",
        "settlement_periods",
        "settlement_period_purchases",
        "reports",
        "audit_log",
        "bot_sessions",
    }


def test_domain_tables_are_tenant_scoped_and_do_not_use_display_name_as_pk():
    for table_name in DOMAIN_TABLES:
        table = table_by_name(table_name)
        assert table.tenant_scoped is True
        assert "tenant_id" in table.columns
        assert table.primary_key.endswith("_id")
        assert table.primary_key not in {"name", "display_name", "normalized_display_name"}


def test_identity_tables_keep_telegram_user_separate_from_participant():
    telegram_accounts = table_by_name("telegram_accounts")
    participants = table_by_name("participants")

    assert telegram_accounts.primary_key == "telegram_account_id"
    assert "telegram_user_id" in telegram_accounts.columns
    assert "user_id" in telegram_accounts.foreign_keys
    assert participants.primary_key == "participant_id"
    assert "linked_user_id" in participants.columns


def test_initial_postgres_migration_contains_schema_contract():
    sql = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "CREATE EXTENSION IF NOT EXISTS pgcrypto" in sql
    for table in TABLES:
        assert f"CREATE TABLE IF NOT EXISTS {table.name}" in sql
        assert f"{table.primary_key} uuid PRIMARY KEY DEFAULT gen_random_uuid()" in sql
        if table.tenant_scoped:
            assert "tenant_id uuid NOT NULL REFERENCES tenants(tenant_id)" in sql

    assert "settlements_snapshot jsonb" in sql
    assert "balances_snapshot jsonb" in sql
    assert "purchase_name_snapshot text NOT NULL" in sql
    assert "storage_backend text NOT NULL" in sql
    assert "metadata jsonb NOT NULL DEFAULT '{}'::jsonb" in sql
    assert "audit_log" in sql


def test_cloud_dependencies_are_optional_and_documented():
    assert planned_cloud_dependencies() == ("SQLAlchemy 2.x", "Alembic", "psycopg")


def test_postgres_settings_reads_env_without_exposing_password():
    settings = PostgresSettings.from_env(
        {
            "DATABASE_URL": "postgresql+psycopg://user:secret@localhost:5432/expense",
            "DATABASE_POOL_SIZE": "10",
            "DATABASE_POOL_TIMEOUT_SECONDS": "15",
        }
    )

    assert settings.pool_size == 10
    assert settings.pool_timeout_seconds == 15
    assert settings.safe_database_url == "postgresql+psycopg://***:***@localhost:5432/expense"
