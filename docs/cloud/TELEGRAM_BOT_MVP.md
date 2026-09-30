# CLOUD.7 — Telegram Bot MVP

Дата: 2026-07-01
Статус: implemented as framework-neutral MVP adapter.

## Цель

CLOUD.7 добавляет Telegram bot слой, который принимает текстовые команды, вызывает
существующие services и возвращает ответы, готовые для будущего `sendMessage` и
`sendDocument`.

Bot code не пишет в YAML напрямую и не вызывает CLI. В тестовом offline режиме он
использует `YamlExpenseRepository` только через service/repository boundary. На сервере
тот же handler должен работать через будущий PostgreSQL repository.

## Реализованные команды

- `/start`
- `/help`
- `/add_purchase`
- `/purchases`
- `/edit_purchase <id> amount=1250 category=еда`
- `/delete_purchase <id> DELETE_PURCHASE`
- `/current_pdf`
- `/current_xlsx`
- `/analytics month 2026 7 xlsx`
- `/periods`
- `/period_report <id> pdf|xlsx`
- `/close_period from=2026-07-01 to=2026-07-31 name=Июль confirm=CLOSE_PERIOD`
- `/cancel`

## Защита от человеческого фактора

Редактирование покупки идет через `PurchaseService.update_purchase`, поэтому:

- изменяются только существующие покупки;
- закрытые покупки защищены service layer;
- плательщик и участники валидируются по справочнику участников;
- поля передаются как patch, без прямой записи в storage.

Удаление покупки идет через `PurchaseService.delete_purchase` и требует точное
подтверждение:

```text
DELETE_PURCHASE
```

Если пользователь вызывает `/delete_purchase <id>` без подтверждения, бот сначала
возвращает безопасный preview и просит повторить команду с confirm marker.

Закрытие периода взаиморасчетов также требует точное подтверждение:

```text
CLOSE_PERIOD
```

Команда `/close_period` вызывает `SettlementService.close_period`, поэтому snapshot,
`purchase_ids`, итоговые переводы и статусы покупок создаются той же бизнес-логикой, что
и в desktop/CLI. Без `confirm=CLOSE_PERIOD` бот возвращает предупреждение и не меняет
данные.

## Report delivery

Команды отчетов вызывают `ReportService` и возвращают `BotReply.documents`.
Telegram SDK adapter должен отправлять эти файлы через `sendDocument`; bot session не
хранит сами файлы.

Поддержанные MVP сценарии:

- current open report PDF;
- current open report XLSX;
- analytics month/quarter/year PDF или XLSX;
- historical settlement period report PDF или XLSX.

## Архитектура

Создан пакет:

```text
src/expense_splitter/telegram_bot/
  __init__.py
  adapter.py
  handlers.py
  keyboards.py
  messages.py
  states.py
```

`handlers.py` содержит command routing и conversation flow. `adapter.py` содержит
framework-neutral DTOs:

- `TelegramContext`;
- `BotReply`;
- `BotServices`;
- `InMemoryBotSessionStore`;
- `TelegramBotAdapter`.

`keyboards.py` хранит framework-neutral описания кнопок для будущего aiogram/webhook
wiring.

## Зависимости

`aiogram` добавлен как optional dependency:

```toml
telegram = ["aiogram>=3.10; python_version < '3.14'"]
```

Он также входит в `cloud` extra с marker для Python `< 3.14`. Текущие тесты не требуют
реального Telegram SDK, поэтому CLOUD.7 остается проверяемым в Python 3.14 окружении.

## Ограничения

- Реальный webhook endpoint и long polling runner не включены в CLOUD.7.
- Telegram identity resolution пока представлен `TelegramContext`; связь
  `telegram_user_id -> user_id -> tenant_id -> participant_id` остается следующим
  серверным этапом.
- Audit log для `purchase.added`, `purchase.edited`, `purchase.deleted` описан в cloud
  документах, но live persistence будет реализована вместе с PostgreSQL repository.
- Команда закрытия периода добавлена с точным маркером; role-based admin authorization
  будет добавлена после identity resolution.
- Переоткрытие периодов из Telegram пока не включено.
