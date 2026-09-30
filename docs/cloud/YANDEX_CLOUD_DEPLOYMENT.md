# CLOUD.8 — Yandex Cloud Deployment MVP

Дата: 2026-07-01
Статус: deployment package prepared; real cloud resources are not created.

## Цель

Подготовить безопасный MVP-путь развертывания Expense Splitter backend/bot в Yandex
Cloud без публикации секретов и без фактического deploy из репозитория.

## MVP topology

```text
Telegram
  -> FastAPI backend container
  -> service layer
  -> PostgreSQL repository
  -> Managed PostgreSQL
  -> ReportService
  -> Object Storage
  -> Telegram sendDocument
```

Для MVP выбран container/VM backend, а не serverless. Причины:

- ReportLab, matplotlib и openpyxl проще проверить в постоянном container runtime;
- PDF требует доступных кириллических шрифтов;
- healthcheck и smoke/debug проще выполнять через HTTP;
- будущий Telegram webhook и background report generation проще развивать в backend service.

Serverless остается future optimization после стабилизации PostgreSQL repository, auth,
object storage upload и report runtime.

## Созданные deployment files

- `Dockerfile`
- `.dockerignore`
- `compose.yaml`
- `scripts/cloud/README.md`
- `scripts/cloud/check-env.ps1`
- `scripts/cloud/docker-build.ps1`
- `scripts/cloud/docker-smoke.ps1`
- `scripts/cloud/smoke-local.ps1`

## Container image

`Dockerfile` использует `python:3.12-slim`, устанавливает:

- `curl` для Docker healthcheck;
- `fontconfig`;
- `fonts-dejavu-core` для PDF/cyrillic font baseline;
- пакет `expense-splitter` с extras `cloud,telegram`.

Container запускается non-root пользователем `expense`.

Запуск:

```powershell
docker build -t expense-splitter-backend:local .
docker run --rm -p 8000:8000 expense-splitter-backend:local
```

Проверка:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\cloud\smoke-local.ps1
```

## Local compose

`compose.yaml` предназначен для локального smoke:

```powershell
docker compose up --build backend
```

По умолчанию backend стартует в YAML mode:

```text
EXPENSE_SPLITTER_REPOSITORY=yaml
```

Это сохраняет offline compatibility и позволяет smoke без live PostgreSQL repository.

Локальный PostgreSQL можно поднять отдельным profile:

```powershell
docker compose --profile postgres up --build
```

Важно: CLOUD.5 пока содержит PostgreSQL schema/migrations и repository contract, а live
PostgreSQL adapter еще не реализован. Поэтому полноценный DB write/read smoke должен быть
добавлен после реализации PostgreSQL repository execution.

## Yandex Cloud target components

- Container/VM runtime for FastAPI backend.
- Managed PostgreSQL.
- Object Storage bucket for generated reports.
- Lockbox/env secrets for Telegram token, webhook secret, database URL and object storage
  credentials.
- Monitoring/logging for health endpoints, container restarts and error rate.

## Environment variables

Required cloud values must come from Lockbox or runtime environment, not Git:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_WEBHOOK_SECRET
DATABASE_URL
YANDEX_CLOUD_FOLDER_ID
YANDEX_OBJECT_STORAGE_BUCKET
EXPENSE_SPLITTER_REPOSITORY=postgres
EXPENSE_SPLITTER_REPORT_STORAGE=object_storage
EXPENSE_SPLITTER_OBJECT_PREFIX=reports
```

`.env.example` remains safe placeholder-only. `.env`, service account keys and tokens are
ignored by Git.

## Object Storage policy

MVP recommendation:

- bucket is private;
- backend writes generated PDF/XLSX files;
- Telegram sends files via `sendDocument`;
- bot session stores only report metadata, never permanent file bytes;
- report artifacts should have lifecycle retention, for example 7-30 days;
- object keys should include tenant/report type/date prefix;
- direct public access is disabled unless a later signed URL flow is explicitly designed.

Current `ObjectStorageReportOutputAdapter` is a storage-key contract stub and does not
upload files yet.

## Managed PostgreSQL policy

MVP recommendation:

- private network access where possible;
- separate app user with least privileges;
- migrations applied by controlled deployment step;
- daily automated backups enabled;
- point-in-time recovery enabled if available for the selected tier;
- manual backup before schema migrations;
- no database password in repository or logs.

## Cloud smoke plan

Run only after explicit operator approval and real resources are prepared:

1. Backend `/health`.
2. Backend `/health/reporting`.
3. Database connection check.
4. Apply migrations dry-run/real migration.
5. Generate current PDF/XLSX in temp workspace.
6. Upload test report artifact to Object Storage.
7. Download/verify uploaded artifact.
8. Telegram webhook dry-run with secret validation.

For current repository state, steps 3, 6, 7 and webhook live call are blockers until live
PostgreSQL repository and Object Storage upload are implemented.

## Deployment decision

CLOUD.8 result is a deployment-ready package, not a production deployment. Safe next work:

- implement live PostgreSQL repository;
- implement Object Storage upload adapter;
- add webhook endpoint and Telegram SDK runner;
- add auth/tenant identity resolution;
- then perform cloud smoke with real resources.
