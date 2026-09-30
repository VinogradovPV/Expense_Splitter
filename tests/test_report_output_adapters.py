import json
from datetime import datetime, timedelta, timezone

from expense_splitter.reports.output_adapters import (
    LocalReportOutputAdapter,
    ObjectStorageReportOutputAdapter,
    TempReportOutputAdapter,
    pdf_font_healthcheck,
)


def write_report_files(report_dir):
    report_dir.mkdir(parents=True)
    pdf_path = report_dir / "report.pdf"
    xlsx_path = report_dir / "report.xlsx"
    csv_path = report_dir / "tables" / "summary.csv"
    csv_path.parent.mkdir()
    pdf_path.write_bytes(b"%PDF-1.4\n")
    xlsx_path.write_bytes(b"xlsx")
    csv_path.write_text("name,value\n", encoding="utf-8")
    return pdf_path, xlsx_path, csv_path


def test_local_output_adapter_returns_delivery_files_with_checksums(tmp_path):
    report_dir = tmp_path / "reports" / "current" / "open"
    pdf_path, _, _ = write_report_files(report_dir)
    adapter = LocalReportOutputAdapter()
    created_at = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)

    result = adapter.build_result(
        tenant_id="local",
        report_type="current",
        report_id="open",
        formats={"pdf"},
        report_dir=report_dir,
        created_at=created_at,
        telegram_caption="caption",
        warnings=[],
        metadata={"source": "test"},
    )

    assert result.storage_backend == "local"
    assert result.created_at == created_at
    assert len(result.files) == 1
    assert result.files[0].filename == pdf_path.name
    assert result.files[0].content_type == "application/pdf"
    assert result.files[0].size_bytes == pdf_path.stat().st_size
    assert result.files[0].checksum_sha256 is not None
    assert result.files[0].local_path == pdf_path
    assert result.files[0].storage_key is None


def test_temp_output_adapter_allocates_workspace(tmp_path):
    adapter = TempReportOutputAdapter(base_dir=tmp_path / "workspace")

    output_root = adapter.output_root(tmp_path / "default", "analytics")

    assert output_root == tmp_path / "workspace" / "analytics"
    assert output_root.is_dir()


def test_object_storage_adapter_returns_stable_keys_without_upload(tmp_path):
    report_dir = tmp_path / "workspace" / "current" / "open"
    _, xlsx_path, _ = write_report_files(report_dir)
    adapter = ObjectStorageReportOutputAdapter(
        bucket="reports-bucket",
        key_prefix="reports",
        retention=timedelta(hours=1),
    )
    created_at = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)

    result = adapter.build_result(
        tenant_id="tenant-1",
        report_type="current",
        report_id="open",
        formats={"xlsx"},
        report_dir=report_dir,
        created_at=created_at,
        telegram_caption="caption",
        warnings=[{"code": "note"}],
        metadata={},
    )

    assert result.storage_backend == "object_storage"
    assert result.expires_at == created_at + timedelta(hours=1)
    assert result.metadata["object_storage_upload"] == "stub"
    assert result.files[0].filename == xlsx_path.name
    assert result.files[0].storage_key == "reports/tenant-1/current/open/report.xlsx"
    assert result.files[0].local_path == xlsx_path


def test_all_format_includes_internal_files_for_desktop_bundle(tmp_path):
    report_dir = tmp_path / "reports" / "current" / "open"
    write_report_files(report_dir)
    adapter = LocalReportOutputAdapter()

    result = adapter.build_result(
        tenant_id="local",
        report_type="current",
        report_id="open",
        formats={"all"},
        report_dir=report_dir,
        created_at=datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc),
        telegram_caption="caption",
        warnings=[],
        metadata={},
    )

    assert {file.filename for file in result.files} == {
        "report.pdf",
        "report.xlsx",
        "summary.csv",
    }


def test_output_adapter_uses_metadata_file_manifest_when_available(tmp_path):
    report_dir = tmp_path / "reports" / "analytics" / "2026-07"
    pdf_path, _, _ = write_report_files(report_dir)
    stale_chart = report_dir / "charts" / "period_trend.png"
    stale_chart.parent.mkdir()
    stale_chart.write_bytes(b"stale")
    (report_dir / "metadata.json").write_text(
        json.dumps({"files": ["report.pdf", "metadata.json"]}),
        encoding="utf-8",
    )
    adapter = LocalReportOutputAdapter()

    result = adapter.build_result(
        tenant_id="local",
        report_type="analytics",
        report_id="2026-07",
        formats={"all"},
        report_dir=report_dir,
        created_at=datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc),
        telegram_caption="caption",
        warnings=[],
        metadata={},
    )

    assert {file.filename for file in result.files} == {pdf_path.name, "metadata.json"}


def test_pdf_font_healthcheck_is_structured():
    health = pdf_font_healthcheck()

    assert set(health) == {"ok", "font_path"}
    assert isinstance(health["ok"], bool)
