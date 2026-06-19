# Expense Splitter: пошаговая инструкция P2
## Settlement periods, UX launcher, HTML/XLSX analytics

Дата актуализации: 2026-06-19.

Документ является самостоятельной пошаговой инструкцией для Codex. Не ссылаться на предыдущие версии как на историю изменений. Работать по этому документу как по актуальному плану P2.

---

## 0. Общие правила для всех этапов P2

### 0.1. Рабочая директория

Все команды проекта выполнять из корня:

```powershell
cd C:\Users\Rockaudit\LLM_CHAT\expense_splitter
```

### 0.2. Outside sandbox

Сразу выполнять outside sandbox:

```text
git / gh
pip install -e ".[dev]"
pytest
compileall
ruff
PowerShell scripts
PyInstaller
.venv\Scripts\*.exe
dist\*.exe
```

Если внутри sandbox возникает `PermissionError`, Temp issue или ExecutionPolicy issue, не повторять внутри sandbox. Выполнить outside sandbox.

### 0.3. UTF-8 prelude на Windows

Перед проверками:

```powershell
chcp 65001
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
```

### 0.4. Обязательные проверки после кодовых этапов

Минимум:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
```

Если затронуты Python-файлы, желательно:

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests
```

### 0.5. Git hygiene

Перед commit:

```powershell
git status --short
git diff --name-only
git diff --cached --name-only
```

Не коммитить generated artifacts:

```text
reports/analytics/
build/
dist/
.venv/
.pytest_cache/
.ruff_cache/
__pycache__/
*.egg-info/
*.bak
```

### 0.6. Progress report

После каждого этапа обновлять:

```text
docs/reports/prod_ready_progress_report.md
```

---

# P2.S.1 - Settlement periods foundation

## Цель

Добавить безопасную модель закрытия плавающих периодов взаиморасчетов без удаления покупок и без переписывания истории.

## Создать/изменить файлы

Создать:

```text
src/expense_splitter/settlement_periods.py
tests/test_settlement_periods.py
docs/SETTLEMENT_PERIODS.md
```

Изменить:

```text
src/expense_splitter/models.py
src/expense_splitter/storage.py
src/expense_splitter/cli.py
src/expense_splitter/reporting.py
docs/USER_GUIDE.md
README.md
docs/reports/prod_ready_progress_report.md
```

## Требования

1. Добавить файл данных `data/settlement_periods.yaml`.
2. Добавить dataclass/model `SettlementPeriod`.
3. Добавить поля покупки:
   - `settled: bool = False`;
   - `settlement_period_id: str | None = None`.
4. Старые покупки без этих полей считаются открытыми.
5. Закрытие периода не удаляет покупки.
6. Закрытие периода создает snapshot settlements.
7. Перед закрытием создается backup YAML-файлов.
8. Запись атомарная.
9. Повторное закрытие уже закрытой покупки запрещено или явно пропускается с warning.
10. Reopen требует `--confirm REOPEN_PERIOD`.

## CLI

Добавить:

```powershell
expense-splitter settlement-period preview --from 2026-06-01 --to 2026-06-19
expense-splitter settlement-period close --from 2026-06-01 --to 2026-06-19 --name "Июнь до 19.06" --confirm CLOSE_PERIOD
expense-splitter settlement-period list
expense-splitter settlement-period show settlement_2026_06_19_001
expense-splitter settlement-period reopen settlement_2026_06_19_001 --confirm REOPEN_PERIOD
```

Расширить:

```powershell
expense-splitter balances --scope open
expense-splitter balances --scope all
expense-splitter balances --settlement-period settlement_2026_06_19_001
expense-splitter settle --scope open
expense-splitter settle --scope all
expense-splitter settle --settlement-period settlement_2026_06_19_001
```

Default `--scope open`.

## Команда для Codex

```text
Выполни P2.S.1 Settlement periods foundation.

Цель: добавить безопасное закрытие плавающего периода взаиморасчетов без удаления покупок.

Реализуй data/model/storage/CLI для settlement periods:
- data/settlement_periods.yaml;
- SettlementPeriod model;
- settled и settlement_period_id у Purchase;
- preview/close/list/show/reopen;
- balances/settle --scope open|all и --settlement-period;
- default scope open;
- close требует --confirm CLOSE_PERIOD;
- reopen требует --confirm REOPEN_PERIOD;
- backup перед close/reopen;
- atomic write;
- backward compatibility со старыми purchases.yaml.

Не реализуй HTML/XLSX и большой launcher на этом этапе.
Не удаляй покупки при close.
Обнови docs/SETTLEMENT_PERIODS.md, README.md, docs/USER_GUIDE.md и progress report.
```

## Проверки

```powershell
.\.venv\Scripts\python.exe -m py_compile src\expense_splitter\settlement_periods.py src\expense_splitter\storage.py src\expense_splitter\cli.py
.\.venv\Scripts\python.exe -m pytest tests\test_settlement_periods.py -v
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
```

CLI smoke:

```powershell
.\.venv\Scripts\expense-splitter.exe init --with-examples
.\.venv\Scripts\expense-splitter.exe settlement-period preview --from 2026-06-01 --to 2026-06-19
.\.venv\Scripts\expense-splitter.exe settlement-period close --from 2026-06-01 --to 2026-06-19 --name "Тестовый период" --confirm CLOSE_PERIOD
.\.venv\Scripts\expense-splitter.exe settlement-period list
.\.venv\Scripts\expense-splitter.exe balances --scope open
.\.venv\Scripts\expense-splitter.exe balances --scope all
```

## Commit

```powershell
git add src tests docs README.md
git commit -m "feat: add settlement periods"
git push
```

## Критерии завершения

```text
- close не удаляет покупки;
- default balances/settle считают только open purchases;
- scope all возвращает старое полное поведение;
- closed period можно посмотреть;
- reopen работает только с confirm;
- tests зеленые;
- CI зеленый после push.
```

---

# P2.UX.1 - Launcher settlement period UX

## Цель

Добавить в UX launcher пользовательский сценарий “Закрыть период и обнулить текущие взаиморасчеты”.

## Изменить файлы

```text
src/expense_splitter/launcher.py
tests/test_launcher.py
tests/test_launcher_flows.py
docs/USER_GUIDE.md
README.md
docs/reports/prod_ready_progress_report.md
```

## Требования

Launcher должен иметь меню:

```text
1. Покупки
2. Участники и группы
3. Расчеты и переводы
4. Аналитика
5. Закрытие / обнуление периода взаиморасчетов
6. Backup / restore
7. Проверка данных
8. Настройки и папки
9. Выход
```

Раздел закрытия периода:

1. Выбрать дату начала.
2. Выбрать дату окончания.
3. Показать покупки периода.
4. Показать итоговые переводы.
5. Показать предупреждение: покупки не удаляются.
6. Создать backup.
7. Запросить подтверждение.
8. Закрыть период.
9. Показать новый текущий open balance.

## Команда для Codex

```text
Выполни P2.UX.1 Launcher settlement period UX.

Добавь в launcher меню закрытия периода:
- preview;
- предупреждение;
- подтверждение;
- close;
- просмотр закрытых периодов;
- показать open balances после close.

Используй функции P2.S.1, не дублируй бизнес-логику.
Не реализуй HTML/XLSX на этом этапе.
Обнови docs и progress report.
```

## Проверки

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_launcher.py tests\test_launcher_flows.py -v
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\expense-splitter-launcher.exe --help
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
```

## Commit

```powershell
git add src tests docs README.md
git commit -m "feat: add settlement period launcher flow"
git push
```

---

# P2.A.1 - Static HTML analytics report

## Цель

Добавить формат `html` для аналитических отчетов.

## Создать/изменить файлы

Создать:

```text
src/expense_splitter/analytics_html.py
tests/test_analytics_html.py
```

Изменить:

```text
src/expense_splitter/analytics_reporting.py
src/expense_splitter/cli.py
src/expense_splitter/launcher.py
docs/ANALYTICS.md
docs/USER_GUIDE.md
README.md
docs/reports/prod_ready_progress_report.md
```

## Требования

1. Добавить `--format html`.
2. `--format all` включает HTML.
3. Создавать `analytics_dashboard.html`.
4. HTML самодостаточный, offline, UTF-8.
5. HTML содержит:
   - summary;
   - warnings;
   - таблицы;
   - PNG-графики;
   - ссылки на CSV.
6. CSS встроен в HTML.
7. Не использовать CDN.
8. Не использовать Plotly на этом этапе.
9. HTML generated artifact не коммитить.

## Команда для Codex

```text
Выполни P2.A.1 Static HTML analytics report.

Добавь формат html к команде analytics.
HTML должен использовать уже созданные tables/*.csv, charts/*.png и metadata.json.
Сделай offline self-contained analytics_dashboard.html со встроенным CSS.
Не добавляй Plotly/Jinja2, если можно обойтись стандартной библиотекой.
Сохрани UTF-8 и anti-mojibake checks.
Обнови docs и progress report.
```

## Проверки

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_analytics_html.py -v
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\expense-splitter.exe analytics --period month --year 2026 --month 6 --format html
.\.venv\Scripts\expense-splitter.exe analytics --period quarter --year 2026 --quarter 2 --format all
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
```

## Commit

```powershell
git add src tests docs README.md
git commit -m "feat: add static HTML analytics report"
git push
```

---

# P2.A.2 - XLSX analytics report

## Цель

Добавить Excel-отчет аналитики через `openpyxl`.

## Создать/изменить файлы

Создать:

```text
src/expense_splitter/analytics_xlsx.py
tests/test_analytics_xlsx.py
```

Изменить:

```text
pyproject.toml
src/expense_splitter/analytics_reporting.py
src/expense_splitter/cli.py
src/expense_splitter/launcher.py
docs/ANALYTICS.md
docs/USER_GUIDE.md
README.md
docs/Troubleshooting.md
docs/reports/prod_ready_progress_report.md
```

## Требования

1. Добавить dependency `openpyxl`.
2. Добавить `--format xlsx`.
3. `--format all` включает XLSX.
4. Создавать `expense_analytics_<period-id>.xlsx`.
5. Листы:
   - Summary;
   - Purchases;
   - By Category;
   - By Payer;
   - By Participant;
   - Balances;
   - Settlements;
   - Top Purchases;
   - Warnings;
   - Charts.
6. Вставлять PNG-графики на лист Charts.
7. Не использовать Excel COM automation.
8. Работать на Windows/Linux/macOS.
9. XLSX generated artifact не коммитить.

## Команда для Codex

```text
Выполни P2.A.2 XLSX analytics report.

Добавь openpyxl и формат xlsx к analytics.
Создавай workbook с обязательными листами и вставкой PNG charts на лист Charts.
Не используй Excel COM automation.
Проверь кириллицу, Decimal output, generated artifact policy.
Обнови docs, troubleshooting и progress report.
```

## Проверки

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest tests\test_analytics_xlsx.py -v
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\expense-splitter.exe analytics --period month --year 2026 --month 6 --format xlsx
.\.venv\Scripts\expense-splitter.exe analytics --period year --year 2026 --format all
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
```

## Commit

```powershell
git add pyproject.toml src tests docs README.md
git commit -m "feat: add XLSX analytics report"
git push
```

---

# P2.REL.1 - P2 quality gate and release readiness

## Цель

Проверить весь P2-функционал перед следующим stable candidate.

## Проверки

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
.\.venv\Scripts\expense-splitter.exe --help
.\.venv\Scripts\expense-splitter-launcher.exe --help
.\.venv\Scripts\expense-splitter.exe analytics --period month --year 2026 --month 6 --format all
.\.venv\Scripts\expense-splitter.exe analytics --period quarter --year 2026 --quarter 2 --format all
.\.venv\Scripts\expense-splitter.exe analytics --period year --year 2026 --format all
```

Если PyInstaller нужно проверить:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-windows.ps1 -NoUpx
.\dist\expense-splitter.exe --help
.\dist\expense-splitter-launcher.exe --help
```

## Commit

```powershell
git add docs README.md
git commit -m "docs: record P2 release readiness"
git push
```

## Финальный критерий

```text
- settlement periods работают;
- launcher умеет закрывать период;
- analytics all создает Markdown, CSV, PNG, HTML, XLSX;
- tests/ruff/compileall/encoding зелёные;
- GitHub Actions зелёные;
- generated reports не staged;
- docs обновлены.
```
