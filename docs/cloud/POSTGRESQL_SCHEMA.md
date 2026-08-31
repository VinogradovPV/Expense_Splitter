# CLOUD.5 — PostgreSQL Schema Foundation

Дата: 2026-07-01
Ветка: `cloud/telegram-prep`
Статус: schema foundation; live PostgreSQL repository implementation is deferred.

## Цель

CLOUD.5 добавляет серверную relational model для будущего FastAPI/Telegram backend и
PostgreSQL repository, не меняя локальный YAML/offline режим.

## Dependency Decision

Выбран будущий серверный стек:

- SQLAlchemy 2.x;
- Alembic;
- psycopg 3.

Зависимости добавлены в optional extra `cloud`, а не в основной desktop/runtime набор:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,cloud]"
```

Обычный desktop/CLI/GUI режим и YAML repository продолжают работать без PostgreSQL.

## Stable ID Strategy

PostgreSQL schema использует UUID primary keys:

- `tenant_id`;
- `user_id`;
- `telegram_account_id`;
- `participant_id`;
- `category_id`;
- `purchase_id`;
- `settlement_period_id`;
- `report_id`;
- `audit_log_id`;
- `bot_session_id`.

Display name не является primary key. Текущие YAML/display identifiers могут быть сохранены
как `legacy_id`, `legacy_name` или `period_code`.

## Migration

Initial SQL migration:

```text
src/expense_splitter/db/migrations/0001_initial.sql
```

Migration создает:

- `pgcrypto` extension для `gen_random_uuid()`;
- tenants/users/telegram identity tables;
- participants/categories/purchases;
- settlement period snapshot tables;
- reports metadata table;
- audit log;
- bot sessions;
- tenant-scoped indexes.

## Tenant Isolation

Все domain tables имеют `tenant_id`:

- `participants`;
- `participant_aliases`;
- `categories`;
- `purchases`;
- `purchase_participants`;
- `settlement_periods`;
- `settlement_period_purchases`;
- `reports`;
- `audit_log`;
- `bot_sessions`.

`users` и `telegram_accounts` являются identity tables. Telegram user не равен participant:

```text
telegram_user_id -> telegram_accounts.user_id -> users.user_id
tenant_id + user_id -> participants.participant_id
```

## Historical Snapshots

Settlement period history stores snapshot fields:

- `settlements_snapshot`;
- `balances_snapshot`;
- `settlement_period_purchases.*_snapshot`;
- payer/category/participant display-name snapshots.

Historical settlement-period reports must use stored snapshots and must not recompute transfers
when snapshot settlements exist.

## Reports Metadata

`reports` stores metadata, warnings, formats and storage backend references. Binary artifacts are
not stored in PostgreSQL. PDF/XLSX/HTML files should be delivered through `ReportService` output
adapters and future Object Storage.

## Audit Log

`audit_log` is intended for:

- purchase creation/editing/deletion;
- settlement period close/reopen;
- directory changes;
- report generation;
- future administrative operations.

## Current Limitations

- `PostgresExpenseRepository` is a contract stub and raises explicit
  `PostgresRepositoryNotImplementedError`.
- No live PostgreSQL tests are required in normal CI.
- Alembic environment is not initialized yet; the initial migration is plain SQL and package data.
- YAML offline mode remains the only fully executable repository adapter.
