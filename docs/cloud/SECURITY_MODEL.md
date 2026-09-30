# CLOUD.0 — Security Model

Дата: 2026-07-01
Статус: security design; secrets and cloud resources не создавались.

## Цель

Описать security model для Telegram + FastAPI + PostgreSQL + Object Storage, продолжая правило
TG-PREP.7: реальные tokens/keys/passwords не попадают в Git.

## Secret Storage

Secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `DATABASE_URL`
- Object Storage credentials
- Yandex service account credentials

Allowed storage:

- Yandex Lockbox;
- deployment environment secrets;
- local ignored `.env` for development.

Forbidden:

- Git;
- committed docs;
- screenshots;
- logs;
- CLI command history where possible;
- service-account JSON in repo.

`.env.example` may contain placeholders only.

## Telegram Webhook Security

Backend validates:

- webhook secret header;
- request shape;
- allowed update types;
- size limits.

Backend should reject invalid secret with 401/403 and no verbose detail.

## Database Security

Rules:

- `DATABASE_URL` password masked in logs;
- least privilege DB user for app;
- separate dev/prod databases;
- migrations run by controlled role;
- tenant isolation enforced in repository/service queries.

## Yandex Cloud Permissions

Service account should have minimal permissions:

- read secrets from Lockbox needed by service;
- write/read report artifacts in specific Object Storage bucket/prefix;
- write logs/metrics.

Do not grant broad admin permissions to runtime service account.

## Object Storage Security

Rules:

- private bucket by default;
- report object keys include tenant/report ID;
- signed URLs if direct download is needed;
- retention policy for generated reports;
- no public bucket for personal expense reports.

Telegram delivery should stream or download the file server-side and call `sendDocument`.

## Audit Log

Audit events:

- `purchase.added`
- `purchase.edited`
- `purchase.deleted`
- `settlement_period.closed`
- `settlement_period.reopened`
- `participant.added`
- `participant.renamed`
- `participant.archived`
- `category.added`
- `category.renamed`
- `category.archived`
- `report.generated`
- `report.failed`

Audit log stores:

- tenant;
- actor user;
- source (`telegram`, `api`, `cli`, `gui`, `migration`);
- before/after snapshots where safe;
- request ID.

Audit log must not store secrets.

## Logging Rules

Do not log:

- bot token;
- webhook secret;
- DB password;
- private keys;
- full service account JSON.

Mask:

- connection strings;
- object storage credentials;
- any token-like values.

Use request IDs to correlate logs without exposing payload secrets.

## Incident Response

If a secret leaks:

1. Treat it as compromised.
2. Rotate/revoke it in Telegram/Yandex/PostgreSQL.
3. Audit where it was used.
4. Remove from current branch.
5. Decide separately whether Git history rewrite is required.
6. Do not rely on "delete in next commit" as remediation.

## Development Safety

Before each cloud-related commit:

```powershell
git status --short
git diff --cached --name-only
git grep -n -E "(BOT_TOKEN|TELEGRAM|YANDEX|YC_|SECRET|PASSWORD|TOKEN|DATABASE_URL|SERVICE_ACCOUNT|PRIVATE_KEY)" -- . ':!docs/cloud/SECURITY_PREP_CHECKLIST.md' ':!.env.example'
```

Expected matches should be documentation placeholders only.

## CLOUD.0 Prohibitions

Do not:

- create real Telegram bot token;
- create Yandex resources;
- commit `.env`;
- commit keys;
- add production deployment config with secrets.
