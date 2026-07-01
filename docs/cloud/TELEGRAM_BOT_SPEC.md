# CLOUD.0 — Telegram Bot Spec

Дата: 2026-07-01
Статус: UX/spec design plus CLOUD.7 framework-neutral Telegram bot MVP adapter.

## Цель

Описать Telegram MVP behavior для Expense Splitter без реализации handlers. Bot должен быть thin
adapter поверх backend/API/service layer.

## Bot Principles

- Bot never writes YAML.
- Bot never calls CLI commands.
- Bot never stores permanent report files.
- Bot resolves user/tenant via backend.
- Bot sends PDF/XLSX via `sendDocument`.
- Bot messages are Russian-first.
- Every mutating action goes through backend and audit log.

## Commands

### `/start`

Purpose:

- greet user;
- resolve or create Telegram account link;
- choose tenant if needed;
- explain main commands.

Message:

```text
Привет! Я помогу добавить покупки и получить отчеты Expense Splitter.
Сначала выберите группу расходов или создайте новую.
```

### `/help`

Shows commands:

- `/add_purchase` — добавить покупку;
- `/edit_purchase` — исправить открытую покупку;
- `/delete_purchase` — удалить открытую покупку с точным подтверждением;
- `/current_pdf` — текущие взаиморасчеты PDF;
- `/current_xlsx` — текущие взаиморасчеты XLSX;
- `/analytics` — отчет за месяц/квартал/год;
- `/periods` — список периодов взаиморасчетов;
- `/period_report` — отчет по закрытому периоду;
- `/close_period` — закрыть период с точным подтверждением;
- `/cancel` — отменить текущий диалог.

### `/add_purchase`

Starts conversational flow for adding purchase.

### `/edit_purchase`

Updates an existing open purchase through `PurchaseService.update_purchase`.

Example:

```text
/edit_purchase p1 amount=1250 category=еда comment=исправлено
```

Settled purchases are protected by service layer.

### `/delete_purchase`

Deletes an open purchase through `PurchaseService.delete_purchase`.

The command requires exact marker:

```text
/delete_purchase p1 DELETE_PURCHASE
```

Without the marker, bot returns a warning and does not change data.

### `/current_pdf`

Requests current open report in PDF:

```python
ReportService.create_current_report(tenant_id, scope="open", formats={"pdf"})
```

Bot sends returned PDF with `sendDocument`.

### `/current_xlsx`

Requests current open report in XLSX.

### `/analytics`

Starts period selection:

- month;
- quarter;
- year;
- format PDF/XLSX/both.

### `/periods`

Lists settlement periods:

- latest first;
- status closed/reopened;
- total amount;
- purchase count;
- short period code/name.

### `/period_report`

Asks user to choose settlement period and format. Uses historical snapshot report.

### `/close_period`

Closes a settlement period through `SettlementService.close_period`.

The command requires exact marker:

```text
/close_period from=2026-07-01 to=2026-07-31 name=Июль confirm=CLOSE_PERIOD
```

Without `confirm=CLOSE_PERIOD`, bot returns a warning and does not change data.

### `/cancel`

Clears `bot_sessions` state for current telegram account.

Message:

```text
Действие отменено.
```

## Add Purchase Conversation

State machine:

1. `awaiting_purchase_name`
2. `awaiting_amount`
3. `awaiting_payer`
4. `awaiting_participants`
5. `awaiting_category`
6. `awaiting_date`
7. `awaiting_comment`
8. `confirm_purchase`

Happy path:

```text
Покупка: Кофе
Сумма: 350
Плательщик: Павел
Участники: Павел, Сергей
Категория: кофе
Дата: сегодня
Комментарий: после встречи
```

Confirmation message:

```text
Проверьте покупку:
Кофе — 350.00
Плательщик: Павел
Участники: Павел, Сергей
Категория: кофе
Дата: 2026-07-01

Сохранить?
```

On confirm:

- bot sends request to backend;
- backend creates purchase;
- audit log records `purchase.added`;
- bot replies:

```text
Покупка добавлена.
```

## Validation UX

Amount invalid:

```text
Не понял сумму. Введите число, например 1250 или 1250.50.
```

Unknown participant:

```text
Участник не найден. Выберите из списка или добавьте его в справочник.
```

Ambiguous alias:

```text
Нашлось несколько похожих участников. Выберите нужного.
```

Backend error:

```text
Не удалось выполнить действие. Попробуйте еще раз или обратитесь к администратору.
```

No stack traces or internal paths in Telegram messages.

## Report Request UX

Current report:

```text
Формирую PDF по открытым покупкам. Данные не изменяются.
```

Settlement period reopened warning:

```text
Период был переоткрыт. Отчет показывает сохраненный snapshot периода.
```

Empty report:

```text
За выбранный период данных нет. Отчет не сформирован.
```

## Tenant Selection

MVP:

- one default tenant per user or invite.

Future:

- `/groups` or `/tenant` command;
- user can switch active tenant;
- every action shows or stores selected tenant in `bot_sessions`.

## Security Rules

- Bot token from secret store only.
- Webhook secret validated by backend.
- Do not log full Telegram update if it may contain personal text.
- Do not expose `DATABASE_URL`.
- Do not store report files in bot session.

## Out Of Scope For CLOUD.0

- aiogram/python-telegram-bot code;
- webhook deployment;
- real bot token;
- cloud resources;
- database migrations.
