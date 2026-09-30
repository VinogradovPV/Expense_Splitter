# TG-PREP.6 — Report Delivery Contract

Дата: 2026-07-01
Ветка: `cloud/telegram-prep`
Статус: delivery contract plan; код report service и Telegram bot пока не создавался.

## Цель

Подготовить единый контракт генерации и доставки отчетов, чтобы Telegram bot мог запросить PDF/XLSX
без знания внутренних деталей: где лежат CSV, как создаются charts, как называются локальные папки
`reports/`, какой writer строит XLSX/PDF и куда потом складываются artifacts.

Telegram должен знать только:

- какой отчет нужен;
- какие форматы нужны;
- какой файл отправить пользователю через `sendDocument`;
- какой caption показать.

## Supported Report Scenarios

### Current Settlement State

Пользовательский смысл: "что сейчас открыто к взаиморасчетам".

Текущие CLI аналоги:

```powershell
expense-splitter current-report --scope open --format pdf
expense-splitter current-report --scope open --format xlsx
```

Future service call:

```python
result = report_service.create_current_report(
    tenant_id=tenant_id,
    scope="open",
    formats={"pdf", "xlsx"},
)
```

Требования:

- не закрывает период;
- не меняет purchases/periods/categories/participants;
- использует текущие open purchases;
- может поддержать `scope="all"` для admin/desktop use, но Telegram MVP должен начинать с
  `scope="open"`.

### Analytics Period Report

Пользовательский смысл: "расходы за календарный месяц/квартал/год".

Текущие CLI аналоги:

```powershell
expense-splitter analytics --period month --year 2026 --month 6 --format pdf
expense-splitter analytics --period month --year 2026 --month 6 --format xlsx

expense-splitter analytics --period quarter --year 2026 --quarter 2 --format pdf
expense-splitter analytics --period quarter --year 2026 --quarter 2 --format xlsx

expense-splitter analytics --period year --year 2026 --format pdf
expense-splitter analytics --period year --year 2026 --format xlsx
```

Future service call:

```python
result = report_service.create_analytics_report(
    tenant_id=tenant_id,
    period=PeriodSpec(kind="month", year=2026, month=6),
    formats={"pdf", "xlsx"},
)
```

Требования:

- не меняет данные;
- использует purchases выбранного tenant-а;
- умеет возвращать warnings для пустого периода или undated purchases;
- поддерживает PDF/XLSX как Telegram-first formats, но backend может генерировать промежуточные
  CSV/PNG/metadata внутри workspace.

### Historical Settlement Period Report

Пользовательский смысл: "что было зафиксировано при закрытии конкретного периода".

Текущие CLI аналоги:

```powershell
expense-splitter settlement-period report <settlement_period_id> --format pdf
expense-splitter settlement-period report <settlement_period_id> --format xlsx
```

Future service call:

```python
result = report_service.create_settlement_period_report(
    tenant_id=tenant_id,
    period_id=settlement_period_id,
    formats={"pdf", "xlsx"},
)
```

Требования:

- historical report использует snapshot settlement period;
- snapshot settlements не пересчитываются;
- если period был reopened, это warning/caption fact, а не повод менять историю;
- если часть purchase details догружается из текущих records, это должно быть отражено в metadata и
  warnings.

## Service API

Минимальный будущий API:

```python
class ReportService:
    def create_current_report(
        self,
        tenant_id: str,
        scope: str,
        formats: set[str],
    ) -> ReportResult: ...

    def create_analytics_report(
        self,
        tenant_id: str,
        period: PeriodSpec,
        formats: set[str],
    ) -> ReportResult: ...

    def create_settlement_period_report(
        self,
        tenant_id: str,
        period_id: str,
        formats: set[str],
    ) -> ReportResult: ...
```

Allowed `formats` for Telegram MVP:

- `{"pdf"}`
- `{"xlsx"}`
- `{"pdf", "xlsx"}`

Backend may support additional formats (`markdown`, `csv`, `png`, `html`, `all`) for desktop/admin,
but Telegram contract should prefer PDF/XLSX.

## ReportResult

`ReportResult` is the only object Telegram bot should need after requesting a report.

```python
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
```

Required fields from the prompt:

- `report_id`
- `report_type`
- `formats`
- `files`
- `created_at`
- `expires_at`
- `storage_backend`
- `telegram_caption`

Recommended additional fields:

- `warnings`
- `metadata`

### ReportFile

```python
@dataclass(frozen=True)
class ReportFile:
    format: str
    filename: str
    content_type: str
    size_bytes: int | None
    storage_key: str | None
    local_path: Path | None
    checksum_sha256: str | None
```

Rules:

- `local_path` may exist in desktop/local adapter.
- `storage_key` must exist in cloud adapter.
- Telegram should not persist file bytes in bot session.
- Files must have user-facing filenames in Russian or stable transliterated names.

## Storage Backends

### Local Desktop Backend

`storage_backend = "local"`

Use cases:

- current desktop GUI;
- CLI;
- tests;
- local smoke.

Behavior:

- writes to current `reports/...` structure;
- returns `local_path`;
- no Object Storage upload required.

### Temporary Workspace Backend

`storage_backend = "temp"`

Use cases:

- backend job before publish;
- integration tests;
- server-side generation before upload.

Behavior:

- generates report into temp dir;
- temp dir can include internal CSV/PNG/metadata;
- publish step decides what to keep.

### Object Storage Backend

`storage_backend = "object_storage"`

Use cases:

- Telegram/FastAPI/Yandex Cloud.

Behavior:

- report generation may happen in temp dir;
- final PDF/XLSX and optional metadata are uploaded to Object Storage;
- `ReportFile.storage_key` points to object key;
- `expires_at` should reflect retention policy or signed URL expiration;
- bot downloads/streams file for `sendDocument` and does not become permanent storage.

Suggested object key shape:

```text
reports/{tenant_id}/{report_type}/{report_id}/{filename}
```

## Telegram Delivery

Telegram bot flow:

1. Resolve `telegram_user_id -> user_id -> tenant_id/participant_id`.
2. Call `ReportService`.
3. For each `ReportFile` in `result.files`:
   - get file stream from `local_path` or `storage_key`;
   - call Telegram `sendDocument`;
   - use `result.telegram_caption` or format-specific caption.
4. Save only `report_id` and short status in `bot_sessions` if needed.

Telegram must not:

- know internal paths like `reports/current_state/...`;
- parse CSV tables;
- generate PDF/XLSX itself;
- store permanent report files in bot state;
- recalculate settlements.

## Telegram Captions

Caption should be short, stable and useful:

Current report:

```text
Текущие взаиморасчеты: открытые покупки. PDF/XLSX сформирован, данные не изменялись.
```

Analytics:

```text
Отчет за июнь 2026. PDF/XLSX сформирован, данные не изменялись.
```

Settlement period:

```text
Исторический отчет по периоду settlement_2026_06_30_001. Использован snapshot периода.
```

If reopened:

```text
Период был переоткрыт. Отчет показывает сохраненный snapshot периода.
```

## Non-Mutation Requirements

All report service methods are read-only domain operations.

Must not:

- add/edit/delete purchases;
- close/reopen settlement periods;
- mutate YAML or DB records except `reports` metadata/audit entries;
- rewrite historical settlement snapshots;
- mark purchases as settled/open.

Allowed side effects:

- create temp files;
- create local report artifacts in desktop mode;
- upload report artifacts in cloud mode;
- create `reports` row/status;
- append `audit_log` event `report.generated` or `report.failed`.

## Historical Snapshot Policy

For settlement period report:

1. Use snapshot settlements from `settlement_periods`.
2. Do not recalculate settlements if snapshot settlements exist.
3. Use snapshot total amount and purchase IDs.
4. If purchase display details are not in snapshot and must be restored from current records, add
   warning and metadata source flag.
5. If current purchase is missing, generate warning instead of failing the whole report.

Metadata example:

```json
{
  "settlement_source": "snapshot",
  "balance_source": "recomputed_from_period_purchases",
  "purchase_details_source": "current_records",
  "historical_accuracy_warning": true
}
```

## PDF Font Requirement

PDF generation must use an available Cyrillic-capable font in server environment.

Options:

1. Package a known font with the application/container.
2. Install font package in image.
3. Configure `REPORT_PDF_FONT_PATH`.

Server startup or report worker healthcheck should verify font availability before accepting PDF
jobs. If PDF font is missing:

- return structured error;
- optionally still generate XLSX;
- record `report.failed` audit event for PDF format.

## Error Contract

Report service should raise or return structured errors that Telegram can convert into a friendly
message.

Examples:

- `REPORT_PERIOD_NOT_FOUND`
- `REPORT_UNSUPPORTED_FORMAT`
- `REPORT_EMPTY_DATASET`
- `REPORT_PDF_FONT_MISSING`
- `REPORT_STORAGE_UPLOAD_FAILED`
- `REPORT_GENERATION_FAILED`

Telegram user messages should not expose stack traces or local filesystem paths.

## Audit Log

For each report request:

Success:

```json
{
  "event_type": "report.generated",
  "entity_type": "report",
  "entity_id": "<report_id>",
  "metadata_json": {
    "report_type": "current",
    "formats": ["pdf", "xlsx"],
    "storage_backend": "object_storage"
  }
}
```

Failure:

```json
{
  "event_type": "report.failed",
  "entity_type": "report",
  "entity_id": "<report_id>",
  "metadata_json": {
    "error_code": "REPORT_PDF_FONT_MISSING",
    "formats": ["pdf"]
  }
}
```

## Implementation Notes

Current modules already have useful split points:

- `build_current_report_dataset` can become read-side service logic.
- `generate_current_report` can be wrapped by a local/temp output adapter.
- `build_analytics_dataset` is reusable after repository load.
- `generate_analytics_report` can write into a workspace.
- `build_settlement_period_report_dataset` preserves historical snapshot policy.
- PDF/XLSX writers can stay file-based internally as long as the service controls workspace and
  publishing.

Do not force Telegram to call CLI commands. CLI remains an adapter; Telegram should call
`ReportService` directly.

## Decision

Report delivery for Telegram should be service-driven:

- domain data loaded by repositories;
- dataset built by report service;
- artifacts generated in controlled workspace;
- cloud artifacts published to Object Storage;
- Telegram sends documents via `sendDocument`;
- bot stores only lightweight session/status, never permanent report files.
