"""PostgreSQL schema foundation for the future cloud backend."""

from expense_splitter.db.models import (
    DOMAIN_TABLES,
    MVP_TABLES,
    SCHEMA_VERSION,
    STABLE_ID_STRATEGY,
    TABLES,
    TableSpec,
)
from expense_splitter.db.session import PostgresSettings

__all__ = [
    "DOMAIN_TABLES",
    "MVP_TABLES",
    "SCHEMA_VERSION",
    "STABLE_ID_STRATEGY",
    "TABLES",
    "PostgresSettings",
    "TableSpec",
]
