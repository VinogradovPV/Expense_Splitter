"""Output adapters for local, temporary, and future Object Storage reports."""

from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol

from expense_splitter.report_pdf import discover_cyrillic_font
from expense_splitter.reports.result import ReportFile, ReportResult

FORMAT_SUFFIXES = {
    "markdown": {".md"},
    "csv": {".csv"},
    "png": {".png"},
    "html": {".html"},
    "xlsx": {".xlsx"},
    "pdf": {".pdf"},
}

CONTENT_TYPES = {
    ".csv": "text/csv",
    ".html": "text/html",
    ".json": "application/json",
    ".md": "text/markdown",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


class ReportOutputAdapter(Protocol):
    storage_backend: str

    def output_root(self, default_root: Path, report_type: str) -> Path: ...

    def build_result(
        self,
        *,
        tenant_id: str,
        report_type: str,
        report_id: str,
        formats: set[str],
        report_dir: Path,
        created_at: datetime,
        telegram_caption: str,
        warnings: list[dict[str, object]],
        metadata: dict[str, object],
    ) -> ReportResult: ...


class LocalReportOutputAdapter:
    """Return local report files without copying or uploading them."""

    storage_backend = "local"

    def output_root(self, default_root: Path, report_type: str) -> Path:
        return default_root

    def build_result(
        self,
        *,
        tenant_id: str,
        report_type: str,
        report_id: str,
        formats: set[str],
        report_dir: Path,
        created_at: datetime,
        telegram_caption: str,
        warnings: list[dict[str, object]],
        metadata: dict[str, object],
    ) -> ReportResult:
        files = [
            _report_file(path, formats, report_dir=report_dir)
            for path in _select_report_files(report_dir, formats)
        ]
        return ReportResult(
            report_id=report_id,
            report_type=report_type,
            formats=set(formats),
            files=files,
            created_at=created_at,
            expires_at=None,
            storage_backend=self.storage_backend,
            telegram_caption=telegram_caption,
            warnings=warnings,
            metadata={
                **_read_metadata_json(report_dir),
                **metadata,
                "tenant_id": tenant_id,
                "report_dir": str(report_dir),
            },
        )


class TempReportOutputAdapter(LocalReportOutputAdapter):
    """Generate reports under a temporary workspace for backend jobs/tests."""

    storage_backend = "temp"

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir is not None else None

    def output_root(self, default_root: Path, report_type: str) -> Path:
        if self.base_dir is not None:
            root = self.base_dir / report_type
            root.mkdir(parents=True, exist_ok=True)
            return root
        return Path(tempfile.mkdtemp(prefix=f"expense_splitter_{report_type}_"))


class ObjectStorageReportOutputAdapter(TempReportOutputAdapter):
    """Future Object Storage adapter stub.

    This adapter intentionally does not upload anything yet. It returns stable storage keys
    so FastAPI/Telegram integration can be built without adding Yandex SDK or secrets.
    """

    storage_backend = "object_storage"

    def __init__(
        self,
        bucket: str,
        key_prefix: str = "reports",
        base_dir: Path | None = None,
        retention: timedelta | None = None,
    ) -> None:
        super().__init__(base_dir=base_dir)
        self.bucket = bucket
        self.key_prefix = key_prefix.strip("/")
        self.retention = retention

    def build_result(
        self,
        *,
        tenant_id: str,
        report_type: str,
        report_id: str,
        formats: set[str],
        report_dir: Path,
        created_at: datetime,
        telegram_caption: str,
        warnings: list[dict[str, object]],
        metadata: dict[str, object],
    ) -> ReportResult:
        files = [
            _report_file(
                path,
                formats,
                report_dir=report_dir,
                storage_key=self._storage_key(tenant_id, report_type, report_id, path.name),
            )
            for path in _select_report_files(report_dir, formats)
        ]
        expires_at = created_at + self.retention if self.retention is not None else None
        return ReportResult(
            report_id=report_id,
            report_type=report_type,
            formats=set(formats),
            files=files,
            created_at=created_at,
            expires_at=expires_at,
            storage_backend=self.storage_backend,
            telegram_caption=telegram_caption,
            warnings=warnings,
            metadata={
                **_read_metadata_json(report_dir),
                **metadata,
                "tenant_id": tenant_id,
                "bucket": self.bucket,
                "object_storage_upload": "stub",
                "report_dir": str(report_dir),
            },
        )

    def _storage_key(
        self,
        tenant_id: str,
        report_type: str,
        report_id: str,
        filename: str,
    ) -> str:
        return f"{self.key_prefix}/{tenant_id}/{report_type}/{report_id}/{filename}"


def pdf_font_healthcheck() -> dict[str, object]:
    font_path = discover_cyrillic_font()
    return {
        "ok": font_path is not None,
        "font_path": str(font_path) if font_path is not None else None,
    }


def _select_report_files(report_dir: Path, formats: set[str]) -> list[Path]:
    normalized = {item.lower() for item in formats}
    files = sorted(path for path in report_dir.rglob("*") if path.is_file())
    if "all" in normalized:
        return files
    suffixes = set().union(*(FORMAT_SUFFIXES.get(item, set()) for item in normalized))
    return [path for path in files if path.suffix.lower() in suffixes]


def _report_file(
    path: Path,
    formats: set[str],
    *,
    report_dir: Path,
    storage_key: str | None = None,
) -> ReportFile:
    return ReportFile(
        format=_format_for_path(path, formats),
        filename=path.name,
        content_type=CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream"),
        size_bytes=path.stat().st_size,
        storage_key=storage_key,
        local_path=path,
        checksum_sha256=_sha256(path),
    )


def _format_for_path(path: Path, formats: set[str]) -> str:
    suffix = path.suffix.lower()
    for format_name, suffixes in FORMAT_SUFFIXES.items():
        if suffix in suffixes:
            return format_name
    if path.name == "metadata.json":
        return "metadata"
    return next(iter(sorted(formats))) if formats else "unknown"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_metadata_json(report_dir: Path) -> dict[str, object]:
    metadata_path = report_dir / "metadata.json"
    if not metadata_path.is_file():
        return {}
    try:
        return json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"metadata_read_error": str(metadata_path)}
