# CLOUD.9 — Production Hardening and Release Gate

Дата: 2026-07-01
Статус: completed as release gate assessment.

## Decision

```text
not cloud ready — blockers
```

Cloud architecture, service boundaries, FastAPI MVP, Telegram bot MVP and deployment package
are prepared, but production cloud release is blocked by missing live infrastructure
execution pieces.

## Completed hardening

- FastAPI exposes structured error responses without tracebacks.
- Telegram webhook endpoint exists as a stub and validates
  `X-Telegram-Bot-Api-Secret-Token` against `TELEGRAM_WEBHOOK_SECRET`.
- Server security headers are configured:
  - `X-Content-Type-Options: nosniff`;
  - `X-Frame-Options: DENY`;
  - `Referrer-Policy: no-referrer`;
  - `Cache-Control: no-store`.
- `DATABASE_URL` and object storage bucket values have masking helpers for diagnostics.
- `.env`, service account keys and token files are ignored.
- Deployment package avoids committing generated reports and user `data/*.yaml`.
- Telegram bot mutating commands use exact confirmation markers for delete/close actions.

## Gate checks

Required checks for this gate:

- unit tests;
- integration/service tests;
- API tests;
- Telegram flow tests;
- cloud deployment asset tests;
- DB migration contract tests;
- encoding/mojibake check;
- Ruff;
- compileall;
- `git diff --check`;
- generated artifacts not staged.

Secret grep result:

- no real Telegram/Yandex tokens found;
- no service account key files found;
- matches are expected env variable names, docs/prompts, `.env.example` placeholders,
  `change_me_local_only` compose values and test-only sample URLs.

Manual or future checks:

- Docker build and container smoke;
- live PostgreSQL read/write smoke;
- Object Storage upload/download smoke;
- Telegram webhook live dry-run with real secret from Lockbox;
- backup/restore drill against Managed PostgreSQL;
- user acceptance smoke.

## Blockers

### B1 — Live PostgreSQL repository execution

CLOUD.5 added schema/migrations and repository contract, but
`PostgresExpenseRepository` still fails explicitly. Production cloud mode needs live
list/add/update/delete purchases, directories, settlement periods and report queries.

### B2 — Object Storage upload adapter

Current Object Storage adapter returns stable storage keys but does not upload report bytes
to Yandex Object Storage. Production report delivery requires upload, download verification,
lifecycle retention and least-privilege service account permissions.

### B3 — Telegram identity and webhook runner

CLOUD.7 added framework-neutral bot handler. Production requires:

- webhook endpoint wired to handler;
- `telegram_user_id -> user_id -> tenant_id -> participant_id` resolution;
- admin role checks for settlement period closing;
- no full Telegram update logging.

### B4 — Audit log persistence

Audit events are documented, but production requires persisted records for:

- purchase added/edited/deleted;
- settlement period closed/reopened;
- directory changes;
- report generated/failed;
- auth/security events.

### B5 — Rate limiting enforcement

`EXPENSE_SPLITTER_RATE_LIMIT_PER_MINUTE` is present in settings, but request throttling is not
enforced yet. Production webhook/API endpoints need per-user or per-tenant rate limits.

### B6 — Backup/restore drill

Managed PostgreSQL backup strategy is documented. Production gate requires an actual
backup/restore drill in the target environment before go-live.

## Release status by component

| Component | Status | Notes |
| --- | --- | --- |
| Domain models/calculations | ready for reuse | storage-independent enough for service layer |
| YAML offline mode | ready | must remain supported |
| Repository protocols | ready | stable boundary exists |
| YAML repository | ready for local/offline | not a cloud multi-user backend |
| PostgreSQL schema | ready as contract | live adapter blocked |
| FastAPI backend | MVP ready | needs auth/rate limits/live DB |
| Telegram bot | MVP handler ready | needs webhook runner and identity |
| ReportService | MVP ready | needs real object storage upload |
| Deployment package | MVP prepared | Docker build/smoke must be run manually |
| Security model | documented plus partial code hardening | enforcement incomplete |

## Next stage

Recommended next stage:

```text
CLOUD.9.1 — live PostgreSQL repository and migration dry-run
```

After that:

1. `CLOUD.9.2 — Object Storage upload adapter`
2. `CLOUD.9.3 — Telegram webhook wiring and identity resolution`
3. `CLOUD.9.4 — audit log and rate limiting`
4. `CLOUD.9.5 — cloud smoke, backup/restore drill and release decision`
