"""DTOs returned by report delivery services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class ReportFile:
    format: str
    filename: str
    content_type: str
    size_bytes: int | None
    storage_key: str | None
    local_path: Path | None
    checksum_sha256: str | None


@dataclass(frozen=True)
class ReportResult:
    report_id: str
    report_type: str
    formats: set[str]
    files: list[ReportFile]
    created_at: datetime
    expires_at: datetime | None
    storage_backend: str
    telegram_caption: str
    warnings: list[dict[str, object]]
    metadata: dict[str, object]
