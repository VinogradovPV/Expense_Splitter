# CLOUD.0 — Implementation Roadmap

Дата: 2026-07-01
Статус: roadmap design; implementation not started.

## Цель

Задать порядок работ после CLOUD.0 так, чтобы Telegram/Yandex Cloud направление не сломало
стабильный Desktop GUI/CLI/YAML режим.

## CLOUD.1 — Repository Protocols Only

Цель:

- добавить `src/expense_splitter/repositories/protocols.py`;
- описать repository protocols and DTO patches;
- не менять поведение CLI/GUI.

Проверки:

- full tests;
- no Typer/Tkinter imports in protocols.

## CLOUD.2 — YAML Repository Adapter

Цель:

- добавить `YamlExpenseRepository`;
- обернуть текущий `storage.py`;
- сохранить local `data/` behavior.

Проверки:

- repository tests compare with storage functions;
- existing CLI/GUI tests stay green.

## CLOUD.3 — Thin Service Layer Extraction

Цель:

- добавить services one use case at a time;
- start with purchases and directory services;
- then settlement service.

Правило:

- CLI/GUI become adapters gradually;
- no Telegram code yet.

## CLOUD.4 — ReportService And Output Adapters

Цель:

- introduce `ReportService`;
- introduce local/temp output adapters;
- keep current report writers working;
- prepare Object Storage adapter interface.

Проверки:

- current/analytics/settlement report tests remain green;
- settlement-period historical snapshot behavior unchanged.

## CLOUD.5 — PostgreSQL Schema And Migrations

Цель:

- create migrations/schema based on `DATABASE_SCHEMA.md`;
- add repository implementation skeleton;
- add transaction tests where possible.

Prerequisite:

- stable IDs decisions confirmed.

## CLOUD.6 — FastAPI Backend MVP

Цель:

- create FastAPI app;
- health endpoints;
- purchase/report endpoints;
- tenant/user resolution skeleton;
- no production Telegram bot code yet.

Security:

- config from env/secret store;
- no committed secrets.

## CLOUD.7 — Telegram Bot MVP

Status: completed as framework-neutral MVP adapter; real webhook/long polling deployment is future work.

Цель:

- implement bot adapter;
- commands `/start`, `/help`, `/add_purchase`, `/current_pdf`, `/current_xlsx`;
- call backend/API only.

Prerequisite:

- CLOUD.0-CLOUD.6 complete.

## CLOUD.8 — Yandex Cloud Deployment MVP

Цель:

- deployment docs/config;
- container build;
- secret store integration;
- managed PostgreSQL/Object Storage wiring;
- smoke plan.

Rules:

- real cloud deploy only with explicit user confirmation.

## CLOUD.9 — Production Hardening

Цель:

- monitoring/alerts;
- backup/restore;
- rate limits;
- audit review;
- data retention;
- security review;
- user acceptance smoke.

## Release Gates

Each stage must:

- keep `cloud/telegram-prep` clean;
- pass relevant tests/checks;
- not commit generated artifacts;
- not commit secrets;
- keep YAML offline mode working unless explicitly changed in a later approved stage.

## Current Next Step

After CLOUD.0, the next safe step is:

```text
CLOUD.1 — repository protocols only
```

Do not start with Telegram handlers. The bot is an adapter, not the place where business logic
should live.
