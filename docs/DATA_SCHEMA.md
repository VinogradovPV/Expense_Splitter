# Схема данных Expense Splitter

Все YAML-файлы сохраняются в UTF-8. Текущая схема покупок — v2.

## purchases.yaml

```yaml
schema_version: 1
purchases:
  - id: p1
    date: '2026-06-18'
    purchase_name: Кофе
    amount: '150.00'
    payer: Павел
    participants: [Павел, Сергей]
    category: кофе
    comment: null
    settled: false
    settlement_period_id: null
```

`amount` читается как Decimal; дата — `YYYY-MM-DD`. `participants` не может быть пустым. Поле
`purchase_name` каноническое; пустое значение нормализуется в `н/д`.

### Совместимость v1

Legacy-поле `title` поддерживается при чтении как alias `purchase_name`, но новые записи используют
только `purchase_name`. Отсутствующие `settled` и `settlement_period_id` означают открытую покупку.

## participants.yaml

```yaml
participants:
  - name: Павел
groups:
  - name: Команда
    members: [Павел, Сергей]
```

Участники и группы хранятся в одном файле и сохраняются при reset-test.

## categories.yaml

```yaml
schema_version: 1
categories:
  - кофе
  - еда
  - без категории
```

Категории непустые и уникальны без учёта регистра. Новые значения GUI добавляет только после
подтверждения. Несколько категорий покупки хранятся строкой через запятую для совместимости схемы.

## settlement_periods.yaml

```yaml
schema_version: 1
settlement_periods:
  - id: settlement_2026_06_30_001
    name: Июнь
    status: closed
    date_from: '2026-06-01'
    date_to: '2026-06-30'
    purchase_ids: [p1]
    total_amount: '150.00'
    settlements: []
```

Период хранит выбранные покупки и snapshot переводов. Reopen не удаляет запись периода.

## Backups и атомарная запись

Перед заменой существующего YAML создаётся `<name>.yaml.<timestamp>.bak`, затем временный файл
атомарно заменяет основной. Ручной backup GUI копирует все YAML в `data/backups/<timestamp>/`.

Reset-test требует `RESET_TEST_DATA`, создаёт backups и записывает пустые списки purchases и
settlement periods. Participants, groups и categories не изменяются.

## Справочники active/archived

Новые сохранения участников поддерживают поле `status`:

```yaml
participants:
  - name: Павел
    status: active
  - name: Старый участник
    status: archived
```

Старые записи без `status` читаются как `active`. Архивные участники не показываются в новых
покупках, но остаются в истории и расчетах.

Новые сохранения категорий поддерживают расширенный формат:

```yaml
schema_version: 1
categories:
  - name: кофе
    status: active
  - name: старая категория
    status: archived
```

Старый формат `categories: [кофе, еда]` читается как список активных категорий. `load_categories()`
по умолчанию возвращает только активные категории; `load_category_entries()` возвращает записи со
статусами. Если покупка хранит несколько категорий строкой через запятую, переименование меняет
только совпавший элемент строки.
