# Expense Splitter — пошаговая инструкция для Codex по дальнейшей работе после TG-PREP

Дата подготовки: 2026-07-01
Целевая ветка: `cloud/telegram-prep`
Текущий статус: TG-PREP завершен как подготовительный пакет; Telegram-бот, FastAPI backend, PostgreSQL migrations, Yandex Cloud deploy и реальные secrets пока не реализуются.

---

## 0. Назначение документа

Этот документ задает дальнейший порядок работ над Expense Splitter после этапа TG-PREP.

Главная цель следующего направления — подготовить проект к автоматизации занесения покупок через Telegram-бота и обработке данных на сервере в Yandex Cloud, не ломая текущий стабильный desktop/CLI режим на локальных YAML-файлах.

Ключевой принцип: **не начинать с Telegram-бота**. Сначала нужно зафиксировать архитектуру, затем выделить service/repository слой, подготовить модель данных, контракт отчетов и security baseline. Только после этого можно писать FastAPI и Telegram bot. Да, звучит скучно. Зато потом бот не будет писать в `purchases.yaml` на сервере и делать вид, что это облачная архитектура.

---

## 1. Исходные документы TG-PREP

Перед началом работ Codex должен использовать следующие документы как источник контекста:

```text
README.md
docs/reports/prod_ready_progress_report.md
docs/cloud/SERVER_READINESS_AUDIT.md
docs/cloud/SERVICE_REPOSITORY_BOUNDARY.md
docs/cloud/DATABASE_READINESS.md
docs/cloud/REPORT_DELIVERY_CONTRACT.md
docs/cloud/SECURITY_PREP_CHECKLIST.md
docs/cloud/CLOUD_0_START_PLAN.md
.env.example
.gitignore
```

Если какие-то документы отсутствуют в локальной ветке, сначала остановиться и сообщить blocker. Не придумывать архитектуру заново по памяти.

---

## 2. Общие жесткие правила для всех следующих этапов

### 2.1. Нельзя делать без отдельного явного разрешения

Запрещено:

```text
- писать production Telegram bot code до CLOUD.7;
- создавать реальные Yandex Cloud resources до CLOUD.8;
- добавлять реальные Telegram/Yandex/PostgreSQL secrets;
- коммитить .env, .env.*, ключи, service-account JSON;
- ломать YAML offline mode;
- удалять или переписывать Desktop GUI/CLI сценарии;
- менять settlement close/reopen semantics без отдельного этапа;
- делать final release/tag;
- выполнять git reset --hard;
- выполнять git clean -fd;
- делать force push.
```

### 2.2. Generated artifacts не коммитить

Не добавлять в Git:

```text
reports/
.tmp/
build/
dist/
.pytest_cache/
.ruff_cache/
__pycache__/
*.egg-info/
*.bak
data/*.yaml
.env
.env.*
*.key
*.pem
*.p12
service-account*.json
telegram_token*.txt
```

Исключение: `.env.example` можно коммитить, если в нем только placeholders.

### 2.3. UTF-8 и mojibake

Все новые документы, Python-файлы, YAML, TOML, Markdown сохранять в UTF-8.

Перед проверками в PowerShell:

```powershell
chcp 65001
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
```

Все тесты, которые читают текстовые файлы, должны использовать:

```python
read_text(encoding="utf-8")
```

Не использовать `read_text()` / `write_text()` без `encoding` для текстовых файлов.

### 2.4. Git/GitHub discipline

Перед каждым этапом:

```powershell
git status --short
git branch --show-current
git log --oneline -5
```

Перед commit:

```powershell
git status --short
git diff --check
git diff --cached --name-only
```

Если staged попали generated artifacts или secrets — остановиться, убрать из staging, объяснить.

---

## 3. Целевой roadmap

Рекомендуемый порядок:

```text
CLOUD.0  — архитектурное проектирование Telegram + Yandex Cloud
CLOUD.1  — repository protocols only
CLOUD.2  — YAML repository adapter
CLOUD.3  — thin service layer extraction
CLOUD.4  — ReportService и report output adapters
CLOUD.5  — PostgreSQL schema and migrations design/code
CLOUD.6  — FastAPI backend MVP
CLOUD.7  — Telegram bot MVP
CLOUD.8  — Yandex Cloud deployment MVP
CLOUD.9  — production hardening and release gate
```

Важно: **CLOUD.7 начинается только после CLOUD.0–CLOUD.6**. Если начать с бота раньше, бизнес-логика расползется в Telegram-handlers, а потом ее придется выковыривать оттуда пинцетом и сожалением.

---

# CLOUD.0 — архитектурное проектирование Telegram + Yandex Cloud

## Цель

Создать полный архитектурный пакет для cloud/server/bot-направления без написания production-кода.

## Входные документы

```text
docs/cloud/SERVER_READINESS_AUDIT.md
docs/cloud/SERVICE_REPOSITORY_BOUNDARY.md
docs/cloud/DATABASE_READINESS.md
docs/cloud/REPORT_DELIVERY_CONTRACT.md
docs/cloud/SECURITY_PREP_CHECKLIST.md
docs/cloud/CLOUD_0_START_PLAN.md
```

## Создать документы

```text
docs/cloud/TELEGRAM_YANDEX_CLOUD_ARCHITECTURE.md
docs/cloud/API_CONTRACT.md
docs/cloud/DATABASE_SCHEMA.md
docs/cloud/TELEGRAM_BOT_SPEC.md
docs/cloud/MIGRATION_PLAN.md
docs/cloud/SECURITY_MODEL.md
docs/cloud/IMPLEMENTATION_ROADMAP.md
```

## Обязательные решения

1. MVP architecture: `FastAPI backend service/container + PostgreSQL + Object Storage`.
2. Serverless описать как future optimization, не как стартовый путь.
3. Telegram bot не пишет в YAML напрямую.
4. Telegram bot не вызывает CLI-команды.
5. Bot вызывает service layer через backend/API.
6. Reports генерируются через `ReportService`, а Telegram только отправляет PDF/XLSX через `sendDocument`.
7. PostgreSQL строится на stable IDs, а не на display names.
8. YAML offline mode сохраняется.

## Проверки

```powershell
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
git diff --check
git status --short --ignored
```

Если менялись только docs, полный pytest не обязателен. Если менялись `.gitignore`, `.env.example`, Python code или workflows — выполнить полный quality gate.

## Commit

```powershell
git add docs/cloud README.md
git commit -m "docs: design telegram yandex cloud architecture"
git push origin cloud/telegram-prep
```

## Критерии готовности

- Все 7 архитектурных документов созданы.
- В документах есть explicit запрет на bot code/cloud deploy/secrets в CLOUD.0.
- Описаны API, DB schema, Telegram flows, migration, security и roadmap.
- Проверки UTF-8 и `git diff --check` пройдены.
- Generated artifacts и secrets не staged.

---

# CLOUD.1 — repository protocols only

## Цель

Добавить минимальные repository protocols и DTO-команды без изменения поведения CLI/GUI.

## Создать структуру

```text
src/expense_splitter/repositories/
  __init__.py
  protocols.py

tests/test_repository_protocols.py
```

## Что добавить в `protocols.py`

Минимально:

```text
PurchaseRepository
ParticipantRepository
CategoryRepository
SettlementPeriodRepository
ExpenseUnitOfWork
PurchasePatch
```

Допускается добавить command DTO:

```text
AddPurchaseCommand
ClosePeriodCommand
ReportRequest
```

Но не надо превращать protocols в энциклопедию будущего. Это первый слой, а не попытка предсказать все страдания проекта на два года вперед.

## Жесткие ограничения

- Не импортировать `typer`, `rich`, `tkinter`, `messagebox`, `subprocess`.
- Не добавлять SQLAlchemy/PostgreSQL.
- Не менять `storage.py`.
- Не переводить CLI/GUI на protocols в этом этапе.
- Не менять YAML schema.
- Не менять расчеты.

## Тесты

Проверить:

1. protocols импортируются без GUI/CLI dependencies;
2. DTO создаются и типизируются;
3. `python -m compileall` проходит;
4. существующий test suite не изменился по поведению.

Команды:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_repository_protocols.py -v
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
.\.venv\Scripts\python.exe -m ruff check src tests
git diff --check
```

## Commit

```powershell
git add src tests docs README.md
git commit -m "feat: add repository protocols for cloud adapters"
git push origin cloud/telegram-prep
```

## Критерии готовности

- Protocols есть.
- Старый CLI/GUI не сломан.
- Полный pytest зеленый.
- Нет cloud code, secrets, DB dependencies.

---

# CLOUD.2 — YAML repository adapter

## Цель

Добавить YAML-backed repository adapter поверх текущего `storage.py`, сохранив offline desktop режим.

## Создать файлы

```text
src/expense_splitter/repositories/yaml_repository.py
tests/test_yaml_repository.py
```

## Основная идея

`YamlExpenseRepository` должен принимать `data_dir: Path` и реализовывать protocols через существующие функции `storage.py`.

Рекомендуемый local tenant:

```python
LOCAL_TENANT_ID = "local"
```

На первом шаге `tenant_id` можно валидировать как `local`, но signatures должны уже принимать `tenant_id`, чтобы PostgreSQL adapter потом не ломал service API.

## Обязательные требования

1. Не переписывать `storage.py` без необходимости.
2. Не менять формат YAML.
3. Сохранить backups и atomic write behavior текущего storage.
4. Repository должен возвращать те же domain objects, что и storage functions.
5. Ошибки storage должны оставаться дружелюбными.

## Тесты

Проверить:

1. repository list/add/update/replace purchases работает в temp data dir;
2. participants/categories/settlement periods читаются и сохраняются;
3. tenant_id != `local` дает понятную ошибку или controlled unsupported case;
4. corrupted YAML дает прежний `StorageError`;
5. backups создаются там, где текущий storage их создает.

Команды:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_yaml_repository.py -v
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
.\.venv\Scripts\python.exe -m ruff check src tests
git diff --check
```

## Commit

```powershell
git add src tests docs README.md
git commit -m "feat: add YAML repository adapter"
git push origin cloud/telegram-prep
```

## Критерии готовности

- `YamlExpenseRepository` есть.
- Он покрыт тестами.
- CLI/GUI все еще работают старым путем.
- Нет PostgreSQL/FastAPI/Telegram code.

---

# CLOUD.3 — thin service layer extraction

## Цель

Постепенно вынести use-case orchestration из CLI/GUI в services, не меняя публичное поведение.

## Создать структуру

```text
src/expense_splitter/services/
  __init__.py
  purchases_service.py
  directories_service.py
  settlement_service.py
  report_service.py

tests/test_purchase_service.py
tests/test_directory_service.py
tests/test_settlement_service.py
tests/test_report_service.py
```

## Порядок подэтапов

### CLOUD.3.1 — PurchaseService

Функции:

```text
list_purchases
add_purchase
update_purchase
delete_purchase
```

Правила:

- settled purchases защищены;
- delete open purchase требует confirm;
- normalizations должны совпадать с текущими CLI/GUI;
- сервис не знает про Typer/Tkinter.

### CLOUD.3.2 — DirectoryService

Функции:

```text
list/add/rename/archive/delete participants
list/add/rename/archive/delete categories
```

Правила:

- used participant нельзя физически удалить;
- used category очищается только по typed confirm, если это уже текущее поведение;
- cascade rename сохраняется.

### CLOUD.3.3 — SettlementService

Функции:

```text
balances(scope)
settlements(scope)
preview_period
suggest_next_period
close_period
reopen_period
rename_period
delete_empty_periods
```

Правила:

- close/reopen должны работать через UnitOfWork boundary;
- в YAML adapter transaction может быть best-effort, но service API должен быть готов к настоящей транзакции.

### CLOUD.3.4 — Initial ReportService wrapper

Функции:

```text
build_current_report
build_analytics_report
build_settlement_period_report
```

На этом этапе можно оборачивать существующие generators, но service должен возвращать result DTO, а не заставлять adapters парсить локальные папки.

## Что пока НЕ делать

- Не переводить весь CLI/GUI сразу.
- Не писать Telegram bot.
- Не писать FastAPI.
- Не добавлять DB.
- Не менять output layout отчетов без отдельного решения.

## Проверки

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_purchase_service.py -v
.\.venv\Scripts\python.exe -m pytest tests\test_directory_service.py -v
.\.venv\Scripts\python.exe -m pytest tests\test_settlement_service.py -v
.\.venv\Scripts\python.exe -m pytest tests\test_report_service.py -v
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
.\.venv\Scripts\python.exe -m ruff check src tests
git diff --check
```

## Commit policy

Лучше делать отдельные commits по подэтапам:

```text
feat: add purchase service
feat: add directory service
feat: add settlement service
feat: add report service wrapper
```

## Критерии готовности

- Services есть и не импортируют UI/CLI.
- YAML repository используется в сервисных тестах.
- Старые CLI/GUI тесты зеленые.
- Business behavior не изменился.

---

# CLOUD.4 — ReportService и output adapters

## Цель

Подготовить генерацию PDF/XLSX для Telegram/FastAPI так, чтобы bot не знал про локальные `reports/...`.

## Создать/обновить

```text
src/expense_splitter/services/report_service.py
src/expense_splitter/reports/output_adapters.py
src/expense_splitter/reports/result.py

tests/test_report_service.py
tests/test_report_output_adapters.py
```

## DTO

Минимально:

```python
@dataclass(frozen=True)
class ReportFile:
    format: str
    filename: str
    content_type: str
    size_bytes: int | None
    storage_key: str | None
    local_path: Path | None
    checksum_sha256: str | None

@dataclass(frozen=True)
class ReportResult:
    report_id: str
    report_type: str
    formats: set[str]
    files: list[ReportFile]
    created_at: datetime
    expires_at: datetime | None
    storage_backend: str
    telegram_caption: str
    warnings: list[dict[str, object]]
    metadata: dict[str, object]
```

## Output adapters

```text
LocalReportOutputAdapter
TempReportOutputAdapter
ObjectStorageReportOutputAdapter  # stub/future, без реального Yandex SDK на этом этапе
```

## Требования

1. Telegram/FastAPI future layer получает `ReportResult`.
2. Local desktop может продолжать использовать текущие папки.
3. Temp adapter подходит для backend tests.
4. ObjectStorage adapter пока может быть interface/stub, без реального upload.
5. Report generation остается read-only для доменных данных.
6. PDF font requirement должен быть проверяемым healthcheck/helper.

## Проверки

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_report_service.py -v
.\.venv\Scripts\python.exe -m pytest tests\test_report_output_adapters.py -v
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
.\.venv\Scripts\python.exe -m ruff check src tests
git diff --check
```

## Commit

```powershell
git add src tests docs README.md
git commit -m "feat: add report service delivery contract"
git push origin cloud/telegram-prep
```

## Критерии готовности

- `ReportResult` и `ReportFile` есть.
- Current/analytics/settlement-period reports могут возвращаться как files для Telegram delivery.
- Bot по-прежнему не пишется.

---

# CLOUD.5 — PostgreSQL schema and migrations

## Цель

Добавить серверную relational data model и миграции, сохранив YAML offline mode.

## Предварительное условие

CLOUD.0–CLOUD.4 должны быть закрыты.

## Возможные зависимости

Выбрать и зафиксировать в docs:

```text
SQLAlchemy 2.x
Alembic
psycopg
```

Не добавлять зависимости без обновления `pyproject.toml`, docs и tests.

## Создать структуру

```text
src/expense_splitter/db/
  __init__.py
  models.py
  session.py
  migrations/ или alembic/

src/expense_splitter/repositories/postgres_repository.py

tests/test_database_schema.py
tests/test_postgres_repository_contract.py
```

## Таблицы MVP

```text
tenants
users
telegram_accounts
participants
participant_aliases
categories
purchases
purchase_participants
settlement_periods
settlement_period_purchases
reports
audit_log
bot_sessions
```

## Требования

1. Все доменные таблицы имеют `tenant_id`.
2. Display name не primary key.
3. Stable IDs: UUID/ULID, решение зафиксировать.
4. `telegram_user_id` не равно `participant_id`.
5. Close/reopen periods должны быть транзакционными в DB repository.
6. Settlement period snapshot должен хранить historical labels и IDs.
7. Reports metadata хранится отдельно от report artifacts.
8. Audit log фиксирует важные операции.

## Локальная разработка

Добавить `docker-compose.yml` только если принято решение использовать Docker для local PostgreSQL. Если Docker добавляется, secrets все равно не коммитить.

## Проверки

Минимум:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_database_schema.py -v
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
.\.venv\Scripts\python.exe -m ruff check src tests
git diff --check
```

Если нужен live PostgreSQL, тесты должны быть optional/integration-marked и не ломать обычный CI без базы.

## Commit

```powershell
git add src tests docs README.md pyproject.toml docker-compose.yml alembic.ini
# добавлять только реально созданные файлы
git commit -m "feat: add PostgreSQL schema foundation"
git push origin cloud/telegram-prep
```

## Критерии готовности

- Schema описана и/или реализована миграциями.
- Offline YAML mode не сломан.
- Secrets не добавлены.
- Unit tests зеленые.

---

# CLOUD.6 — FastAPI backend MVP

## Цель

Добавить backend API как отдельный adapter поверх services/repositories.

## Создать структуру

```text
src/expense_splitter/server/
  __init__.py
  app.py
  config.py
  dependencies.py
  schemas.py
  routes/
    purchases.py
    reports.py
    settlement_periods.py
    health.py

tests/test_server_health.py
tests/test_server_purchases_api.py
tests/test_server_reports_api.py
```

## API MVP

```text
GET  /health
POST /api/purchases
GET  /api/purchases
GET  /api/balances?scope=open
GET  /api/settlements?scope=open
POST /api/current-report
POST /api/analytics-report
GET  /api/reports/{report_id}/download
GET  /api/settlement-periods
POST /api/settlement-periods/close
POST /api/settlement-periods/{id}/reopen
```

`POST /telegram/webhook` можно добавить как stub только после security model, но не реализовывать full bot flow до CLOUD.7.

## Требования

1. Backend использует services.
2. Backend не импортирует Tkinter/Typer/Rich.
3. Tenant resolution пока может быть simplified для MVP, но должен быть явный `tenant_id` boundary.
4. Errors structured, без traceback в response.
5. Secrets читаются из env/settings, не из Git.
6. PDF/XLSX reports возвращаются через `ReportService`.

## Проверки

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_server_health.py -v
.\.venv\Scripts\python.exe -m pytest tests\test_server_purchases_api.py -v
.\.venv\Scripts\python.exe -m pytest tests\test_server_reports_api.py -v
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
.\.venv\Scripts\python.exe -m ruff check src tests
git diff --check
```

## Commit

```powershell
git add src tests docs README.md pyproject.toml
# плюс config templates, если созданы
git commit -m "feat: add FastAPI backend MVP"
git push origin cloud/telegram-prep
```

---

# CLOUD.7 — Telegram bot MVP

## Цель

Добавить Telegram bot adapter, который позволяет участникам заносить покупки и получать PDF/XLSX отчеты.

## Предварительные условия

- CLOUD.0–CLOUD.6 закрыты.
- Security model утвержден.
- Secrets policy работает.
- Backend API/service layer готов.

## Создать структуру

```text
src/expense_splitter/telegram_bot/
  __init__.py
  handlers.py
  keyboards.py
  states.py
  messages.py
  adapter.py

tests/test_telegram_bot_handlers.py
tests/test_telegram_bot_flows.py
```

## MVP команды

```text
/start
/help
/add_purchase
/current_pdf
/current_xlsx
/analytics
/periods
/period_report
/cancel
```

## Add purchase flow

1. Наименование покупки, default `н/д`.
2. Сумма.
3. Плательщик, default linked participant.
4. Участники через inline multi-select.
5. Категория.
6. Дата, default today.
7. Комментарий.
8. Preview.
9. Confirm.
10. Save через service/API.
11. Audit log.
12. Ответ пользователю.

## Report flows

Telegram должен уметь отправить:

```text
current-report PDF/XLSX по open scope
analytics PDF/XLSX за month/quarter/year
settlement-period report PDF/XLSX по выбранному period
```

## Security

1. Проверять Telegram webhook secret.
2. Resolve `telegram_user_id -> user_id -> tenant_id -> participant_id`.
3. Не использовать username как identity без подтверждения.
4. Не логировать token.
5. Не хранить файлы отчетов в bot session.
6. Admin-only действия закрытия/переоткрытия периода — по умолчанию выключить или оставить на отдельный этап.

## Проверки

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_telegram_bot_handlers.py -v
.\.venv\Scripts\python.exe -m pytest tests\test_telegram_bot_flows.py -v
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
.\.venv\Scripts\python.exe -m ruff check src tests
git diff --check
```

## Commit

```powershell
git add src tests docs README.md pyproject.toml
git commit -m "feat: add Telegram bot MVP"
git push origin cloud/telegram-prep
```

---

# CLOUD.8 — Yandex Cloud deployment MVP

## Цель

Подготовить развертывание backend/bot в Yandex Cloud.

## Предпочтительный MVP путь

```text
Container/VM backend
Managed PostgreSQL
Object Storage
Lockbox/env secrets
Monitoring/logging
```

Serverless оставить как future optimization.

## Документы/файлы

```text
docs/cloud/YANDEX_CLOUD_DEPLOYMENT.md
docs/cloud/OPERATIONS_RUNBOOK.md
Dockerfile
compose.yaml или docker-compose.yml для local dev
scripts/cloud/
```

## Обязательные правила

- Не коммитить реальные credentials.
- Service account keys не хранить в repo.
- `.env` ignored.
- Проверить PDF font availability в container healthcheck.
- Object Storage retention policy описать.
- DB backup strategy описать.

## Smoke

1. Backend healthcheck.
2. DB connection.
3. Report PDF font healthcheck.
4. Generate current PDF/XLSX in temp workspace.
5. Upload test artifact to Object Storage, если cloud resources уже созданы и явно разрешены.
6. Telegram webhook dry-run, если token предоставлен через secret store.

---

# CLOUD.9 — production hardening and release gate

## Цель

Довести cloud/bot направление до production-ready candidate.

## Обязательные проверки

```text
unit tests
integration tests
API tests
Telegram flow tests
DB migration dry-run
YAML -> DB migration dry-run
security grep
secret scanning
encoding/mojibake
ruff
compileall
report generation PDF/XLSX
backup/restore drill
```

## Security hardening

- Webhook secret validation.
- Masked logs.
- Rate limits.
- Audit log.
- Admin roles.
- Tenant isolation tests.
- DB least privilege user.
- Object Storage permissions.

## Release decision

Статус может быть:

```text
cloud MVP ready
not cloud ready — blockers
```

---

## 4. Первая команда для Codex

Скопируй Codex эту команду как следующий рабочий этап.

```text
Выполни CLOUD.0 — архитектурное проектирование Telegram + Yandex Cloud automation для Expense Splitter.

Рабочая директория:
C:\Users\Rockaudit\LLM_CHAT\expense_splitter

Рабочая ветка:
cloud/telegram-prep

Перед началом:
1. Выполни git status --short.
2. Выполни git branch --show-current.
3. Убедись, что ветка cloud/telegram-prep.
4. Убедись, что generated artifacts и secrets не staged.
5. Не создавать tag/release.

Используй входные документы:
- docs/cloud/SERVER_READINESS_AUDIT.md
- docs/cloud/SERVICE_REPOSITORY_BOUNDARY.md
- docs/cloud/DATABASE_READINESS.md
- docs/cloud/REPORT_DELIVERY_CONTRACT.md
- docs/cloud/SECURITY_PREP_CHECKLIST.md
- docs/cloud/CLOUD_0_START_PLAN.md
- README.md
- docs/reports/prod_ready_progress_report.md

Создай документы:
- docs/cloud/TELEGRAM_YANDEX_CLOUD_ARCHITECTURE.md
- docs/cloud/API_CONTRACT.md
- docs/cloud/DATABASE_SCHEMA.md
- docs/cloud/TELEGRAM_BOT_SPEC.md
- docs/cloud/MIGRATION_PLAN.md
- docs/cloud/SECURITY_MODEL.md
- docs/cloud/IMPLEMENTATION_ROADMAP.md

Обязательные решения:
1. MVP architecture = FastAPI backend service/container + PostgreSQL + Object Storage.
2. Serverless описать как future optimization, не как стартовый путь.
3. Telegram bot не должен писать в YAML напрямую.
4. Telegram bot не должен вызывать CLI-команды.
5. Telegram bot должен получать PDF/XLSX через ReportService/Backend contract.
6. PostgreSQL model должна использовать stable IDs и tenant isolation.
7. YAML offline desktop mode должен быть сохранен.
8. Real secrets/tokens/keys не добавлять.
9. Cloud resources не создавать.
10. Production bot code не писать.

В TELEGRAM_YANDEX_CLOUD_ARCHITECTURE.md опиши:
- target architecture;
- Yandex Cloud components;
- local/dev/prod environments;
- report generation flow;
- object storage flow;
- deployment topology;
- observability basics;
- почему container/backend service выбран для MVP.

В API_CONTRACT.md опиши:
- FastAPI endpoints;
- Telegram webhook endpoint;
- request/response schemas;
- error codes;
- idempotency;
- tenant/user resolution;
- auth/security expectations.

В DATABASE_SCHEMA.md опиши:
- tenants;
- users;
- telegram_accounts;
- participants;
- participant_aliases;
- categories;
- purchases;
- purchase_participants;
- settlement_periods;
- settlement_period_purchases;
- reports;
- audit_log;
- bot_sessions;
- primary keys, foreign keys, indexes, constraints.

В TELEGRAM_BOT_SPEC.md опиши:
- /start;
- /help;
- /add_purchase;
- /current_pdf;
- /current_xlsx;
- /analytics;
- /periods;
- /period_report;
- /cancel;
- conversational flow добавления покупки;
- report request UX;
- русские пользовательские сообщения.

В MIGRATION_PLAN.md опиши:
- YAML -> PostgreSQL dry-run;
- stable ID generation;
- alias mapping;
- конфликтные имена;
- migration warnings;
- rollback/backup strategy;
- validation totals/counts.

В SECURITY_MODEL.md опиши:
- Telegram bot token storage;
- webhook secret validation;
- Yandex Lockbox/env secrets;
- DATABASE_URL masking;
- service account permissions;
- audit log;
- incident response при утечке secret.

В IMPLEMENTATION_ROADMAP.md опиши:
- CLOUD.1 repository protocols only;
- CLOUD.2 YAML repository adapter;
- CLOUD.3 service layer extraction;
- CLOUD.4 ReportService/output adapters;
- CLOUD.5 PostgreSQL schema/migrations;
- CLOUD.6 FastAPI backend MVP;
- CLOUD.7 Telegram bot MVP;
- CLOUD.8 Yandex Cloud deployment MVP;
- CLOUD.9 production hardening.

Запрещено:
- писать Telegram bot code;
- деплоить cloud;
- добавлять реальные secrets;
- менять бизнес-логику;
- ломать CLI/GUI/YAML offline mode;
- менять settlement close/reopen semantics;
- коммитить generated artifacts;
- выполнять git reset --hard, git clean -fd, force push.

Проверки:
chcp 65001
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)

.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
git diff --check
git status --short --ignored

Если менялись только docs, полный pytest не обязателен.
Если менялись .gitignore, .env.example, Python code или workflow, выполни полный quality gate:
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe -m ruff check src tests

Commit:
git add docs/cloud README.md
git commit -m "docs: design telegram yandex cloud architecture"
git push origin cloud/telegram-prep

Финальный ответ на русском:
1. Этап.
2. Статус.
3. Созданные документы.
4. Рекомендованная архитектура.
5. Открытые решения.
6. Проверки.
7. Commit hash.
8. Push status.
9. GitHub Actions status.
10. Generated artifacts not staged.
11. Следующий этап: CLOUD.1 — repository protocols only.
```

---

## 5. Итоговое решение

Дальнейшая работа должна идти через аккуратный cloud-roadmap, а не через “давайте быстро прикрутим бота”.

Правильный ближайший шаг: **CLOUD.0**.
Правильный первый кодовый шаг после CLOUD.0: **CLOUD.1 — repository protocols only**.
Telegram bot появляется только на **CLOUD.7**.

Так проект сохранит текущий стабильный desktop/CLI режим и получит нормальную основу для server/cloud автоматизации, а не еще один интерфейс поверх локального YAML. Это, конечно, менее драматично, зато потом меньше шансов проводить археологические раскопки в собственном коде.
