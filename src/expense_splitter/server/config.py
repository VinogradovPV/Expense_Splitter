"""Backend settings loaded from environment or tests."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping

RepositoryBackend = Literal["yaml", "postgres"]
ReportStorageBackend = Literal["local", "temp", "object_storage"]


@dataclass(frozen=True)
class ServerSettings:
    data_dir: Path = Path("data")
    reports_dir: Path = Path("reports/server")
    default_tenant_id: str = "local"
    repository_backend: RepositoryBackend = "yaml"
    report_storage_backend: ReportStorageBackend = "temp"
    object_storage_bucket: str | None = None
    object_storage_prefix: str = "reports"
    database_url: str | None = None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "ServerSettings":
        values = os.environ if env is None else env
        return cls(
            data_dir=Path(values.get("EXPENSE_SPLITTER_DATA_DIR", "data")),
            reports_dir=Path(values.get("EXPENSE_SPLITTER_REPORTS_DIR", "reports/server")),
            default_tenant_id=values.get("EXPENSE_SPLITTER_TENANT_ID", "local"),
            repository_backend=_repository_backend(
                values.get("EXPENSE_SPLITTER_REPOSITORY", "yaml")
            ),
            report_storage_backend=_report_storage_backend(
                values.get("EXPENSE_SPLITTER_REPORT_STORAGE", "temp")
            ),
            object_storage_bucket=values.get("YANDEX_OBJECT_STORAGE_BUCKET"),
            object_storage_prefix=values.get("EXPENSE_SPLITTER_OBJECT_PREFIX", "reports"),
            database_url=values.get("DATABASE_URL"),
        )


def _repository_backend(value: str) -> RepositoryBackend:
    if value not in {"yaml", "postgres"}:
        raise ValueError("EXPENSE_SPLITTER_REPOSITORY must be yaml or postgres.")
    return value  # type: ignore[return-value]


def _report_storage_backend(value: str) -> ReportStorageBackend:
    if value not in {"local", "temp", "object_storage"}:
        raise ValueError(
            "EXPENSE_SPLITTER_REPORT_STORAGE must be local, temp, or object_storage."
        )
    return value  # type: ignore[return-value]
