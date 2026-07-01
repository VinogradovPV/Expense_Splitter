"""PostgreSQL connection settings for future server adapters."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class PostgresSettings:
    database_url: str
    pool_size: int = 5
    pool_timeout_seconds: int = 30

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "PostgresSettings":
        values = os.environ if env is None else env
        database_url = values.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL is required for PostgreSQL mode.")
        return cls(
            database_url=database_url,
            pool_size=int(values.get("DATABASE_POOL_SIZE", "5")),
            pool_timeout_seconds=int(values.get("DATABASE_POOL_TIMEOUT_SECONDS", "30")),
        )

    @property
    def safe_database_url(self) -> str:
        if "://" not in self.database_url or "@" not in self.database_url:
            return self.database_url
        scheme, rest = self.database_url.split("://", 1)
        return f"{scheme}://***:***@{rest.split('@', 1)[1]}"


def planned_cloud_dependencies() -> tuple[str, ...]:
    return ("SQLAlchemy 2.x", "Alembic", "psycopg")
