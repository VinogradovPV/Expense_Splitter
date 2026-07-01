# CLOUD.0 — Telegram + Yandex Cloud Architecture

Дата: 2026-07-01
Ветка: `cloud/telegram-prep`
Статус: architecture design; production bot code, cloud deploy и secrets не создавались.

## Цель

Определить целевую архитектуру Expense Splitter для Telegram + Yandex Cloud так, чтобы новый
серверный контур переиспользовал существующую доменную логику, не писал напрямую в YAML и не ломал
Desktop GUI/CLI offline mode.

## Target MVP Architecture

Решение для MVP:

```text
Telegram Bot
  -> FastAPI backend service/container
  -> service layer
  -> repository protocols
  -> PostgreSQL repository
  -> PostgreSQL
  -> ReportService/report generator
  -> Object Storage
  -> Telegram sendDocument
```

Обязательные решения:

- Telegram bot не пишет в YAML напрямую.
- Telegram bot не вызывает CLI-команды.
- Bot обращается к backend/API, а backend вызывает service layer.
- PostgreSQL использует stable IDs и tenant isolation.
- YAML offline desktop mode сохраняется через будущий YAML repository adapter.
- Reports генерируются через `ReportService`, а Telegram только отправляет PDF/XLSX через
  `sendDocument`.

## Component Responsibilities

### Telegram Bot

Отвечает за:

- команды и conversational UX;
- прием Telegram updates;
- передачу пользовательских действий в backend;
- отправку документов пользователю через `sendDocument`.

Не отвечает за:

- расчет балансов;
- запись покупок напрямую;
- генерацию PDF/XLSX;
- хранение постоянных report files;
- доступ к PostgreSQL напрямую.

### FastAPI Backend

Отвечает за:

- Telegram webhook endpoint;
- internal API endpoints для future UI/admin;
- tenant/user/participant resolution;
- validation boundary;
- вызов services;
- structured errors;
- audit context.

### Service Layer

Отвечает за:

- purchase use cases;
- participant/category directory use cases;
- settlement period preview/close/reopen;
- report requests;
- transaction boundaries.

Services не должны импортировать Typer, Tkinter, Rich, Telegram SDK или raw SQL.

### Repository Layer

Отвечает за:

- единый contract доступа к данным;
- PostgreSQL adapter для cloud;
- YAML adapter для desktop/offline mode;
- скрытие storage details от расчетов.

### PostgreSQL

Отвечает за:

- tenants/users/telegram accounts;
- stable IDs;
- purchases and participants;
- settlement snapshots;
- report metadata;
- audit log;
- bot sessions.

### Report Generator

Отвечает за:

- build current/analytics/settlement-period datasets;
- создание PDF/XLSX и при необходимости CSV/PNG/HTML intermediates;
- работу во временной директории;
- передачу artifacts в output adapter.

### Object Storage

Отвечает за:

- хранение final report artifacts;
- retention/expiration;
- object keys per tenant/report;
- возможность скачать/stream file для Telegram `sendDocument`.

## Yandex Cloud Components

MVP candidates:

- Container/VM runtime for FastAPI backend.
- Managed PostgreSQL или PostgreSQL-compatible managed DB.
- Object Storage bucket for report artifacts.
- Yandex Lockbox or environment secrets for bot token, webhook secret, database URL and service
  credentials.
- Logging/Monitoring for backend and report generation.

Future optional components:

- Message Queue for async report jobs.
- Serverless Functions for lightweight webhook routing.
- Container Registry for backend images.
- API Gateway, if public endpoint management requires it.

## Environments

### Local

- Existing CLI/GUI continue using YAML.
- Backend can run with local PostgreSQL or fake repositories.
- Reports may use local temp directories.
- `.env` stays ignored; `.env.example` has placeholders only.

### Dev

- One dev tenant.
- Test Telegram bot token from secret store.
- Dev PostgreSQL.
- Dev Object Storage bucket with short retention.
- Debug logging allowed, secrets masked.

### Prod

- Production bot token only in secret store.
- Separate production PostgreSQL.
- Object Storage retention policy.
- Minimal logs with masked PII/secrets.
- Audit log enabled for domain operations.

## Report Generation Flow

Current report example:

```text
Telegram /current_pdf
  -> webhook
  -> resolve telegram_user_id -> user_id -> participant_id -> tenant_id
  -> ReportService.create_current_report(tenant_id, scope="open", formats={"pdf"})
  -> repository loads purchases/participants
  -> build_current_report_dataset
  -> generate report in temp workspace
  -> upload PDF to Object Storage
  -> return ReportResult
  -> bot sends PDF via sendDocument
```

Settlement period report:

- Load period by `settlement_period_id`.
- Use snapshot settlements.
- Do not recalculate historical settlements.
- Include reopened/missing-data warnings.
- Upload final PDF/XLSX to Object Storage.

## Object Storage Flow

Suggested object key:

```text
reports/{tenant_id}/{report_type}/{report_id}/{filename}
```

Rules:

- Bot stores only `report_id`/status in session.
- Backend/report service owns upload.
- Expiration/retention is backend policy.
- Object Storage credentials never appear in bot code or docs.

## Deployment Topology

MVP topology:

```text
Internet
  -> Telegram
  -> HTTPS webhook endpoint
  -> FastAPI container/service
  -> PostgreSQL
  -> Object Storage
  -> Telegram sendDocument
```

The container should include:

- Python runtime;
- application package;
- ReportLab;
- matplotlib;
- openpyxl;
- Cyrillic-capable font.

## Observability Basics

Minimum:

- structured request logs with `request_id`;
- report generation duration;
- error codes;
- audit log for domain operations;
- healthcheck for backend;
- healthcheck for PDF font availability;
- metrics for report success/failure.

Never log:

- bot token;
- webhook secret;
- database password;
- service account private key.

## Why Backend Service / Container For MVP

Container/backend service is preferred over pure serverless because Expense Splitter report stack
uses:

- ReportLab;
- matplotlib;
- openpyxl;
- Cyrillic fonts;
- temporary report workspaces;
- artifact upload.

This path is easier to smoke test, debug and deploy without fighting cold start, font packaging and
file workspace limits.

Serverless can be revisited as a future optimization after service/repository/report boundaries are
stable.

## Explicit CLOUD.0 Prohibitions

CLOUD.0 must not:

- write Telegram bot code;
- deploy cloud resources;
- add real secrets;
- change business logic;
- break CLI/GUI/YAML offline mode;
- change settlement close/reopen semantics;
- commit generated artifacts.
