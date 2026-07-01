# CLOUD.0 — API Contract

Дата: 2026-07-01
Статус: API design; FastAPI code не создавался.

## Цель

Описать будущий FastAPI contract между Telegram bot, backend service layer и report delivery
контуром. Telegram bot не должен вызывать CLI и не должен знать YAML/filesystem/report internals.

## API Principles

- JSON over HTTPS.
- All requests resolve `tenant_id`.
- All mutating requests are audit logged.
- Report endpoints are read-only except report metadata/audit entries.
- Errors are structured and user-safe.
- Real secrets are never passed in URLs.
- Bot webhook is validated by Telegram/webhook secret.

## Authentication And Resolution

Telegram webhook request includes Telegram user context. Backend resolves:

```text
telegram_user_id -> telegram_accounts.user_id -> users.user_id -> participants.participant_id
```

Tenant selection:

- MVP may use one default tenant per Telegram account.
- Future supports multiple tenants and explicit tenant selection.
- Every domain endpoint operates inside a resolved `tenant_id`.

## Telegram Webhook Endpoint

```http
POST /telegram/webhook
```

Headers:

- `X-Telegram-Bot-Api-Secret-Token: <webhook_secret>`

Behavior:

- validate webhook secret;
- parse update;
- dispatch command/conversation state;
- call internal services;
- return fast 200 response to Telegram.

Responses:

```json
{"ok": true}
```

Errors should be logged internally and converted to user-friendly Telegram messages where possible.

## Health Endpoints

```http
GET /health
GET /health/reporting
```

`/health` checks app readiness.

`/health/reporting` checks:

- ReportLab import;
- matplotlib backend;
- openpyxl import;
- Cyrillic PDF font availability;
- Object Storage configuration presence in non-local environment.

## Purchase Endpoints

### List Purchases

```http
GET /api/v1/tenants/{tenant_id}/purchases?scope=open
```

Response:

```json
{
  "items": [
    {
      "purchase_id": "uuid",
      "date": "2026-07-01",
      "purchase_name": "Кофе",
      "amount": "350.00",
      "payer_participant_id": "uuid",
      "participant_ids": ["uuid"],
      "category_id": "uuid",
      "status": "open"
    }
  ]
}
```

### Add Purchase

```http
POST /api/v1/tenants/{tenant_id}/purchases
Idempotency-Key: <client-generated-key>
```

Request:

```json
{
  "purchase_name": "Кофе",
  "date": "2026-07-01",
  "amount": "350.00",
  "payer_participant_id": "uuid",
  "participant_ids": ["uuid"],
  "category_id": "uuid",
  "comment": "после встречи"
}
```

Response: `201 Created` with purchase object.

### Update Purchase

```http
PATCH /api/v1/tenants/{tenant_id}/purchases/{purchase_id}
```

Request contains patch fields only.

Rules:

- settled purchases are protected by service policy;
- optimistic locking can use `version`;
- edits are audit logged.

## Directory Endpoints

```http
GET /api/v1/tenants/{tenant_id}/participants
GET /api/v1/tenants/{tenant_id}/categories
POST /api/v1/tenants/{tenant_id}/participants
PATCH /api/v1/tenants/{tenant_id}/participants/{participant_id}
POST /api/v1/tenants/{tenant_id}/categories
PATCH /api/v1/tenants/{tenant_id}/categories/{category_id}
```

Display names are mutable labels, not IDs.

## Settlement Period Endpoints

Preview:

```http
POST /api/v1/tenants/{tenant_id}/settlement-periods/preview
```

Close:

```http
POST /api/v1/tenants/{tenant_id}/settlement-periods
Idempotency-Key: <client-generated-key>
```

Reopen:

```http
POST /api/v1/tenants/{tenant_id}/settlement-periods/{settlement_period_id}/reopen
```

List/show:

```http
GET /api/v1/tenants/{tenant_id}/settlement-periods
GET /api/v1/tenants/{tenant_id}/settlement-periods/{settlement_period_id}
```

Rules:

- close/reopen must be transactional;
- historical snapshot settlements are stored at close time;
- reopen does not delete historical snapshot.

## Report Endpoints

Current report:

```http
POST /api/v1/tenants/{tenant_id}/reports/current
```

Request:

```json
{"scope": "open", "formats": ["pdf", "xlsx"]}
```

Analytics:

```http
POST /api/v1/tenants/{tenant_id}/reports/analytics
```

Request:

```json
{"period": {"kind": "month", "year": 2026, "month": 7}, "formats": ["pdf"]}
```

Settlement period:

```http
POST /api/v1/tenants/{tenant_id}/reports/settlement-period
```

Request:

```json
{"settlement_period_id": "uuid", "formats": ["pdf", "xlsx"]}
```

Response:

```json
{
  "report_id": "uuid",
  "report_type": "current",
  "formats": ["pdf"],
  "files": [
    {
      "format": "pdf",
      "filename": "current_state.pdf",
      "content_type": "application/pdf",
      "storage_key": "reports/tenant/report/current_state.pdf"
    }
  ],
  "created_at": "2026-07-01T10:00:00Z",
  "expires_at": "2026-07-08T10:00:00Z",
  "storage_backend": "object_storage",
  "telegram_caption": "Текущие взаиморасчеты: открытые покупки.",
  "warnings": []
}
```

## Error Codes

Common errors:

- `AUTH_INVALID_WEBHOOK_SECRET`
- `AUTH_TENANT_ACCESS_DENIED`
- `VALIDATION_ERROR`
- `PURCHASE_NOT_FOUND`
- `PARTICIPANT_NOT_FOUND`
- `CATEGORY_NOT_FOUND`
- `SETTLEMENT_PERIOD_NOT_FOUND`
- `SETTLEMENT_PERIOD_ALREADY_REOPENED`
- `REPORT_UNSUPPORTED_FORMAT`
- `REPORT_EMPTY_DATASET`
- `REPORT_PDF_FONT_MISSING`
- `REPORT_STORAGE_UPLOAD_FAILED`
- `INTERNAL_ERROR`

Error shape:

```json
{
  "error": {
    "code": "REPORT_PDF_FONT_MISSING",
    "message": "PDF временно недоступен: не найден кириллический шрифт.",
    "request_id": "uuid"
  }
}
```

## Idempotency

Use `Idempotency-Key` for:

- add purchase;
- close settlement period;
- reopen settlement period;
- report generation requests if repeated Telegram commands can duplicate work.

Backend stores request key per tenant/user/action and returns previous result for safe retries.

## Security Expectations

- Webhook secret validation is mandatory.
- Bot token is stored outside Git in Lockbox/env secrets.
- Database credentials are masked in logs.
- API responses do not expose local filesystem paths in cloud mode.
- Audit log records actor/source/action but not secrets.

## Explicit CLOUD.0 Prohibitions

This contract does not authorize:

- writing FastAPI code;
- writing Telegram bot code;
- deploying cloud resources;
- adding real secrets;
- changing current CLI/GUI behavior.
