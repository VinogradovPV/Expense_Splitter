# Expense Splitter: пошаговая инструкция доработки до production-ready v1
## На основе аудита Codex, полностью на русском

Дата актуализации: 2026-06-18.

---

## 0. Назначение документа

Этот документ задает порядок работ по стабилизации проекта `Expense Splitter` после аудита Codex.

Главная цель — довести проект от рабочего прототипа до production-ready candidate без переписывания с нуля и без потери пользовательских данных.

Ключевые выводы аудита:

```text
- проект не production-ready;
- editable install сломан;
- initialize_data_files перезаписывает participants/groups;
- CI/release workflow не соответствует структуре GitHub;
- PyInstaller spec paths некорректны;
- storage не защищает пользовательские данные;
- launcher неполный;
- документация содержит placeholders и не полностью соответствует проекту;
- локальная копия и GitHub не синхронизированы.
```

---

## 1. Общие правила для всех этапов

### 1.1. Рабочая директория

```powershell
cd C:\Users\Rockaudit\LLM_CHAT\expense_splitter
```

### 1.2. Git/GitHub только outside sandbox

Все `git` и `gh` команды выполнять только outside sandbox.

Перед commit:

```powershell
git status --short
git diff --name-only
git diff --cached --name-only | Select-String ".venv|__pycache__|.pytest_cache|.ruff_cache|dist|build|*.egg-info|reports/tmp|logs|tmp|temp|*.part|*.crdownload|backup|backups"
```

После push:

```powershell
gh run list --limit 5
```

Если run упал:

```powershell
gh run view --log
```

### 1.3. Не коммитить

```text
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
dist/
build/
*.egg-info/
logs/
tmp/
temp/
*.tmp
*.part
*.crdownload
user backups
local generated reports
```

### 1.4. UTF-8 и русский язык

```text
- Markdown сохранять в UTF-8 без BOM.
- Документацию писать на русском.
- PowerShell output должен корректно отображать кириллицу.
- Тесты должны покрывать русские имена участников.
```

### 1.5. Отчет по каждому этапу

После каждого этапа обновлять:

```text
REPORT.md
```

Формат записи:

```markdown
### YYYY-MM-DD HH:MM — <этап>

- Status:
- Files changed:
- Decisions:
- Checks executed:
- Checks skipped and why:
- Errors/warnings:
- Commit:
- Push:
- GitHub Actions:
- Generated artifacts not staged:
- Data safety:
- Next step:
```

### 1.6. Экономия токенов

В ответах и отчетах:

```text
- не вставлять полные файлы;
- не печатать длинные логи;
- указывать только ключевые ошибки;
- подробности писать в REPORT.md;
- группировать изменения по этапам.
```

---

# P0.0 — Синхронизация локального проекта и GitHub

## Цель

Привести локальный проект и GitHub к понятному состоянию до исправлений.

Аудит показал: GitHub существует, PR ref существует, но локально remote не настроен, коммитов нет, все файлы untracked.

## Команда для агента

```text
Выполни P0.0 — синхронизация локального проекта и GitHub.

Цель:
- понять фактическую структуру локального проекта;
- настроить remote, если он отсутствует;
- не потерять текущие локальные файлы;
- создать защитный локальный commit перед изменениями;
- определить, работаем ли от локальной копии или от remote branch feature/installer-readme-launcher.

Не удаляй файлы.
Не делай force push.
Не переписывай историю.
Git/GitHub команды выполняй only outside sandbox.
Обнови REPORT.md.
```

## Проверки и команды

```powershell
cd C:\Users\Rockaudit\LLM_CHAT\expense_splitter
git status --short
git branch --show-current
git remote -v
git log --oneline -10
```

Если remote отсутствует:

```powershell
git remote add origin https://github.com/VinogradovPV/Expense_Splitter.git
git remote -v
```

Если все файлы untracked, создать защитный commit:

```powershell
git add .
git status --short
git commit -m "chore: preserve local Expense Splitter project state"
```

Проверить remote branches:

```powershell
git fetch origin
git branch -a
```

## Критерии завершения

```text
- remote origin настроен или documented почему нет;
- локальное состояние сохранено commit;
- понятно, какая ветка является базой;
- REPORT.md обновлен;
- нет force push.
```

## Commit

Если были изменения:

```powershell
git add REPORT.md
git commit -m "docs: record repository synchronization status"
```

---

# P0.1 — Исправление Python packaging и editable install

## Цель

Исправить P0-дефект: `pip install -e .[dev]` не проходит из-за нерабочего build backend.

## Файлы

```text
pyproject.toml
REPORT.md
```

При необходимости:

```text
src/expense_splitter/__init__.py
src/expense_splitter/__main__.py
```

## Команда для агента

```text
Выполни P0.1 — исправление Python packaging.

Исправь pyproject.toml так, чтобы:
- build backend был рабочим;
- setuptools package discovery корректно находил src/expense_splitter;
- dev dependencies включали pytest, ruff, pyinstaller при необходимости;
- entry points expense-splitter и expense-splitter-launcher работали.

Не меняй бизнес-логику.
Не трогай storage/calculator на этом этапе.
Обнови REPORT.md.
```

## Требования

Ожидаемый backend:

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"
```

Package discovery:

```toml
[tool.setuptools.packages.find]
where = ["src"]
```

Entry points:

```toml
[project.scripts]
expense-splitter = "expense_splitter.cli:app"
expense-splitter-launcher = "expense_splitter.launcher:main"
```

Если фактические callable отличаются, привести к рабочему варианту и описать решение в REPORT.md.

## Проверки

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
python -c "import expense_splitter; print(expense_splitter.__file__)"
expense-splitter --help
python -m expense_splitter --help
```

Если launcher пока не поддерживает `--help`:

```powershell
expense-splitter-launcher
```

Но лучше добавить безопасный `--help` на одном из следующих этапов.

## Commit

```powershell
git add pyproject.toml REPORT.md
git commit -m "fix: repair Python packaging and editable install"
git push
```

## Критерии завершения

```text
- python -m pip install -e ".[dev]" проходит;
- package import работает;
- expense-splitter --help работает;
- REPORT.md обновлен;
- CI не сломан или failure documented.
```

---

# P0.2 — Исправление storage/init и тестов данных

## Цель

Исправить P0-дефект: `initialize_data_files()` перезаписывает `participants.yaml` при сохранении groups.

## Файлы

```text
src/expense_splitter/storage.py
src/expense_splitter/defaults.py
tests/test_storage.py
tests/test_cli.py
REPORT.md
```

## Команда для агента

```text
Выполни P0.2 — исправление storage/init.

Цель:
- init должен создавать корректные participants, groups и purchases;
- participants и groups не должны перезаписывать друг друга;
- существующие пользовательские данные не должны молча перезаписываться;
- добавить регрессионные тесты на этот дефект.

Не меняй CLI UX шире необходимого.
Не меняй расчетную логику.
Обнови REPORT.md.
```

## Рекомендуемое решение

Выбрать один вариант и явно зафиксировать в README/REPORT:

### Вариант A — единый config file

```text
data/participants.yaml содержит:
participants:
  - name: Павел
groups:
  - name: Кофе
    members: [...]
```

### Вариант B — раздельные файлы

```text
data/participants.yaml
data/groups.yaml
data/purchases.yaml
```

Рекомендуется вариант B, потому что он проще для пользователя и снижает риск перезаписи.

## Обязательные проверки

```powershell
python -m pytest tests/test_storage.py -v
python -m pytest tests/test_cli.py -v
python -m pytest tests -v
```

Ручная проверка в temp data dir:

```powershell
Remove-Item -Recurse -Force .\tmp_test_data -ErrorAction SilentlyContinue
expense-splitter init --data-dir .\tmp_test_data --with-examples
Get-ChildItem .\tmp_test_data
Get-Content .\tmp_test_data\participants.yaml -Encoding UTF8
Get-Content .\tmp_test_data\groups.yaml -Encoding UTF8
Get-Content .\tmp_test_data\purchases.yaml -Encoding UTF8
```

Если CLI не поддерживает `--data-dir`, добавить или зафиксировать как P1, но storage tests должны использовать temp dir.

## Тесты должны покрывать

```text
- init создает participants;
- init создает groups;
- init создает purchases;
- повторный init не перезаписывает существующие данные без confirm;
- кириллица сохраняется корректно;
- load/save roundtrip работает.
```

## Commit

```powershell
git add src/expense_splitter/storage.py src/expense_splitter/defaults.py tests/test_storage.py tests/test_cli.py REPORT.md
git commit -m "fix: prevent init data overwrite and add storage regression tests"
git push
```

## Критерии завершения

```text
- дефект перезаписи закрыт;
- есть регрессионный тест;
- init безопасен для пользовательских данных;
- тесты проходят.
```

---

# P0.3 — Data safety: atomic write, backup, corrupted YAML

## Цель

Добавить минимальную защиту пользовательских данных.

## Файлы

```text
src/expense_splitter/storage.py
src/expense_splitter/cli.py
tests/test_storage.py
tests/test_cli.py
docs/TROUBLESHOOTING.md
REPORT.md
```

## Команда для агента

```text
Выполни P0.3 — защита пользовательских данных.

Добавь:
- atomic write через temp file + replace;
- backup перед изменением YAML;
- понятные ошибки при поврежденном YAML;
- тесты для corrupted YAML и backup creation.

Не добавляй сложную миграционную систему.
Не меняй формат данных без необходимости.
Обнови REPORT.md.
```

## Требования

```text
- save_* functions пишут во временный файл, затем atomic replace;
- перед заменой существующего файла создается backup;
- backup naming содержит timestamp;
- поврежденный YAML не приводит к stack trace для пользователя;
- CLI показывает понятную ошибку и путь к проблемному файлу.
```

## Проверки

```powershell
python -m pytest tests/test_storage.py -v
python -m pytest tests/test_cli.py -v
python -m pytest tests -v
python -m compileall -q src tests
```

## Commit

```powershell
git add src/expense_splitter/storage.py src/expense_splitter/cli.py tests/test_storage.py tests/test_cli.py docs/TROUBLESHOOTING.md REPORT.md
git commit -m "feat: add atomic storage writes and data safety checks"
git push
```

## Критерии завершения

```text
- storage writes atomic;
- backup создается;
- corrupted YAML обработан дружелюбно;
- тесты проходят.
```

---

# P0.4 — Исправление GitHub Actions и структуры remote

## Цель

Исправить P0-дефект: remote проект лежит во вложенной папке `expense-splitter/`, а workflow запускает команды из repo root.

## Файлы

```text
.github/workflows/ci.yml
.github/workflows/build-release.yml
README.md
REPORT.md
```

Или структура репозитория, если принято решение поднять проект в root.

## Команда для агента

```text
Выполни P0.4 — исправление GitHub Actions и структуры remote.

Сначала определи фактическую структуру:
- проект в root;
- или проект во вложенной папке expense-splitter/.

Выбери один путь:
A. Перенести проект в root репозитория.
B. Настроить workflow working-directory: expense-splitter.

Предпочтительно A, если это не ломает историю и пользователь согласен.
Без согласия на крупный перенос используй B.

Обнови CI так, чтобы clean GitHub run устанавливал проект и запускал тесты.
Обнови REPORT.md.
```

## Минимальный CI

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: windows-latest
    defaults:
      run:
        shell: pwsh
        working-directory: .
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install --upgrade pip
      - run: python -m pip install -e ".[dev]"
      - run: python -m pytest tests -v
      - run: python -m compileall -q src tests
      - run: expense-splitter --help
```

Если проект во вложенной папке, поставить:

```yaml
working-directory: expense-splitter
```

## Проверки

Локально:

```powershell
python -m pip install -e ".[dev]"
python -m pytest tests -v
```

После push:

```powershell
gh run list --limit 5
gh run view --log
```

## Commit

```powershell
git add .github/workflows README.md REPORT.md
git commit -m "fix: align GitHub Actions with project layout"
git push
```

## Критерии завершения

```text
- GitHub Actions запускается из правильной директории;
- pip install проходит в CI;
- pytest проходит или failure documented;
- REPORT.md обновлен.
```

---

# P0.5 — Исправление PyInstaller packaging

## Цель

Исправить P0-дефект: `.spec` использует неверные относительные пути.

## Файлы

```text
packaging/expense_splitter.spec
scripts/build-windows.ps1
scripts/build-unix.sh
docs/PACKAGING.md
REPORT.md
```

## Команда для агента

```text
Выполни P0.5 — исправление PyInstaller packaging.

Цель:
- spec paths должны соответствовать фактической структуре;
- build scripts должны работать из корня проекта;
- собираться должны expense-splitter и expense-splitter-launcher;
- пользовательские данные не должны зашиваться как рабочая data директория.

Не запускай тяжелую сборку, если окружение не готово; в таком случае укажи команду и причину пропуска.
Обнови REPORT.md.
```

## Требования

```text
- build-windows.ps1 запускается из project root;
- spec использует корректный project root;
- dist/ и build/ не коммитятся;
- docs/PACKAGING.md соответствует фактическим командам.
```

## Проверки

Легкие:

```powershell
python -m py_compile src\expense_splitter\cli.py src\expense_splitter\launcher.py
python -m compileall -q src
```

Сборка, если окружение готово:

```powershell
.\scripts\build-windows.ps1
.\dist\expense-splitter.exe --help
.\dist\expense-splitter-launcher.exe --help
```

## Commit

```powershell
git add packaging/expense_splitter.spec scripts/build-windows.ps1 scripts/build-unix.sh docs/PACKAGING.md REPORT.md
git commit -m "fix: repair PyInstaller packaging paths"
git push
```

## Критерии завершения

```text
- spec paths исправлены;
- build scripts используют правильный root;
- сборка проверена или explicitly deferred;
- dist/build не staged.
```

---

# P1.1 — validate-data, backup, restore

## Цель

Добавить пользовательские команды проверки и восстановления данных.

## Файлы

```text
src/expense_splitter/cli.py
src/expense_splitter/storage.py
src/expense_splitter/validation.py
tests/test_validation.py
tests/test_cli.py
README.md
docs/USER_GUIDE.md
docs/TROUBLESHOOTING.md
REPORT.md
```

## Команда для агента

```text
Выполни P1.1 — validate-data, backup, restore.

Добавь CLI-команды:
- validate-data;
- backup;
- restore.

validate-data должен проверять participants, groups, purchases и выводить понятные ошибки.
backup должен создавать архив или копию data directory.
restore должен восстанавливать из backup с подтверждением.

Добавь тесты.
Обнови README/docs/REPORT.
```

## validate-data должен проверять

```text
- unknown payer;
- unknown participant;
- duplicate participant names;
- duplicate group names;
- duplicate purchase participants;
- empty participants;
- invalid amount;
- invalid date;
- missing data files;
- corrupted YAML;
- group members exist.
```

## Проверки

```powershell
python -m pytest tests/test_validation.py -v
python -m pytest tests/test_cli.py -v
python -m pytest tests -v
expense-splitter validate-data --help
expense-splitter backup --help
expense-splitter restore --help
```

## Commit

```powershell
git add src/expense_splitter/cli.py src/expense_splitter/storage.py src/expense_splitter/validation.py tests/test_validation.py tests/test_cli.py README.md docs/USER_GUIDE.md docs/TROUBLESHOOTING.md REPORT.md
git commit -m "feat: add data validation backup and restore commands"
git push
```

## Критерии завершения

```text
- validate-data работает;
- backup/restore работают;
- тесты проходят;
- документация обновлена.
```

---

# P1.2 — CRUD участников и групп в CLI

## Цель

Добавить управление участниками и группами через CLI.

## Файлы

```text
src/expense_splitter/cli.py
src/expense_splitter/storage.py
src/expense_splitter/models.py
tests/test_cli.py
tests/test_storage.py
README.md
docs/USER_GUIDE.md
REPORT.md
```

## Команда для агента

```text
Выполни P1.2 — CRUD участников и групп в CLI.

Добавь команды:
participants list/add/rename/remove
groups list/add/rename/remove/add-member/remove-member

Удаление участника должно быть безопасным:
- если участник есть в purchases, не удалять без force;
- предпочтительно archive/deactivate вместо физического удаления.

Добавь тесты и документацию.
```

## Команды

```powershell
expense-splitter participants list
expense-splitter participants add "Анна"
expense-splitter participants rename "Анна" "Анна Иванова"
expense-splitter participants remove "Анна Иванова"

expense-splitter groups list
expense-splitter groups add "Новая группа"
expense-splitter groups add-member "Новая группа" "Павел"
expense-splitter groups remove-member "Новая группа" "Павел"
expense-splitter groups rename "Новая группа" "Офис"
expense-splitter groups remove "Офис"
```

## Проверки

```powershell
python -m pytest tests/test_cli.py -v
python -m pytest tests -v
expense-splitter participants --help
expense-splitter groups --help
```

## Commit

```powershell
git add src/expense_splitter/cli.py src/expense_splitter/storage.py src/expense_splitter/models.py tests/test_cli.py tests/test_storage.py README.md docs/USER_GUIDE.md REPORT.md
git commit -m "feat: add participant and group management commands"
git push
```

## Критерии завершения

```text
- участника можно добавить через CLI;
- группу можно создать и изменить;
- нельзя случайно сломать исторические покупки;
- тесты проходят.
```

---

# P1.3 — CRUD покупок в CLI

## Цель

Добавить редактирование и удаление покупок.

## Файлы

```text
src/expense_splitter/cli.py
src/expense_splitter/storage.py
tests/test_cli.py
README.md
docs/USER_GUIDE.md
REPORT.md
```

## Команда для агента

```text
Выполни P1.3 — CRUD покупок в CLI.

Добавь:
- purchases edit;
- purchases delete;
- понятный список ID покупок;
- защиту от удаления без confirm;
- тесты и документацию.
```

## Команды

```powershell
expense-splitter purchases edit <purchase-id> --amount 1500
expense-splitter purchases edit <purchase-id> --payer "Павел"
expense-splitter purchases edit <purchase-id> --participants "Павел,Сергей"
expense-splitter purchases delete <purchase-id> --confirm DELETE_PURCHASE
```

Если текущая команда называется `list-purchases`, сохранить совместимость.

## Проверки

```powershell
python -m pytest tests/test_cli.py -v
python -m pytest tests -v
expense-splitter purchases --help
```

## Commit

```powershell
git add src/expense_splitter/cli.py src/expense_splitter/storage.py tests/test_cli.py README.md docs/USER_GUIDE.md REPORT.md
git commit -m "feat: add purchase edit and delete commands"
git push
```

## Критерии завершения

```text
- покупку можно безопасно изменить;
- покупку можно удалить только с confirm;
- исторические данные не портятся;
- тесты проходят.
```

---

# P1.4 — UX launcher для обычного пользователя

## Цель

Довести launcher до состояния, где обычный пользователь может выполнять ключевые операции без запоминания CLI.

## Файлы

```text
src/expense_splitter/launcher.py
src/expense_splitter/cli.py
tests/test_launcher.py
README.md
docs/USER_GUIDE.md
REPORT.md
```

## Команда для агента

```text
Выполни P1.4 — улучшение UX launcher.

Launcher должен поддерживать:
- help / about;
- добавить покупку;
- посмотреть покупки;
- посмотреть балансы;
- посмотреть переводы;
- создать отчет;
- validate-data;
- backup;
- restore;
- добавить/переименовать/архивировать участника;
- управление группами;
- редактирование/удаление покупок;
- открыть папку данных;
- открыть папку отчетов;
- выход.

Не дублируй бизнес-логику в launcher.
Launcher должен вызывать сервисные функции или CLI helpers.
Добавь smoke tests.
Обнови docs и REPORT.
```

## Проверки

```powershell
python -m pytest tests/test_launcher.py -v
python -m pytest tests -v
expense-splitter-launcher --help
.\scripts\run-launcher.ps1
```

Если launcher полностью интерактивный, тестировать через injectable input/output или функции меню, чтобы не зависать в CI.

## Commit

```powershell
git add src/expense_splitter/launcher.py src/expense_splitter/cli.py tests/test_launcher.py README.md docs/USER_GUIDE.md REPORT.md
git commit -m "feat: expand UX launcher management flows"
git push
```

## Критерии завершения

```text
- launcher имеет help;
- участника можно добавить через launcher;
- группу можно изменить через launcher;
- покупку можно добавить/изменить/удалить через launcher;
- smoke tests проходят.
```

---

# P1.5 — Fair rounding policy

## Цель

Убрать систематическое смещение, когда остаток округления всегда получает последний участник.

## Файлы

```text
src/expense_splitter/calculator.py
src/expense_splitter/models.py
tests/test_calculator.py
README.md
docs/USER_GUIDE.md
REPORT.md
```

## Команда для агента

```text
Выполни P1.5 — fair rounding policy.

Определи и реализуй явную политику распределения округлительных остатков.
Не используй float.
Сохрани инвариант: сумма shares равна сумме purchase amount.
Добавь тесты.
Обнови README/docs/REPORT.
```

## Возможные политики

Выбрать одну и описать:

```text
A. deterministic by sorted participant name;
B. rotating remainder by purchase id/date;
C. largest remainder method;
D. configurable policy.
```

Рекомендуется:

```text
largest remainder method с детерминированным tie-breaker.
```

## Проверки

```powershell
python -m pytest tests/test_calculator.py -v
python -m pytest tests -v
```

## Commit

```powershell
git add src/expense_splitter/calculator.py src/expense_splitter/models.py tests/test_calculator.py README.md docs/USER_GUIDE.md REPORT.md
git commit -m "fix: implement fair rounding policy for shared expenses"
git push
```

## Критерии завершения

```text
- остаток не назначается всегда последнему участнику;
- сумма shares равна amount;
- политика описана;
- тесты проходят.
```

---

# P1.6 — Документация и placeholders cleanup

## Цель

Привести документацию к фактическому состоянию проекта.

## Файлы

```text
README.md
docs/INSTALLATION.md
docs/PACKAGING.md
docs/TROUBLESHOOTING.md
docs/USER_GUIDE.md
docs/RELEASE_CHECKLIST.md
REPORT.md
```

## Команда для агента

```text
Выполни P1.6 — очистка и актуализация документации.

Убери placeholders:
- YOUR_GITHUB_USERNAME;
- <repository_url> без пояснения;
- bot@manus.im;
- несуществующие пути и команды.

Документация должна быть на русском, в UTF-8.
README должен соответствовать фактическим scripts, CLI, launcher, install, tests, packaging.
Добавь USER_GUIDE и RELEASE_CHECKLIST, если их нет.
Обнови REPORT.md.
```

## Проверки

```powershell
Select-String -Path README.md,docs\*.md -Pattern "YOUR_GITHUB_USERNAME|bot@manus.im|<repository_url>|TODO|FIXME"
git diff --name-only
```

Если Python не менялся, тесты можно не запускать, но указать это в REPORT.md.

## Commit

```powershell
git add README.md docs REPORT.md
git commit -m "docs: align user documentation with actual project state"
git push
```

## Критерии завершения

```text
- placeholders отсутствуют;
- команды в docs работают;
- GitHub URL актуален;
- документация на русском;
- REPORT.md обновлен.
```

---

# P1.7 — Installer smoke и release workflow

## Цель

Проверить установщики и подготовить release workflow.

## Файлы

```text
scripts/install.ps1
scripts/run-cli.ps1
scripts/run-launcher.ps1
scripts/uninstall.ps1
scripts/install.sh
scripts/run-cli.sh
scripts/run-launcher.sh
.github/workflows/build-release.yml
docs/INSTALLATION.md
docs/RELEASE_CHECKLIST.md
REPORT.md
```

## Команда для агента

```text
Выполни P1.7 — installer smoke и release workflow.

Проверь Windows scripts:
- install.ps1;
- run-cli.ps1;
- run-launcher.ps1;
- uninstall.ps1.

Проверь, что scripts работают с путями, содержащими пробелы.
Проверь, что run scripts можно запускать из project root.
Обнови release workflow и docs.
Не публикуй release без отдельного разрешения.
```

## Проверки

```powershell
.\scripts\install.ps1
.\scripts\run-cli.ps1 --help
.\scripts\run-cli.ps1 validate-data
.\scripts\run-launcher.ps1
```

Если launcher интерактивный, зафиксировать ручной smoke-test.

Linux/macOS scripts — best effort, если окружение доступно:

```bash
./scripts/install.sh
./scripts/run-cli.sh --help
```

## Commit

```powershell
git add scripts .github/workflows docs/INSTALLATION.md docs/RELEASE_CHECKLIST.md REPORT.md
git commit -m "fix: stabilize installer scripts and release workflow"
git push
```

## Критерии завершения

```text
- install.ps1 проходит;
- run-cli.ps1 --help работает;
- launcher запускается;
- release workflow соответствует структуре;
- GitHub Actions status проверен.
```

---

# P2.1 — Улучшение отчетов и экспортов

## Цель

Сделать отчеты полезнее для реального использования.

## Файлы

```text
src/expense_splitter/reporting.py
src/expense_splitter/cli.py
tests/test_reporting.py
README.md
docs/USER_GUIDE.md
REPORT.md
```

## Команда для агента

```text
Выполни P2.1 — улучшение отчетов.

Добавь:
- Markdown отчет;
- CSV экспорт balances;
- CSV экспорт settlements;
- CSV экспорт purchases;
- опционально Excel export, если зависимость оправдана.

Не добавляй тяжелые зависимости без необходимости.
Добавь тесты и документацию.
```

## Проверки

```powershell
python -m pytest tests/test_reporting.py -v
python -m pytest tests -v
expense-splitter report --help
```

## Commit

```powershell
git add src/expense_splitter/reporting.py src/expense_splitter/cli.py tests/test_reporting.py README.md docs/USER_GUIDE.md REPORT.md
git commit -m "feat: improve reports and exports"
git push
```

---

# P2.2 — Production-ready final quality gate

## Цель

Проверить проект перед присвоением статуса production-ready candidate.

## Команда для агента

```text
Выполни P2.2 — финальный quality gate.

Не меняй код без необходимости.
Запусти полный набор проверок.
Обнови REPORT.md и docs/RELEASE_CHECKLIST.md.
Если все проверки успешны, зафиксируй статус production-ready candidate.
Если есть failures, составь список блокеров.
```

## Проверки

```powershell
git status --short
python -m pip install -e ".[dev]"
python -m pytest tests -v
python -m compileall -q src tests
expense-splitter --help
expense-splitter init --help
expense-splitter validate-data --help
expense-splitter backup --help
expense-splitter restore --help
expense-splitter-launcher --help
.\scripts\install.ps1
.\scripts\run-cli.ps1 --help
```

Packaging, если готово:

```powershell
.\scripts\build-windows.ps1
.\dist\expense-splitter.exe --help
.\dist\expense-splitter-launcher.exe --help
```

GitHub:

```powershell
git status --short
git log --oneline -10
gh run list --limit 5
```

## Commit

```powershell
git add REPORT.md docs/RELEASE_CHECKLIST.md
git commit -m "docs: record production readiness quality gate"
git push
```

## Критерии завершения

```text
- editable install проходит;
- tests проходят;
- CLI работает;
- launcher работает;
- storage безопасен;
- validate/backup/restore работают;
- installer smoke пройден или failure documented;
- GitHub Actions зеленые;
- generated artifacts not staged;
- git status clean;
- REPORT.md содержит итоговый статус.
```

---

## Финальный ответ агента после каждого этапа

```text
1. Этап.
2. Статус.
3. Что изменено.
4. Какие проверки выполнены.
5. Какие проверки пропущены и почему.
6. Ошибки/warnings.
7. Измененные файлы.
8. Commit hash.
9. Push status.
10. GitHub Actions status, если был push.
11. Generated artifacts not staged.
12. Пользовательские данные не перезаписаны.
13. Git/GitHub commands outside sandbox only.
14. Следующий рекомендуемый этап.
```
