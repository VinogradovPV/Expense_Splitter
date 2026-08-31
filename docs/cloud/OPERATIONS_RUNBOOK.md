# Operations Runbook — Expense Splitter Cloud MVP

Дата: 2026-07-01
Статус: runbook draft for CLOUD.8; no live cloud deployment yet.

## Principles

- Do not commit secrets, service account keys, tokens or `.env`.
- Use Yandex Lockbox or runtime environment for secrets.
- Do not run destructive database commands without backup and explicit approval.
- Keep YAML desktop/offline mode separate from cloud PostgreSQL mode.
- Treat reports as temporary artifacts with retention policy.

## Local container smoke

Build:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\cloud\docker-build.ps1
```

Run:

```powershell
docker compose up --build backend
```

Smoke:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\cloud\smoke-local.ps1
```

Expected checks:

- `/health` returns `ok = true`;
- `/health/reporting` returns ReportLab/openpyxl availability;
- current PDF report request returns a report result;
- current XLSX report request returns a report result.

## Environment validation

Check only key presence; script does not print values:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\cloud\check-env.ps1 -EnvFile .env
```

If this fails, fix runtime secret injection. Do not commit `.env`.

## Health endpoints

- `GET /health`
- `GET /health/reporting`

`/health/reporting` is the container PDF/XLSX readiness baseline. It must stay green before
enabling Telegram report delivery.

## Database operations

Before production rollout:

1. Confirm Managed PostgreSQL automated backups are enabled.
2. Create least-privilege app user.
3. Store `DATABASE_URL` in Lockbox/env secrets.
4. Apply migrations in controlled release step.
5. Run read/write smoke through repository/service layer.

Known CLOUD.8 limitation: live PostgreSQL repository execution is still pending. The
schema and migrations exist, but application write/read operations through PostgreSQL are
not production-ready yet.

## Object Storage operations

Before production rollout:

1. Create private bucket.
2. Enable lifecycle retention for reports.
3. Store bucket name and credentials outside Git.
4. Verify upload/download of a test report.
5. Confirm Telegram sends the file and does not persist file bytes in bot session.

Known CLOUD.8 limitation: Object Storage adapter currently returns stable storage keys but
does not upload bytes to Yandex Object Storage.

## Telegram operations

Before production rollout:

1. Store bot token in Lockbox/env secrets.
2. Store webhook secret in Lockbox/env secrets.
3. Validate webhook secret on inbound requests.
4. Do not log full Telegram updates.
5. Resolve `telegram_user_id -> user_id -> tenant_id -> participant_id`.

Known CLOUD.8 limitation: Telegram bot MVP is framework-neutral. Real webhook/long polling
wiring is future work.

## Rollback

If deployment fails before data migration:

- stop new container;
- restart previous image;
- keep database untouched.

If deployment fails after migration:

- stop new writes;
- inspect migration logs;
- restore from latest managed backup only after explicit approval;
- preserve failed container logs for incident review.

## Incident checklist

- Capture UTC timestamp and deployment version.
- Check `/health` and `/health/reporting`.
- Check container restart count.
- Check database connectivity.
- Check Object Storage access.
- Check recent error logs.
- Confirm no secrets were printed in logs.

## Next hardening

- live PostgreSQL repository;
- real Object Storage upload adapter;
- Telegram webhook endpoint;
- auth and tenant isolation;
- rate limits;
- audit log persistence;
- backup/restore drill.

## CLOUD.9 gate result

Current gate decision:

```text
not cloud ready — blockers
```

See `docs/cloud/PRODUCTION_HARDENING_GATE.md` for blockers and the next hardening stages.
