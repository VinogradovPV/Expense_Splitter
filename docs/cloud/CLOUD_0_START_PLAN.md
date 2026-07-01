# TG-PREP.8 — CLOUD.0 Start Plan

Дата: 2026-07-01
Ветка: `cloud/telegram-prep`
Статус: ready-for-CLOUD.0 planning package; bot code, cloud deploy и secrets не добавлялись.

## Цель

Сформировать рабочий пакет для следующего этапа `CLOUD.0`, где будет спроектирована архитектура
Telegram + Yandex Cloud automation до написания кода бота и до создания cloud resources.

Этот документ фиксирует recommended MVP path, альтернативы, документы, которые должен создать
CLOUD.0, и запреты, чтобы cloud-направление не сломало стабильный YAML/Desktop baseline.

## Prepared Inputs

Перед CLOUD.0 уже подготовлены:

- `docs/cloud/SERVER_READINESS_AUDIT.md`
- `docs/cloud/SERVICE_REPOSITORY_BOUNDARY.md`
- `docs/cloud/DATABASE_READINESS.md`
- `docs/cloud/REPORT_DELIVERY_CONTRACT.md`
- `docs/cloud/SECURITY_PREP_CHECKLIST.md`
- `.env.example`
- `.gitignore` rules для `.env`, keys и service account files

## Recommended MVP Architecture

Рекомендуемый поток:

```text
Telegram Bot
  -> FastAPI backend
  -> service layer
  -> repository
  -> PostgreSQL
  -> report generator
  -> Object Storage
  -> Telegram sendDocument
```

Разделение ответственности:

- Telegram Bot: получает сообщения, показывает UX, отправляет документы через `sendDocument`.
- FastAPI backend: принимает webhook/API calls, авторизует Telegram user, вызывает services.
- Service layer: добавление покупок, справочники, settlement periods, report requests.
- Repository: скрывает YAML/PostgreSQL детали от services.
- PostgreSQL: server storage, transaction boundary, stable IDs, audit log.
- Report generator: строит PDF/XLSX/HTML/CSV/PNG во временной рабочей папке.
- Object Storage: хранит готовые artifacts с retention policy.
- Telegram delivery: отправляет файл пользователю, не становясь permanent storage.

## Architecture Alternatives

### Serverless

Вариант:

- Telegram webhook -> Yandex Cloud Functions;
- PostgreSQL/YDB/Managed DB;
- Object Storage для отчетов.

Плюсы:

- меньше инфраструктуры;
- потенциально дешевле на малой нагрузке;
- проще стартовать для простых text-only команд.

Минусы:

- тяжелее контролировать ReportLab/matplotlib/openpyxl dependencies;
- сложнее обеспечить кириллические шрифты для PDF;
- cold start может быть неприятен для report generation;
- сложнее отлаживать долгие jobs и файловые workspaces;
- artifacts generation может упереться во временное хранилище/лимиты.

Вывод: подходит как future optimization, но не лучший первый шаг для отчетов PDF/XLSX.

### VM / Container

Вариант:

- один backend service в container/VM;
- FastAPI;
- bot webhook endpoint;
- report generation внутри container;
- PostgreSQL + Object Storage.

Плюсы:

- контроль над Python dependencies;
- можно упаковать кириллические fonts;
- проще smoke/debug/deploy;
- проще воспроизвести локально;
- проще поддержать временные папки для report generation;
- меньше сюрпризов с ReportLab/matplotlib/openpyxl.

Минусы:

- нужно управлять runtime/service;
- нужно следить за обновлениями и logs;
- может быть дороже serverless при совсем малой нагрузке.

Вывод: предпочтительный MVP path.

### Hybrid

Вариант:

- lightweight Telegram webhook в serverless;
- тяжелые reports в container worker;
- PostgreSQL + Object Storage.

Плюсы:

- быстрый bot response;
- report generation вынесена в controlled environment;
- можно масштабировать worker отдельно.

Минусы:

- больше движущихся частей;
- нужен queue/job orchestration;
- больше surface для security/config mistakes.

Вывод: хороший этап после MVP, если отчеты станут тяжелыми или появится много пользователей.

## Why Backend Service / Container Is Preferred For MVP

Expense Splitter уже имеет rich report stack:

- ReportLab for PDF;
- matplotlib for charts;
- openpyxl for XLSX;
- локальные/серверные кириллические шрифты;
- offline HTML/CSV/PNG intermediates;
- smoke/debug сценарии через CLI и tests.

Container/backend service дает:

- воспроизводимую среду для fonts and binary dependencies;
- controlled temp workspace;
- понятный healthcheck для PDF font availability;
- возможность запускать existing tests в CI/CD;
- проще смотреть logs и artifacts при ошибках;
- проще не ломать desktop YAML mode, потому что backend станет отдельным adapter/use-case layer.

## CLOUD.0 Must Create These Documents

`CLOUD.0` должен создать архитектурный пакет:

- `docs/cloud/TELEGRAM_YANDEX_CLOUD_ARCHITECTURE.md`
- `docs/cloud/API_CONTRACT.md`
- `docs/cloud/DATABASE_SCHEMA.md`
- `docs/cloud/TELEGRAM_BOT_SPEC.md`
- `docs/cloud/MIGRATION_PLAN.md`
- `docs/cloud/SECURITY_MODEL.md`
- `docs/cloud/IMPLEMENTATION_ROADMAP.md`

### `TELEGRAM_YANDEX_CLOUD_ARCHITECTURE.md`

Должен описать:

- выбранную MVP architecture;
- deployment topology;
- Yandex Cloud components;
- request/report flows;
- local/dev/prod environments;
- observability basics.

### `API_CONTRACT.md`

Должен описать:

- FastAPI endpoints;
- request/response schemas;
- auth model;
- Telegram webhook contract;
- error codes;
- idempotency expectations.

### `DATABASE_SCHEMA.md`

Должен развить `DATABASE_READINESS.md` в конкретную relational schema:

- tables;
- columns;
- primary/foreign keys;
- indexes;
- constraints;
- migration order.

### `TELEGRAM_BOT_SPEC.md`

Должен описать:

- commands;
- conversational flows;
- validation messages;
- participant/tenant selection;
- report request UX;
- Russian user-facing copy.

### `MIGRATION_PLAN.md`

Должен описать:

- YAML -> PostgreSQL import;
- stable ID generation;
- display name alias mapping;
- conflict handling;
- rollback/backup strategy;
- dry-run migration.

### `SECURITY_MODEL.md`

Должен описать:

- secret storage;
- Yandex Lockbox/env secrets;
- Telegram webhook secret validation;
- database credential handling;
- service account permissions;
- audit log and privacy considerations.

### `IMPLEMENTATION_ROADMAP.md`

Должен описать:

- phased implementation;
- which code changes happen first;
- test strategy;
- release gates;
- what remains explicitly out of scope.

## CLOUD.0 Explicit Prohibitions

В рамках `CLOUD.0` запрещено:

- писать Telegram bot code;
- деплоить cloud resources;
- добавлять реальные secrets/tokens/keys;
- ломать YAML offline mode;
- удалять Desktop GUI/CLI flows;
- менять settlement close/reopen semantics;
- переписывать report generation без compatibility plan;
- создавать final production release/tag без отдельного подтверждения.

## Required CLOUD.0 Checks

После подготовки документов:

```powershell
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
git diff --check
git status --short --ignored
```

Если CLOUD.0 меняет только docs, полный test suite не обязателен, но CI на push должен быть зеленым.
Если CLOUD.0 меняет `.gitignore`, `.env.example`, Python code или workflow, нужен полный quality
gate.

## Recommended Command For Next Codex Task

```text
Выполни CLOUD.0 — архитектурное проектирование Telegram + Yandex Cloud automation.

Рабочая ветка:
cloud/telegram-prep

Используй как входные документы:
docs/cloud/SERVER_READINESS_AUDIT.md
docs/cloud/SERVICE_REPOSITORY_BOUNDARY.md
docs/cloud/DATABASE_READINESS.md
docs/cloud/REPORT_DELIVERY_CONTRACT.md
docs/cloud/SECURITY_PREP_CHECKLIST.md
docs/cloud/CLOUD_0_START_PLAN.md

Создай:
docs/cloud/TELEGRAM_YANDEX_CLOUD_ARCHITECTURE.md
docs/cloud/API_CONTRACT.md
docs/cloud/DATABASE_SCHEMA.md
docs/cloud/TELEGRAM_BOT_SPEC.md
docs/cloud/MIGRATION_PLAN.md
docs/cloud/SECURITY_MODEL.md
docs/cloud/IMPLEMENTATION_ROADMAP.md

Запрещено:
не писать bot code;
не деплоить cloud;
не добавлять secrets;
не ломать YAML offline mode.

После документов выполнить:
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
git diff --check
git status --short --ignored

Commit:
git add docs/cloud
git commit -m "docs: design telegram yandex cloud architecture"
git push origin cloud/telegram-prep
```

## Decision

`TG-PREP` завершает подготовку cloud-ветки. Следующий безопасный шаг — `CLOUD.0`, полностью
документационный архитектурный этап. Реализация Telegram bot должна начинаться только после
утверждения architecture/API/database/security roadmap.
