# TG-PREP.5 — Database Readiness

Дата: 2026-07-01
Ветка: `cloud/telegram-prep`
Статус: data model plan; PostgreSQL schema/migrations пока не создавались.

## Цель

Подготовить модель данных Expense Splitter для многопользовательского server/cloud контура:
Telegram bot, будущий FastAPI backend, PostgreSQL repository и сохранение offline YAML режима как
отдельного adapter-а.

Главный принцип: display name не является идентификатором. Имя участника можно менять, показывать в
отчетах и хранить в historical snapshot, но нельзя использовать как primary key.

## Stable IDs

Минимальные stable IDs:

- `tenant_id`
- `user_id`
- `telegram_account_id`
- `participant_id`
- `category_id`
- `purchase_id`
- `settlement_period_id`
- `report_id`
- `audit_log_id`
- `bot_session_id`

Рекомендуемый формат: UUID/ULID на уровне backend. Человеко-читаемые IDs вроде текущих
`settlement_YYYY_MM_DD_001` можно сохранить как `period_code` или `legacy_id`, но не как
единственный primary key в PostgreSQL.

## Multi-Tenant Model

Даже если MVP стартует с одним tenant, схема должна поддерживать несколько групп/tenant-ов:

- один tenant = одна изолированная группа расходов;
- users могут принадлежать нескольким tenant-ам;
- participant является ролью/профилем пользователя внутри tenant-а;
- покупки, категории, периоды, отчеты и audit events всегда принадлежат tenant-у.

Все запросы backend должны фильтроваться по `tenant_id`. Telegram chat/user ID сам по себе не
заменяет tenant isolation.

## Entity Overview

### `tenants`

Назначение: изолированная группа совместных расходов.

Поля:

- `tenant_id` PK
- `name`
- `status` (`active`, `archived`)
- `default_currency`
- `created_at`
- `updated_at`

Индексы:

- unique normalized `name` можно добавить позже только внутри admin context; не использовать как
  основной lookup в bot flow.

### `users`

Назначение: человек/аккаунт приложения, который может быть связан с Telegram и с одним или
несколькими participants.

Поля:

- `user_id` PK
- `display_name`
- `status` (`active`, `disabled`)
- `created_at`
- `updated_at`

Примечание: user не обязан совпадать с participant. Один user может представлять себя в разных
tenant-ах разными participant profiles.

### `telegram_accounts`

Назначение: связь Telegram identity с внутренним user.

Поля:

- `telegram_account_id` PK
- `telegram_user_id` unique not null
- `user_id` FK -> `users.user_id`
- `username`
- `first_name`
- `last_name`
- `language_code`
- `created_at`
- `last_seen_at`

Связь Telegram user:

```text
telegram_user_id -> telegram_accounts.user_id -> users.user_id -> participants.participant_id
```

Для выбора participant в конкретном tenant:

```text
telegram_user_id + tenant_id
  -> user_id
  -> participants where tenant_id = ? and linked_user_id = user_id
```

### `participants`

Назначение: участник расчетов внутри tenant-а.

Поля:

- `participant_id` PK
- `tenant_id` FK -> `tenants.tenant_id`
- `linked_user_id` nullable FK -> `users.user_id`
- `display_name`
- `normalized_display_name`
- `status` (`active`, `archived`)
- `created_at`
- `updated_at`

Ограничения:

- unique (`tenant_id`, `normalized_display_name`) для active participants желательно, но это не PK.
- historical reports должны хранить display labels в snapshot, потому что display name может
  измениться позже.

### `participant_aliases`

Назначение: миграция и распознавание старых/альтернативных имен участников.

Поля:

- `participant_alias_id` PK
- `tenant_id` FK
- `participant_id` FK -> `participants.participant_id`
- `alias`
- `normalized_alias`
- `source` (`yaml_migration`, `telegram_input`, `manual`)
- `created_at`

Использование:

- при миграции YAML старое имя становится alias;
- при rename старое display name можно добавить как alias;
- bot может использовать alias matching, но должен подтверждать ambiguous matches.

### `categories`

Назначение: справочник категорий внутри tenant-а.

Поля:

- `category_id` PK
- `tenant_id` FK
- `display_name`
- `normalized_display_name`
- `status` (`active`, `archived`)
- `created_at`
- `updated_at`

Ограничения:

- category display name не является PK.
- YAML `category` string мигрируется в `category_id`; исходная строка может храниться в audit или
  migration notes.

### `purchases`

Назначение: покупка/расход.

Поля:

- `purchase_id` PK
- `tenant_id` FK
- `purchase_date`
- `purchase_name`
- `amount`
- `currency`
- `payer_participant_id` FK -> `participants.participant_id`
- `category_id` nullable FK -> `categories.category_id`
- `comment`
- `status` (`open`, `settled`, `deleted`)
- `settlement_period_id` nullable FK -> `settlement_periods.settlement_period_id`
- `legacy_purchase_id` nullable
- `created_by_user_id` nullable FK -> `users.user_id`
- `created_at`
- `updated_at`
- `version`

Индексы:

- (`tenant_id`, `purchase_date`)
- (`tenant_id`, `status`)
- (`tenant_id`, `payer_participant_id`)
- (`tenant_id`, `settlement_period_id`)

Примечание: `version` нужен для optimistic locking при редактировании через bot/API.

### `purchase_participants`

Назначение: many-to-many связь покупки и участников, между которыми делится сумма.

Поля:

- `purchase_id` FK -> `purchases.purchase_id`
- `participant_id` FK -> `participants.participant_id`
- `share_amount` nullable
- `share_weight` nullable
- `created_at`

Primary key:

- (`purchase_id`, `participant_id`)

Для текущего поведения равного деления можно оставлять `share_amount` null и считать по текущей
fair rounding policy. Если позже появятся custom shares, таблица уже готова.

### `settlement_periods`

Назначение: исторический snapshot закрытого или переоткрытого периода.

Поля:

- `settlement_period_id` PK
- `tenant_id` FK
- `period_code` nullable unique per tenant
- `name`
- `status` (`closed`, `reopened`)
- `date_from`
- `date_to`
- `closed_at`
- `reopened_at` nullable
- `total_amount`
- `snapshot_json`
- `created_by_user_id` nullable FK -> `users.user_id`
- `created_at`
- `updated_at`

Snapshot requirements:

- хранить historical settlements как IDs + display labels;
- хранить total amount периода;
- хранить participant labels на момент закрытия;
- не пересчитывать historical settlements при генерации period report, если snapshot есть.

### `settlement_period_purchases`

Назначение: связь периода и покупок, входивших в snapshot.

Поля:

- `settlement_period_id` FK
- `purchase_id` FK
- `purchase_snapshot_json`
- `created_at`

Primary key:

- (`settlement_period_id`, `purchase_id`)

`purchase_snapshot_json` нужен, чтобы period report мог восстановить исторический вид покупки даже
после rename participant/category или изменения текущей purchase record.

### `reports`

Назначение: metadata и статус генерации отчетов.

Поля:

- `report_id` PK
- `tenant_id` FK
- `report_type` (`analytics`, `current`, `settlement_period`)
- `scope`
- `period_kind` nullable (`month`, `quarter`, `year`)
- `settlement_period_id` nullable FK
- `format`
- `status` (`pending`, `generated`, `failed`, `expired`)
- `storage_backend` (`local`, `object_storage`)
- `storage_key`
- `metadata_json`
- `warnings_json`
- `created_by_user_id` nullable FK
- `created_at`
- `generated_at`
- `expires_at` nullable

Отчеты не должны зависеть от локальной папки `reports/` в cloud mode. Локальная папка остается
только для desktop adapter.

### `audit_log`

Назначение: неизменяемая история важных операций.

Поля:

- `audit_log_id` PK
- `tenant_id` FK
- `actor_user_id` nullable FK -> `users.user_id`
- `actor_source` (`cli`, `gui`, `telegram`, `api`, `system`, `migration`)
- `event_type`
- `entity_type`
- `entity_id`
- `before_json`
- `after_json`
- `metadata_json`
- `created_at`
- `request_id` nullable

Обязательные события:

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

Audit log должен записывать display labels, IDs и source command/context. Для Telegram операций
важно фиксировать `telegram_user_id` в `metadata_json`, но actor identity должна ссылаться на
`user_id`.

### `bot_sessions`

Назначение: состояние диалога Telegram bot.

Поля:

- `bot_session_id` PK
- `tenant_id` nullable FK
- `telegram_account_id` FK
- `state`
- `payload_json`
- `last_message_id`
- `expires_at`
- `created_at`
- `updated_at`

Принцип: bot session хранит только conversational state. Доменная операция считается завершенной
только после записи в domain tables и audit log.

## YAML To Stable IDs Migration

### Source data

Текущий YAML содержит:

- `participants.yaml`: participant names, groups, statuses;
- `categories.yaml`: category names/statuses;
- `purchases.yaml`: purchase id, date, amount, payer name, participants names, category string,
  settled flag, settlement period id;
- `settlement_periods.yaml`: period id, dates, purchase ids, total amount, settlements with names.

### Migration steps

1. Создать default tenant:
   - `tenant_id = generated UUID`;
   - `name = "Default"` или имя из будущего import wizard.

2. Создать participants:
   - для каждого YAML participant создать `participant_id`;
   - `display_name = old name`;
   - `normalized_display_name = normalize(old name)`;
   - добавить alias в `participant_aliases` с `source = yaml_migration`.

3. Создать categories:
   - для каждой YAML category создать `category_id`;
   - сохранить display name/status;
   - unmatched purchase category strings либо создать как active category, либо записать в
     migration warnings.

4. Мигрировать purchases:
   - сохранить старый YAML `id` как `legacy_purchase_id`;
   - создать новый `purchase_id`;
   - `payer` name сопоставить через participants/aliases;
   - `participants` names разложить в `purchase_participants`;
   - category string сопоставить с `category_id`;
   - `settled` перевести в `status`.

5. Мигрировать settlement periods:
   - сохранить YAML `id` как `period_code` или `legacy_settlement_period_id`;
   - создать stable `settlement_period_id`;
   - `purchase_ids` сопоставить через `legacy_purchase_id`;
   - settlements сохранить в `snapshot_json` как participant IDs + display names + amount;
   - заполнить `settlement_period_purchases` с `purchase_snapshot_json`.

6. Создать audit entries:
   - `migration.imported` для tenant;
   - optional per-entity events only if needed for audit depth;
   - сохранить source file names/checksum в `metadata_json`.

### Ambiguity handling

Если одно display name встречается неоднозначно:

- не угадывать silently;
- создать migration warning;
- потребовать manual mapping;
- не импортировать покупку/period snapshot в "успешное" состояние без разрешения конфликта.

## Telegram Identity Flow

Первый вход Telegram user:

1. Bot получает `telegram_user_id`.
2. Ищет `telegram_accounts.telegram_user_id`.
3. Если account не найден:
   - создает или предлагает связать `users`;
   - предлагает выбрать tenant или принять invite;
   - создает/связывает participant внутри tenant.
4. Для каждой команды bot определяет:
   - `tenant_id`;
   - `user_id`;
   - `participant_id` внутри tenant.

Не делать:

- не использовать `telegram_user_id` как `participant_id`;
- не использовать Telegram username как имя участника без подтверждения;
- не смешивать tenants на основе одного chat id без явного membership model.

## MVP Scope

MVP может иметь один tenant и один participant на user, но схема должна позволять:

- несколько tenants;
- один user в нескольких tenants;
- несколько Telegram accounts per user в будущем, если потребуется;
- participants без linked user для людей, которые не пользуются ботом;
- архивирование участников и категорий без потери истории.

## Reporting Implications

Report builders должны получать данные уже с resolved display labels:

- current labels для текущих reports;
- snapshot labels для settlement period reports;
- IDs для machine-readable metadata.

`reports.metadata_json` должен сохранять:

- `tenant_id`;
- `report_type`;
- filters/scope;
- IDs involved;
- generated artifact list;
- warnings;
- source snapshot policy.

## Audit Log Examples

### Добавление покупки

```json
{
  "event_type": "purchase.added",
  "entity_type": "purchase",
  "entity_id": "<purchase_id>",
  "after_json": {
    "amount": "1250.00",
    "payer_participant_id": "<participant_id>",
    "participant_ids": ["<participant_id>"]
  }
}
```

### Редактирование покупки

```json
{
  "event_type": "purchase.edited",
  "entity_type": "purchase",
  "entity_id": "<purchase_id>",
  "before_json": {"amount": "1250.00"},
  "after_json": {"amount": "1300.00"}
}
```

### Закрытие периода

```json
{
  "event_type": "settlement_period.closed",
  "entity_type": "settlement_period",
  "entity_id": "<settlement_period_id>",
  "metadata_json": {
    "purchase_count": 12,
    "total_amount": "18450.00",
    "snapshot_source": "close_flow"
  }
}
```

### Переоткрытие периода

```json
{
  "event_type": "settlement_period.reopened",
  "entity_type": "settlement_period",
  "entity_id": "<settlement_period_id>",
  "metadata_json": {
    "purchase_ids_returned_to_open_scope": ["<purchase_id>"]
  }
}
```

### Изменение справочников

```json
{
  "event_type": "participant.renamed",
  "entity_type": "participant",
  "entity_id": "<participant_id>",
  "before_json": {"display_name": "Pavel"},
  "after_json": {"display_name": "Павел"}
}
```

### Генерация отчета

```json
{
  "event_type": "report.generated",
  "entity_type": "report",
  "entity_id": "<report_id>",
  "metadata_json": {
    "report_type": "settlement_period",
    "format": "pdf",
    "storage_key": "reports/<tenant_id>/<report_id>/settlement_period.pdf"
  }
}
```

## Open Questions For CLOUD.0

- Какой формат stable ID выбрать: UUIDv7, ULID или database-generated UUID.
- Нужна ли membership table `tenant_members` сразу в MVP.
- Как приглашать пользователей в tenant через Telegram.
- Как хранить custom shares: `share_amount`, `share_percent` или `share_weight`.
- Нужно ли soft delete для purchases или достаточно `status = deleted`.
- Где хранить report artifacts: Yandex Object Storage bucket naming and retention.
- Какой уровень audit нужен для personal/local use vs shared tenant use.

## Decision

Серверная модель должна строиться вокруг stable IDs и tenant isolation. YAML display names
мигрируются в display labels и aliases, но не становятся primary keys. Telegram identity связывается
через `telegram_user_id -> user_id -> participant_id`, а все доменные операции пишут audit log.

## CLOUD.5 Update

CLOUD.5 created the executable PostgreSQL schema foundation:

- `src/expense_splitter/db/migrations/0001_initial.sql`;
- schema metadata in `src/expense_splitter/db/models.py`;
- future PostgreSQL repository contract stub;
- optional `cloud` dependencies for SQLAlchemy 2.x, Alembic and psycopg.

The selected stable ID strategy for the first server schema is database-generated UUID via
PostgreSQL `pgcrypto`/`gen_random_uuid()`. YAML offline mode is unchanged.
