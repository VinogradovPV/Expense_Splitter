# Expense Splitter: пошаговая инструкция production-ready v5
## Самодостаточная инструкция: P0.6 + schema/purchase_name + аналитика Markdown/CSV/PNG с единой палитрой

Дата актуализации: 2026-06-18.

Инструкция самодостаточна. Codex не должен ссылаться на изменения относительно предыдущих версий и не должен пересказывать историю появления требований.  
Рабочая директория:

```powershell
cd C:\Users\Rockaudit\LLM_CHAT\expense_splitter
```

---

## 0. Общие правила для всех этапов

### 0.1. Язык и UTF-8

Все пользовательские тексты, Markdown, YAML, JSON, CSV, Python source, CLI help и отчеты писать на русском языке в UTF-8.

Перед проверками с русским текстом в PowerShell:

```powershell
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
chcp 65001
```

Все Python read/write операции с текстом выполнять с `encoding="utf-8"`.

### 0.2. Mojibake check

Поддерживать QA-скрипт:

```text
scripts/qa/check_text_encoding.py
```

Он должен искать признаки mojibake:

```text
Рџ Рђ Р‘ РІ Рµ Ð Ñ ╨ ╤ �
```

Проверка:

```powershell
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
```

Если найден mojibake, этап не завершен.

### 0.3. Outside sandbox

Сразу outside sandbox выполнять:

```text
git/gh
pip install
pytest
compileall
PyInstaller
PowerShell scripts с ExecutionPolicy Bypass
.venv\Scripts\*.exe
.\dist\*.exe
```

Не повторять внутри sandbox команды, которые уже давали `PermissionError`.

### 0.4. Progress report

После каждого этапа обновлять:

```text
docs/reports/prod_ready_progress_report.md
```

### 0.5. Перед commit

```powershell
git status --short
git diff --name-only
git diff --cached --name-only
git diff --cached --name-only | Select-String "\.venv|__pycache__|\.pytest_cache|\.ruff_cache|dist/|build/|\.egg-info|\.bak$|\.tmp$|\.part$|\.crdownload$"
```

Generated artifacts не должны быть staged.

---

# P0.6 — GitHub push, CI verification, UTF-8/mojibake baseline

## Цель

Зафиксировать локальные P0-исправления, отправить их в GitHub, проверить CI и добавить базовый UTF-8/mojibake guard.

## Создать/изменить

Создать при отсутствии:

```text
scripts/qa/check_text_encoding.py
```

Изменить:

```text
docs/reports/prod_ready_progress_report.md
```

## Требования

1. Проверить текущий branch, remote, commits, untracked/generated artifacts.
2. Создать/переключиться на рабочую ветку:

```powershell
git checkout -b prod-ready/p0-p1
```

Если ветка уже есть:

```powershell
git checkout prod-ready/p0-p1
```

3. Добавить mojibake checker.
4. Проверить, что P0.1–P0.5 изменения staged корректно.
5. Сделать commit, если есть изменения.
6. Push в GitHub.
7. Проверить GitHub Actions.

## Проверки

```powershell
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
chcp 65001

.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\expense-splitter.exe --help
.\.venv\Scripts\expense-splitter-launcher.exe --help
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
```

## Commit

```powershell
git add .github .gitignore README.md docs packaging pyproject.toml scripts src tests
git commit -m "chore: publish P0 production-ready baseline"
git push -u origin prod-ready/p0-p1
gh run list --limit 5
```

## Критерии завершения

```text
- P0 changes committed.
- Branch pushed.
- GitHub Actions checked.
- Mojibake checker exists and passes.
- Generated artifacts not staged.
```

---

# P1.0 — Data schema v2 и purchase_name

## Цель

Добавить поле `purchase_name` / «Наименование покупки» с default `н/д`, не ломая legacy YAML с `title`.

## Создать/изменить

```text
src/expense_splitter/models.py
src/expense_splitter/storage.py
src/expense_splitter/defaults.py
src/expense_splitter/cli.py
src/expense_splitter/launcher.py
tests/test_storage.py
tests/test_cli.py
tests/test_launcher.py
docs/DATA_SCHEMA.md
docs/reports/prod_ready_progress_report.md
```

## Реализация

Выбран вариант C:

```text
purchase_name = canonical field
title = legacy alias on read only
```

Требования:

1. Новые покупки сохраняются с `purchase_name`.
2. Default `purchase_name`: `н/д`.
3. Старые YAML с `title` читаются корректно.
4. Если есть `title`, но нет `purchase_name`, storage возвращает `purchase_name = title`.
5. Если нет обоих полей, storage возвращает `purchase_name = "н/д"`.
6. Новые YAML не должны писать `title`.
7. CLI и launcher показывают «Наименование покупки».
8. Пустой ввод в CLI/launcher превращается в `н/д`.
9. Все операции с русским текстом сохраняют UTF-8.

## Проверки

```powershell
.\.venv\Scripts\python.exe -m py_compile src\expense_splitter\models.py src\expense_splitter\storage.py src\expense_splitter\cli.py src\expense_splitter\launcher.py
.\.venv\Scripts\python.exe -m pytest tests\test_storage.py tests\test_cli.py tests\test_launcher.py -v
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
```

## Commit

```powershell
git add src tests docs README.md
git commit -m "feat: add purchase_name data schema compatibility"
git push
```

## Критерии завершения

```text
- purchase_name работает в модели/storage/CLI/launcher.
- Legacy title читается.
- Новые данные пишут purchase_name.
- Default н/д покрыт тестами.
- Mojibake check passes.
```

---



# P1.A.0 — Единая палитра аналитических графиков

## Цель

Интегрировать единую цветовую палитру в аналитику Expense Splitter до генерации PNG-графиков, чтобы все отчеты имели стабильный визуальный стиль и не зависели от дефолтных цветов matplotlib.

## Создать/изменить

Создать:

```text
src/expense_splitter/visual/__init__.py
src/expense_splitter/visual/palette.py
tests/test_palette.py
```

Изменить при необходимости:

```text
src/expense_splitter/analytics_charts.py
tests/test_analytics_charts.py
docs/ANALYTICS.md
docs/reports/prod_ready_progress_report.md
```

## Требования

1. Создать модуль `src/expense_splitter/visual/palette.py`.
2. Не импортировать палитру из OFZ-проекта; адаптировать ее как собственный модуль Expense Splitter.
3. В модуле хранить только визуальные константы и helper-функции.
4. Не размещать в `palette.py` расчетную логику аналитики.
5. Использовать базовые палитры:

```python
QUALITATIVE_PALETTE = ["#001542", "#09C886", "#FF5A50", "#3A3377", "#822B93", "#2EA3D8", "#7D8AFA", "#166A75", "#B48DE9", "#60AEA1", "#E6D957", "#D8D8D8"]
SEQUENTIAL_PALETTE = ["#D2ECF9", "#BFD5E9", "#ACBED9", "#90A7C8", "#737BAA", "#606998", "#4D4A87", "#3A3377"]
CONTRAST_SEQUENTIAL_PALETTE = ["#D2ECF9", "#BFD5E9", "#ACBED9", "#90A7C8", "#737BAA", "#606998", "#4D4A87", "#3A3377"]
STATUS_PALETTE = {"норма": "#09C886", "предупреждение": "#E6D957", "риск": "#FF5A50", "требует проверки": "#FF5A50", "нет данных": "#D8D8D8"}
```

6. Создать Expense Splitter specific maps:

```python
EXPENSE_DIMENSION_COLOR_MAP = {
    "Период": "#001542",
    "Категория": "#166A75",
    "Плательщик": "#3A3377",
    "Участник": "#822B93",
    "Покупка": "#2EA3D8",
}

BALANCE_STATUS_COLOR_MAP = {
    "к получению": "#09C886",
    "к оплате": "#FF5A50",
    "ноль": "#D8D8D8",
}
```

7. Реализовать helper-функции:

```python
build_stable_color_map(labels, palette=QUALITATIVE_PALETTE)
color_for_label(label, labels, palette=QUALITATIVE_PALETTE)
build_period_color_map(periods)
color_for_period(period, periods)
color_for_balance_status(net_amount)
```

8. Все цвета должны быть валидными HEX `#[0-9A-Fa-f]{6}`.
9. Для категорий использовать stable color map по отсортированным категориям.
10. Для периодов использовать хронологический порядок.
11. Для балансов использовать статусную окраску: положительный net — `к получению`, отрицательный — `к оплате`, ноль — `ноль`.
12. Не переносить OFZ-специфичные словари `FORMAT_COLOR_MAP`, `MATURITY_COLOR_MAP`, `DIMENSION_COLOR_MAP` как есть.
13. В `metadata.json` аналитического отчета писать `palette_name`, `palette_version`, `color_strategy` для каждого графика.

## Проверки

```powershell
.\.venv\Scripts\python.exe -m py_compile src\expense_splitter\visual\palette.py tests\test_palette.py
.\.venv\Scripts\python.exe -m pytest tests\test_palette.py -v
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
```

## Commit

```powershell
git add src/expense_splitter/visual tests/test_palette.py docs/ANALYTICS.md docs/reports/prod_ready_progress_report.md
git commit -m "Add unified analytics color palette"
```

## Критерии завершения

```text
- palette.py создан внутри Expense Splitter.
- OFZ-specific maps не перенесены вслепую.
- Все HEX цвета валидны.
- Helper-функции покрыты тестами.
- Mojibake check проходит.
```

# P1.A.1 — Analytics core: периодные агрегации

## Цель

Создать слой аналитики за месяц/квартал/год без генерации графиков на этом подэтапе.

## Создать/изменить

Создать:

```text
src/expense_splitter/analytics.py
tests/test_analytics.py
docs/ANALYTICS.md
```

Изменить:

```text
src/expense_splitter/reporting.py
docs/reports/prod_ready_progress_report.md
```

## Требования

Реализовать функции:

```text
parse_period(period, year, month=None, quarter=None)
filter_purchases_by_period(purchases, period_spec, include_undated=False)
build_analytics_dataset(participants, groups, purchases, period_spec)
aggregate_summary(...)
aggregate_by_category(...)
aggregate_by_payer(...)
aggregate_by_participant(...)
build_top_purchases(...)
build_warnings(...)
```

Периоды:

```text
month: YYYY-MM-01..last day
quarter: Q1/Q2/Q3/Q4
year: YYYY-01-01..YYYY-12-31
```

Правила:

1. Использовать `Decimal`, не `float`.
2. Использовать существующие `calculate_balances` и settlement logic для выбранного периода.
3. Покупки без даты по умолчанию не включать в периодную аналитику.
4. Покупки без даты добавлять в warnings.
5. Категория `None` отображается как `Без категории`.
6. `purchase_name` всегда присутствует, default `н/д`.

## Проверки

```powershell
.\.venv\Scripts\python.exe -m py_compile src\expense_splitter\analytics.py
.\.venv\Scripts\python.exe -m pytest tests\test_analytics.py -v
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
```

## Commit

```powershell
git add src\expense_splitter\analytics.py tests\test_analytics.py docs\ANALYTICS.md docs\reports\prod_ready_progress_report.md
git commit -m "feat: add period analytics core"
git push
```

## Критерии завершения

```text
- Месяц/квартал/год фильтруются корректно.
- Агрегации покрыты тестами.
- Undated purchases handled via warnings.
- Balance/settlement analytics uses existing business logic.
```

---

# P1.A.2 — Analytics reports: Markdown + CSV + PNG

## Цель

Реализовать выбранный вариант 4: базовый production-ready отчет с таблицами и графиками.

## Создать/изменить

Создать:

```text
src/expense_splitter/analytics_reporting.py
src/expense_splitter/analytics_charts.py
tests/test_analytics_reporting.py
tests/test_analytics_charts.py
```

Изменить:

```text
pyproject.toml
src/expense_splitter/cli.py
src/expense_splitter/launcher.py
docs/ANALYTICS.md
README.md
docs/reports/prod_ready_progress_report.md
```

## Dependencies

Добавить `matplotlib` как runtime dependency только если он еще не добавлен.

Не добавлять `plotly`, `jinja2`, `pandas`, `openpyxl` на P1.A.2. HTML/XLSX — P2.

## Output structure

```text
reports/analytics/<year>/<period-id>/
├── analytics_report.md
├── metadata.json
├── tables/
│   ├── summary.csv
│   ├── purchases.csv
│   ├── by_category.csv
│   ├── by_payer.csv
│   ├── by_participant.csv
│   ├── balances.csv
│   ├── settlements.csv
│   ├── top_purchases.csv
│   └── warnings.csv
└── charts/
    ├── spending_by_category.png
    ├── spending_by_payer.png
    ├── participant_share.png
    ├── balances.png
    ├── period_trend.png
    └── top_purchases.png
```

## CSV требования

1. CSV писать в UTF-8 with BOM или plain UTF-8. Предпочтительно `utf-8-sig` для Excel compatibility на Windows.
2. Decimal сериализовать как строки с двумя знаками.
3. Участников в CSV писать через `, ` или `; ` стабильно.
4. Заголовки таблиц на русском языке.

## PNG требования

1. Использовать `matplotlib`, не seaborn.
2. Backend должен работать headless: `Agg`.
3. Графики сохранять в PNG.
4. Кириллица должна отображаться корректно или иметь documented fallback.
5. Если данных для графика нет, создать предупреждение в `warnings.csv` и не падать.

## CLI

Добавить команду:

```powershell
expense-splitter analytics --period month --year 2026 --month 6 --format all
expense-splitter analytics --period quarter --year 2026 --quarter 2 --format all
expense-splitter analytics --period year --year 2026 --format all
```

Форматы:

```text
markdown
csv
png
all
```

`all` генерирует Markdown + CSV + PNG + metadata.json.

## Launcher

Добавить пункт меню:

```text
Аналитика за период
```

Пользователь выбирает период, год, месяц/квартал, формат. После генерации показать путь к отчету.

## Проверки

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m py_compile src\expense_splitter\analytics_reporting.py src\expense_splitter\analytics_charts.py src\expense_splitter\cli.py src\expense_splitter\launcher.py
.\.venv\Scripts\python.exe -m pytest tests\test_analytics.py tests\test_analytics_reporting.py tests\test_analytics_charts.py tests\test_cli.py tests\test_launcher.py -v
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\expense-splitter.exe analytics --period month --year 2026 --month 6 --format all
.\.venv\Scripts\expense-splitter.exe analytics --period quarter --year 2026 --quarter 2 --format all
.\.venv\Scripts\expense-splitter.exe analytics --period year --year 2026 --format all
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
```

## Commit

```powershell
git add pyproject.toml src tests docs README.md
git commit -m "feat: add analytics reports with tables and charts"
git push
gh run list --limit 5
```

## Критерии завершения

```text
- analytics команда работает для month/quarter/year.
- Создаются Markdown, CSV, PNG, metadata.json.
- Все обязательные таблицы есть.
- Все обязательные графики создаются или documented warning.
- Тесты проходят.
- Mojibake check passes.
- Generated report artifacts не staged.
```

---

# P1.A.3 — Документация аналитики и пользовательский smoke-test

## Цель

Довести пользовательскую документацию по аналитике до понятного состояния и провести smoke-test на Windows.

## Изменить

```text
README.md
docs/ANALYTICS.md
docs/USER_GUIDE.md
docs/TROUBLESHOOTING.md
docs/reports/prod_ready_progress_report.md
```

## Документировать

1. Что такое аналитика за месяц/квартал/год.
2. Какие таблицы создаются.
3. Какие графики создаются.
4. Где лежат отчеты.
5. Как открыть PNG/CSV/Markdown.
6. Почему HTML/XLSX пока P2.
7. Как работает `purchase_name`.
8. Что значит `н/д`.
9. Что делать при mojibake в CSV/PowerShell.
10. Как удалить generated reports перед commit.

## Проверки

```powershell
.\.venv\Scripts\expense-splitter.exe analytics --period month --year 2026 --month 6 --format all
Get-ChildItem reports\analytics -Recurse
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
git status --short
```

Generated reports не коммитить.

## Commit

```powershell
git add README.md docs
git commit -m "docs: document analytics reports workflow"
git push
gh run list --limit 5
```

## Критерии завершения

```text
- Пользователь может создать analytics report по README.
- Документация не содержит placeholders.
- UTF-8/mojibake check passes.
- Generated reports not staged.
```

---

# P2.A — HTML/XLSX future extension, не для текущего этапа

HTML dashboard и XLSX report не реализовывать в P1.A, если пользователь отдельно не попросит.

Будущие этапы:

```text
P2.A.1 HTML dashboard через Plotly/Jinja2.
P2.A.2 XLSX report через openpyxl/xlsxwriter.
```

Они не блокируют production-ready candidate базового CLI/launcher продукта.

---

## Финальный ответ Codex после каждого этапа

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
12. UTF-8/mojibake check status.
13. Git/GitHub commands outside sandbox only.
14. Следующий рекомендуемый этап.
```
