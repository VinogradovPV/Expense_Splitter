# TG-PREP.7 — Security Prep Checklist

Дата: 2026-07-01
Ветка: `cloud/telegram-prep`
Статус: baseline prepared; реальные tokens, service account keys и cloud resources не создавались.

## Цель

Не допустить попадания Telegram/Yandex/PostgreSQL секретов, ключей и `.env` файлов в Git перед
началом Telegram bot и Yandex Cloud этапов.

## Git Ignore Baseline

`.gitignore` должен содержать:

```gitignore
.env
.env.*
!.env.example
*.key
*.pem
*.p12
service-account*.json
telegram_token*.txt
```

Статус: выполнено.

Дополнительно в проекте уже игнорируются generated artifacts и локальные пользовательские данные:

- `reports/`
- `.tmp/`
- `build/`
- `dist/`
- caches
- `*.bak`
- `data/*.yaml`

## Safe Env Template

Создан безопасный шаблон `.env.example`.

Содержимое использует только placeholders:

```env
TELEGRAM_BOT_TOKEN=replace_me
TELEGRAM_WEBHOOK_SECRET=replace_me
DATABASE_URL=postgresql+psycopg://user:password@host:5432/dbname
YANDEX_CLOUD_FOLDER_ID=replace_me
YANDEX_OBJECT_STORAGE_BUCKET=replace_me
```

Правила:

- `.env.example` можно коммитить.
- `.env` нельзя коммитить.
- `.env.*` нельзя коммитить, кроме `.env.example`.
- Реальные tokens/passwords/service account keys запрещены в репозитории и в истории Git.

## Secret Marker Search

Выполнена команда:

```powershell
git grep -n -E "(BOT_TOKEN|TELEGRAM|YANDEX|YC_|SECRET|PASSWORD|TOKEN|DATABASE_URL|SERVICE_ACCOUNT|PRIVATE_KEY)" -- . ':!docs/cloud/SECURITY_PREP_CHECKLIST.md' ':!.env.example'
```

Результат:

```text
docs/prompts/expense_splitter_pre_telegram_bot_step_by_step_v1_ru.md:476:TELEGRAM_BOT_TOKEN=replace_me
docs/prompts/expense_splitter_pre_telegram_bot_step_by_step_v1_ru.md:477:TELEGRAM_WEBHOOK_SECRET=replace_me
docs/prompts/expense_splitter_pre_telegram_bot_step_by_step_v1_ru.md:478:DATABASE_URL=postgresql+psycopg://user:password@host:5432/dbname
docs/prompts/expense_splitter_pre_telegram_bot_step_by_step_v1_ru.md:479:YANDEX_CLOUD_FOLDER_ID=replace_me
docs/prompts/expense_splitter_pre_telegram_bot_step_by_step_v1_ru.md:480:YANDEX_OBJECT_STORAGE_BUCKET=replace_me
docs/prompts/expense_splitter_pre_telegram_bot_step_by_step_v1_ru.md:486:git grep -n -E "(BOT_TOKEN|TELEGRAM|YANDEX|YC_|SECRET|PASSWORD|TOKEN|DATABASE_URL|SERVICE_ACCOUNT|PRIVATE_KEY)" -- . ':!docs/cloud/SECURITY_PREP_CHECKLIST.md' ':!.env.example'
docs/prompts/expense_splitter_pre_telegram_bot_step_by_step_v1_ru.md:530:   - `TELEGRAM_YANDEX_CLOUD_ARCHITECTURE.md`;
docs/prompts/expense_splitter_pre_telegram_bot_step_by_step_v1_ru.md:533:   - `TELEGRAM_BOT_SPEC.md`;
```

Классификация:

- Найдены только документационные placeholders `replace_me`.
- `DATABASE_URL` в prompt содержит example value, не реальный пароль.
- Реальные Telegram tokens не найдены.
- Реальные Yandex service account keys не найдены.
- `PRIVATE_KEY`, `SERVICE_ACCOUNT`, `YC_` с реальными значениями не найдены.

## Yandex Cloud Rules

Для future deployment:

- использовать Yandex Lockbox или environment secrets;
- не хранить service account JSON в репозитории;
- не хранить `.pem`, `.key`, `.p12`;
- не писать tokens в docs, tests, screenshots, logs или issue comments;
- не передавать секреты в CLI args, если они могут попасть в shell history;
- использовать короткоживущие credentials там, где это возможно.

## Telegram Bot Rules

- Bot token хранится только в runtime secret store или локальном `.env`, который ignored.
- Webhook secret хранится только в secret store или ignored `.env`.
- Bot logs не должны печатать token, webhook secret, database URL password.
- Telegram `telegram_user_id` не является секретом, но является user identifier; не публиковать
  реальные IDs в публичных fixtures без необходимости.

## Database Rules

- `DATABASE_URL` с реальным password не коммитить.
- В docs использовать только placeholders.
- В tests использовать local/temp database URL без реальных credentials.
- Connection strings в logs должны маскировать password.

## Pre-Commit Manual Checklist

Перед каждым cloud/security commit:

1. `git status --short`
2. Проверить staged files:
   `git diff --cached --name-only`
3. Убедиться, что нет `.env`, `.env.*`, `*.key`, `*.pem`, `*.p12`,
   `service-account*.json`, `telegram_token*.txt`.
4. Выполнить secret marker grep.
5. Выполнить `scripts\qa\check_text_encoding.py`.
6. Выполнить `git diff --check`.

## Incident Rule

Если реальный token/key/password попал в Git:

1. Немедленно считать секрет скомпрометированным.
2. Отозвать/rotate token в Telegram/Yandex/PostgreSQL.
3. Не пытаться "просто удалить файл следующим commit" как единственную меру.
4. Решить отдельно, нужна ли история Git rewrite, с явным подтверждением пользователя.

## Decision

Security baseline готов для дальнейшей подготовки Telegram/Yandex Cloud контура: `.env.example`
разрешен, реальные `.env`/keys/service account files ignored, secret marker grep выполнен и не
выявил реальных секретов.
