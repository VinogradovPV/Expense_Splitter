# CLOUD.6 — FastAPI Backend MVP

Дата: 2026-07-01
Ветка: `cloud/telegram-prep`
Статус: backend adapter MVP; Telegram bot is not implemented yet.

## Scope

CLOUD.6 adds a FastAPI adapter above the existing service/repository layers.

The backend exposes MVP endpoints for:

- health checks;
- purchases;
- balances;
- settlements;
- current reports;
- analytics reports;
- settlement periods;
- settlement-period reports;
- report download from generated local/temp files.

## Dependencies

FastAPI dependencies live in optional extra `cloud`:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,cloud]"
```

Notes for the current Python 3.14 development environment:

- `httpx` is conditional for Python `< 3.14` because the current index did not provide a
  compatible `httpcore` wheel during CLOUD.6 work;
- `uvicorn` is included without `[standard]` because `websockets` was unavailable for Python 3.14.

Server deployment can still use Python 3.11/3.12 and install the same `cloud` extra.

## App Factory

FastAPI app is created via:

```python
from expense_splitter.server import ServerSettings, create_app

app = create_app(ServerSettings.from_env())
```

For Uvicorn:

```powershell
uvicorn expense_splitter.server.app:create_app --factory
```

The module does not create an app at import time, so importing server code does not mutate local
`data/*.yaml`.

## Configuration

Environment variables:

- `EXPENSE_SPLITTER_DATA_DIR`
- `EXPENSE_SPLITTER_REPORTS_DIR`
- `EXPENSE_SPLITTER_TENANT_ID`
- `EXPENSE_SPLITTER_REPOSITORY` (`yaml` or `postgres`)
- `EXPENSE_SPLITTER_REPORT_STORAGE` (`local`, `temp`, `object_storage`)
- `YANDEX_OBJECT_STORAGE_BUCKET`
- `EXPENSE_SPLITTER_OBJECT_PREFIX`
- `DATABASE_URL`

## Repository Mode

Default backend is YAML repository for local smoke and offline compatibility.

PostgreSQL mode is configured but not executable yet: `PostgresExpenseRepository` is still a
CLOUD.5 contract stub and returns structured 501 responses through the FastAPI exception handler.
Live PostgreSQL repository implementation remains for a later cloud stage.

## Tenant Boundary

MVP tenant resolution:

- request header `X-Tenant-Id`;
- fallback to `EXPENSE_SPLITTER_TENANT_ID`;
- default value: `local`.

Every route calls services/repositories with an explicit `tenant_id`.

## Error Handling

Errors are structured and do not expose traceback:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "user-safe message",
    "request_id": "uuid"
  }
}
```

## Current Limitations

- No Telegram webhook implementation.
- No authentication/authorization yet.
- No live PostgreSQL repository execution yet.
- Report download is local/temp-file based; Object Storage upload remains a stub from CLOUD.4.
- Tests use app factory and endpoint functions directly; they do not require `httpx` on Python 3.14.
