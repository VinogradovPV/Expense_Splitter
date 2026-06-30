# Expense Splitter — пошаговая инструкция подготовки проекта перед созданием Telegram-бота

Дата подготовки: 2026-06-30  
Целевая ветка: `prod-ready/p0-p1`  
Рекомендуемое имя этапа: `TG-PREP.0 — подготовка проекта к Telegram/Yandex Cloud контуру`  
Статус: инструкция для Codex, реализация Telegram-бота на этом этапе запрещена.

---

## 1. Зачем нужен этот этап

Проект уже доведен до состояния локального production-ready candidate: desktop GUI, CLI, YAML-хранилище, справочники, периоды взаиморасчетов, PDF/XLSX/HTML/CSV/PNG/Markdown-отчеты и standalone-сборка. Следующая крупная цель — автоматизация занесения покупок через Telegram-бота с серверной обработкой в Yandex Cloud.

Перед написанием Telegram-бота нужно подготовить проект так, чтобы бот не стал четвертым независимым интерфейсом со своей логикой, своим хранилищем и своим маленьким болотом. GUI, CLI, будущий API и Telegram должны использовать единые доменные сервисы и единый контракт отчетов.

На этом этапе Codex должен:

1. Зафиксировать и проверить текущий release baseline.
2. Устранить или явно задокументировать P3.REL-хвосты, влияющие на дальнейшую разработку.
3. Подготовить проектную документацию для перехода от локального YAML-приложения к server/cloud архитектуре.
4. Проанализировать текущие точки сцепления с YAML, filesystem, GUI и CLI.
5. Подготовить план service/repository abstraction перед CLOUD.0 и перед кодом Telegram-бота.
6. Не писать Telegram-бота, не создавать cloud resources, не добавлять реальные токены.

---

## 2. Важный вывод из P3.REL

По P3.REL-документам проект готов как локальное приложение, но не как многопользовательская облачная система.

Ключевые факты, которые нужно учитывать:

- Версия проекта зафиксирована как `0.1.1`; рекомендуемый финальный tag — `v0.1.1`.
- Ветка перед release dry-run: `prod-ready/p0-p1`.
- Локальные `data/*.yaml` не tracked и ignored.
- Generated artifacts не должны попадать в Git.
- `build-release.yml` умеет `workflow_dispatch` и tag-triggered запуск по `v*.*.*`.
- RC tag `v0.1.1-rc.1` уже был создан, workflow успешно собрал Linux/Windows artifacts и создал GitHub Release.
- В RC-проверке был найден дефект: RC release был опубликован как обычный release; workflow исправлен так, чтобы будущие `*-rc.*` публиковались как prerelease.
- Скачивание artifacts на локальную машину было нестабильным; smoke на частично скачанных `.exe` не засчитывается.
- Known limitation: данные пока хранятся локально в YAML, многопользовательская синхронизация не реализована.

Это значит: перед Telegram-ботом нужно не “быстренько добавить aiogram”, а отделить доменную логику от локального хранения и подготовить серверный контракт. Да, скучно. Зато потом бот не будет сохранять покупки в YAML где-нибудь на сервере как записки в холодильник.

---

## 3. Жесткие правила этапа

Codex обязан соблюдать эти правила:

1. Не реализовывать Telegram-бота на этом этапе.
2. Не добавлять реальные Telegram/Yandex Cloud tokens.
3. Не создавать реальные Yandex Cloud resources.
4. Не менять пользовательские `data/*.yaml`.
5. Не выполнять destructive-команды:
   - `git reset --hard`;
   - `git clean -fd`;
   - force push;
   - массовое удаление файлов.
6. Не коммитить generated artifacts:
   - `reports/`;
   - `.tmp/`;
   - `build/`;
   - `dist/`;
   - `.pytest_cache/`;
   - `.ruff_cache/`;
   - `__pycache__/`;
   - `*.egg-info/`;
   - `*.bak`.
7. Git/GitHub-команды выполнять outside sandbox.
8. Проверки `pip`, `pytest`, `compileall`, `ruff`, `check_text_encoding.py`, PyInstaller и GUI запускать outside sandbox.
9. Все документы сохранять в UTF-8.
10. Не допускать mojibake.
11. Не создавать финальный tag `v0.1.1` и не публиковать финальный GitHub Release без явного подтверждения пользователя.
12. Если создается новый RC tag, сначала согласовать это с пользователем.

---

## 4. Этап TG-PREP.0 — сверка baseline перед cloud-веткой

### Цель

Подтвердить, что локальное состояние совпадает с `origin/prod-ready/p0-p1`, release artifacts не попали в Git, а P3.REL-документы отражают фактическое состояние.

### Команды

```powershell
cd C:\Users\Rockaudit\LLM_CHAT\expense_splitter

chcp 65001
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)

git fetch origin --prune
git checkout prod-ready/p0-p1
git pull --ff-only origin prod-ready/p0-p1
git status --short
git rev-parse HEAD
git rev-parse origin/prod-ready/p0-p1
git log --oneline -10
```

### Что проверить

1. Ветка: `prod-ready/p0-p1`.
2. `HEAD` совпадает с `origin/prod-ready/p0-p1`.
3. Нет staged/untracked файлов, кроме ожидаемых локальных generated artifacts.
4. `data/*.yaml` не tracked.
5. `reports/`, `.tmp/`, `build/`, `dist/` не staged.
6. Финальный tag `v0.1.1` не создан без подтверждения.
7. RC tag и release workflow status зафиксированы в документации.

### Если есть несоответствия

- Не чинить вслепую.
- Зафиксировать список несоответствий в `docs/reports/prod_ready_progress_report.md`.
- Запросить решение пользователя, если требуется tag/release/удаление/пересоздание RC.

---

## 5. Этап TG-PREP.1 — P3.REL hygiene перед новой архитектурой

### Цель

Привести release-документы к состоянию, которое не будет путать последующую разработку Telegram/Yandex Cloud контура.

### Проверить документы

- `docs/releases/RELEASE_CHECKLIST_v0.1.1.md`
- `docs/releases/RELEASE_NOTES_v0.1.1.md`
- `docs/reports/prod_ready_progress_report.md`
- `.github/workflows/build-release.yml`
- `pyproject.toml`

### Что сделать

1. Проверить, что release notes не утверждают “tag не создан” без уточнения, что позже был создан `v0.1.1-rc.1`.
2. Проверить, что RC release issue `prerelease=false` отражен как исправленный для будущих RC tags.
3. Проверить, что clean smoke на частично скачанных `.exe` не засчитан.
4. Проверить, что финальный `v0.1.1` release явно требует отдельного подтверждения.
5. Проверить, что `dist/` и release artifacts не коммитятся.
6. Устранить warning по `typer[all]`, если он еще есть в `pyproject.toml`:
   - заменить `typer[all]>=...` на `typer>=...`, если `rich` уже указан отдельной dependency;
   - выполнить полный quality gate;
   - зафиксировать как maintenance commit.

### Проверки

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
git diff --check
```

### Commit

Если менялись только release docs:

```powershell
git add docs/releases docs/reports/prod_ready_progress_report.md README.md
git commit -m "docs: align release notes before cloud preparation"
git push origin prod-ready/p0-p1
```

Если менялся `pyproject.toml`:

```powershell
git add pyproject.toml docs/reports/prod_ready_progress_report.md
git commit -m "chore: simplify typer dependency declaration"
git push origin prod-ready/p0-p1
```

---

## 6. Этап TG-PREP.2 — создать cloud-prep ветку

### Цель

Не смешивать стабильную локальную release-линию с подготовкой серверной архитектуры.

### Команды

```powershell
git fetch origin --prune
git checkout prod-ready/p0-p1
git pull --ff-only origin prod-ready/p0-p1
git checkout -b cloud/telegram-prep
```

Если ветка уже существует:

```powershell
git checkout cloud/telegram-prep
git pull --ff-only origin cloud/telegram-prep
```

### Правило

Ветка `cloud/telegram-prep` предназначена для документации, аудита, service-layer подготовки и безопасных внутренних refactor-ов. Не добавлять реальный Telegram bot до завершения архитектурного этапа.

---

## 7. Этап TG-PREP.3 — аудит серверной готовности текущего кода

### Цель

Понять, какие части текущего проекта можно переиспользовать на сервере, а какие привязаны к локальному YAML/filesystem/GUI.

### Создать документ

```text
docs/cloud/SERVER_READINESS_AUDIT.md
```

### Проанализировать файлы

- `src/expense_splitter/models.py`
- `src/expense_splitter/calculator.py`
- `src/expense_splitter/settlement.py`
- `src/expense_splitter/settlement_periods.py`
- `src/expense_splitter/analytics.py`
- `src/expense_splitter/current_report.py`
- `src/expense_splitter/settlement_period_report.py`
- `src/expense_splitter/report_pdf.py`
- `src/expense_splitter/analytics_xlsx.py`
- `src/expense_splitter/storage.py`
- `src/expense_splitter/cli.py`
- `src/expense_splitter/gui/`

### Команды поиска

```powershell
rg "Path\(|open\(|read_text|write_text|mkdir|reports|data_dir|load_purchases|save_purchases" src tests
rg "typer|messagebox|tkinter|click|Console|Table" src/expense_splitter
rg "calculate_balances|calculate_settlements|generate_current_report|generate_analytics|settlement-period" src tests
```

### В документе зафиксировать

1. Pure domain modules:
   - модели;
   - расчет балансов;
   - settlement minimizer;
   - аналитические агрегации, если они не завязаны на filesystem.
2. Filesystem-bound modules:
   - YAML storage;
   - report output paths;
   - backup logic.
3. Interface-bound modules:
   - CLI;
   - GUI;
   - PowerShell wrappers.
4. Report-generation modules:
   - что можно вызывать из backend;
   - что нужно адаптировать под temp dir/Object Storage.
5. Риски:
   - имена участников как display-name вместо stable ID;
   - YAML как single-user хранилище;
   - отчеты пишутся в локальную папку;
   - GUI/CLI могут содержать бизнес-логику, которую нужно вынести.

---

## 8. Этап TG-PREP.4 — подготовить service/repository boundary

### Цель

Сформировать план выделения слоя сервисов и репозиториев без переписывания всего проекта. Переписывать всё сразу — любимое развлечение разработчиков, после которого проект обычно уходит жить в архив.

### Создать документ

```text
docs/cloud/SERVICE_REPOSITORY_BOUNDARY.md
```

### Описать будущую структуру

```text
src/expense_splitter/services/
  purchases_service.py
  participants_service.py
  categories_service.py
  settlement_service.py
  report_service.py

src/expense_splitter/repositories/
  protocols.py
  yaml_repository.py
  postgres_repository.py   # future
```

### Описать интерфейсы

Минимальные repository protocols:

```python
class PurchaseRepository(Protocol):
    def list_purchases(self, tenant_id: str) -> list[Purchase]: ...
    def add_purchase(self, tenant_id: str, purchase: Purchase) -> Purchase: ...
    def update_purchase(self, tenant_id: str, purchase_id: str, patch: PurchasePatch) -> Purchase: ...

class ParticipantRepository(Protocol):
    def list_participants(self, tenant_id: str) -> list[Participant]: ...

class CategoryRepository(Protocol):
    def list_categories(self, tenant_id: str) -> list[Category]: ...

class SettlementPeriodRepository(Protocol):
    def list_periods(self, tenant_id: str) -> list[SettlementPeriod]: ...
    def save_period(self, tenant_id: str, period: SettlementPeriod) -> SettlementPeriod: ...
```

### Обязательные решения

1. Desktop/CLI пока продолжают работать через YAML repository.
2. Telegram/FastAPI позже будут работать через PostgreSQL repository.
3. Расчеты не должны знать, откуда пришли данные.
4. Отчеты должны принимать dataset/output adapter, а не напрямую писать в глобальный `reports/` без контроля.
5. Backward compatibility текущего GUI/CLI не ломать.

---

## 9. Этап TG-PREP.5 — data model для будущего Telegram/Yandex Cloud

### Цель

Подготовить модель данных, пригодную для многопользовательского сервера.

### Создать документ

```text
docs/cloud/DATABASE_READINESS.md
```

### Описать сущности

Минимум:

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

### Обязательные акценты

1. Не использовать имя участника как primary key.
2. Ввести stable IDs:
   - `tenant_id`;
   - `participant_id`;
   - `purchase_id`;
   - `category_id`;
   - `settlement_period_id`.
3. Связать Telegram user через `telegram_user_id -> user_id -> participant_id`.
4. Поддержать несколько групп/tenant-ов в будущем, даже если MVP будет один tenant.
5. Описать миграцию display names из YAML в stable IDs.
6. Описать audit log для операций:
   - добавление покупки;
   - редактирование покупки;
   - закрытие периода;
   - переоткрытие периода;
   - изменение справочников;
   - генерация отчета.

---

## 10. Этап TG-PREP.6 — contract отчетов для Telegram

### Цель

Подготовить единый контракт генерации отчетов, чтобы Telegram bot мог запрашивать PDF/XLSX без знания внутренних файловых деталей.

### Создать документ

```text
docs/cloud/REPORT_DELIVERY_CONTRACT.md
```

### Описать сценарии

1. Текущий период взаиморасчетов:
   - `current-report --scope open --format pdf`;
   - `current-report --scope open --format xlsx`.
2. Отчетный период:
   - analytics month PDF/XLSX;
   - analytics quarter PDF/XLSX;
   - analytics year PDF/XLSX.
3. Конкретный settlement period:
   - PDF;
   - XLSX.

### Описать будущий API сервиса отчетов

```python
class ReportService:
    def create_current_report(tenant_id: str, scope: str, formats: set[str]) -> ReportResult: ...
    def create_analytics_report(tenant_id: str, period: PeriodSpec, formats: set[str]) -> ReportResult: ...
    def create_settlement_period_report(tenant_id: str, period_id: str, formats: set[str]) -> ReportResult: ...
```

### Описать ReportResult

```text
report_id
report_type
formats
files
created_at
expires_at
storage_backend
telegram_caption
```

### Требования

1. Отчеты не меняют данные.
2. Snapshot settlements не пересчитываются для historical settlement-period report.
3. Генерация может идти во временную директорию.
4. В cloud-режиме результат должен сохраняться в Object Storage или аналогичный backend.
5. Telegram отправляет файл через `sendDocument`, а не хранит его постоянно в боте.
6. PDF должен использовать доступный кириллический шрифт в серверной среде.

---

## 11. Этап TG-PREP.7 — security baseline перед ботом

### Цель

Не допустить появления токенов, секретов и ключей в репозитории. Звучит очевидно, но человечество уже миллионы раз коммитило `.env`, так что повторим вслух.

### Создать документ

```text
docs/cloud/SECURITY_PREP_CHECKLIST.md
```

### Добавить или проверить

1. `.gitignore` содержит:

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

2. Создать безопасный шаблон:

```text
.env.example
```

Пример содержимого без секретов:

```env
TELEGRAM_BOT_TOKEN=replace_me
TELEGRAM_WEBHOOK_SECRET=replace_me
DATABASE_URL=postgresql+psycopg://user:password@host:5432/dbname
YANDEX_CLOUD_FOLDER_ID=replace_me
YANDEX_OBJECT_STORAGE_BUCKET=replace_me
```

3. Проверить поиск секретов:

```powershell
git grep -n -E "(BOT_TOKEN|TELEGRAM|YANDEX|YC_|SECRET|PASSWORD|TOKEN|DATABASE_URL|SERVICE_ACCOUNT|PRIVATE_KEY)" -- . ':!docs/cloud/SECURITY_PREP_CHECKLIST.md' ':!.env.example'
```

### Правила

- `.env.example` можно коммитить.
- `.env` нельзя коммитить.
- Реальные Telegram/Yandex tokens запрещены в истории Git.
- Yandex service account keys не хранить в репозитории.
- Для future deployment использовать Yandex Lockbox/env secrets.

---

## 12. Этап TG-PREP.8 — подготовить CLOUD.0 как следующий рабочий пакет

### Цель

Сформировать пакет документов и команду, после которой можно будет передавать Codex полноценный этап CLOUD.0.

### Создать документ

```text
docs/cloud/CLOUD_0_START_PLAN.md
```

### Включить в документ

1. Рекомендуемую архитектуру MVP:

```text
Telegram Bot → FastAPI backend → service layer → repository → PostgreSQL → report generator → Object Storage → sendDocument
```

2. Альтернативы:
   - serverless;
   - VM/container;
   - hybrid.
3. Почему для MVP предпочтительнее backend service/container:
   - ReportLab;
   - matplotlib;
   - openpyxl;
   - кириллические шрифты;
   - проще smoke/debug/deploy.
4. Список документов, которые CLOUD.0 должен создать:
   - `TELEGRAM_YANDEX_CLOUD_ARCHITECTURE.md`;
   - `API_CONTRACT.md`;
   - `DATABASE_SCHEMA.md`;
   - `TELEGRAM_BOT_SPEC.md`;
   - `MIGRATION_PLAN.md`;
   - `SECURITY_MODEL.md`;
   - `IMPLEMENTATION_ROADMAP.md`.
5. Список запретов для CLOUD.0:
   - не писать bot code;
   - не деплоить cloud;
   - не добавлять secrets;
   - не ломать YAML offline mode.

---

## 13. Проверки этапа TG-PREP

Если менялись только документы:

```powershell
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
git diff --check
```

Если менялись `.gitignore`, `.env.example`, `pyproject.toml` или Python-код:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
git diff --check
```

Дополнительно:

```powershell
git status --short --ignored
```

Проверить, что generated artifacts не staged.

---

## 14. Commit policy

### Если изменения только в docs/cloud и README

```powershell
git add docs/cloud README.md docs/reports/prod_ready_progress_report.md
git commit -m "docs: prepare Telegram and cloud readiness plan"
git push -u origin cloud/telegram-prep
```

### Если добавлен `.env.example` и обновлен `.gitignore`

```powershell
git add .gitignore .env.example docs/cloud docs/reports/prod_ready_progress_report.md
git commit -m "chore: add cloud secrets baseline"
git push -u origin cloud/telegram-prep
```

### Если исправлен `pyproject.toml`

```powershell
git add pyproject.toml docs/reports/prod_ready_progress_report.md
git commit -m "chore: simplify dependency declaration before cloud work"
git push -u origin cloud/telegram-prep
```

---

## 15. Финальный ответ Codex по этапу

Codex должен ответить на русском:

```text
1. Этап.
2. Статус.
3. Что проанализировано.
4. Какие P3.REL-хвосты выявлены.
5. Какие документы созданы.
6. Какие изменения внесены в README/.gitignore/.env.example/pyproject.toml, если были.
7. Проверки и результаты.
8. Commit hash.
9. Push status.
10. GitHub Actions status, если был push.
11. Generated artifacts not staged.
12. Secrets not committed.
13. Что осталось перед CLOUD.0.
14. Следующий рекомендуемый этап: CLOUD.0 — архитектурное проектирование Telegram + Yandex Cloud automation.
```

---

## 16. Критерии готовности перед созданием Telegram-бота

Переходить к проектированию/разработке Telegram-бота можно только если выполнено следующее:

- P3.REL-документы синхронизированы и не противоречат фактическому состоянию RC/final release.
- Финальный release `v0.1.1` не создан без подтверждения пользователя.
- Release artifacts и generated files не попали в Git.
- Создана ветка `cloud/telegram-prep` или другое согласованное имя ветки.
- Созданы документы:
  - `SERVER_READINESS_AUDIT.md`;
  - `SERVICE_REPOSITORY_BOUNDARY.md`;
  - `DATABASE_READINESS.md`;
  - `REPORT_DELIVERY_CONTRACT.md`;
  - `SECURITY_PREP_CHECKLIST.md`;
  - `CLOUD_0_START_PLAN.md`.
- Проверено, что secrets не попали в репозиторий.
- Сформулирован план сохранения offline YAML mode.
- Сформулирован план stable IDs и миграции из YAML в DB.
- Сформулирован контракт генерации PDF/XLSX для Telegram.
- Quality gate пройден в объеме, соответствующем изменениям.

Только после этого давать Codex этап CLOUD.0 или сразу CLOUD.1. До этого писать Telegram bot преждевременно. Бот без подготовленного service/repository слоя станет просто еще одним интерфейсом к локальному приложению, а не облачной системой. И да, потом это придется переделывать, потому что иначе не бывает.
