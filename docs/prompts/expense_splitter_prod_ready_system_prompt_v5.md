# Expense Splitter: системный промпт production-ready v5
## Самодостаточный промпт для Codex: production-ready, аналитика, UTF-8 и единая палитра

Дата актуализации: 2026-06-18.

Этот документ является самодостаточным источником требований для Codex. Не предполагается знание предыдущих версий промпта или инструкции. Не объясняй в отчетах, что изменилось относительно v1/v2/v3/v4; работай по этому документу как по актуальному контракту.  
Проект: `Expense Splitter` / `expense-splitter`.  
Репозиторий: `https://github.com/VinogradovPV/Expense_Splitter`.  
Локальный корень проекта:

```powershell
cd C:\Users\Rockaudit\LLM_CHAT\expense_splitter
```

---

## 1. Фактический статус после P0

Не начинай проект с нуля. Codex уже выполнил P0-работы и зафиксировал их в `docs/reports/prod_ready_progress_report.md`.

Фактический статус:

```text
P0.0 GitHub/local synchronization baseline: completed.
P0.1 Python packaging / editable install: completed.
P0.2 storage/init participants+groups overwrite fix: completed.
P0.3 data safety minimal layer: completed.
P0.4 GitHub Actions root-layout alignment: completed locally.
P0.5 PyInstaller packaging paths: completed locally, Windows build verified.
Следующий обязательный этап перед feature work: P0.6 GitHub push, CI verification, UTF-8/mojibake baseline.
```

Не повторяй эти исправления без явной причины:

- `pyproject.toml` уже переведен на `setuptools.build_meta`.
- Editable install и CLI entry points уже подтверждены.
- `initialize_data_files()` уже не должен терять `participants` и `groups`.
- YAML-запись уже должна использовать atomic write и timestamped `.bak` backup.
- Corrupted YAML должен давать дружелюбный `StorageError`.
- GitHub Actions локально выровнены под root-layout.
- PyInstaller spec и Windows build scripts локально исправлены.

---

## 2. Главная цель следующих этапов

Довести проект до production-ready candidate через управляемые этапы:

1. P0.6: запушить локальные P0-исправления, проверить CI, добавить UTF-8/mojibake baseline.
2. P1.0: расширить модель и хранение данных до `schema_version: 2`.
3. P1.1: добавить новое поле покупки `purchase_name` / «Наименование покупки» с default `н/д`.
4. P1.A: добавить аналитические отчеты за месяц/квартал/год с таблицами и графиками.
5. P1.B: обновить CLI, UX launcher, документацию и тесты.
6. P2: добавить расширенные форматы HTML/XLSX только после стабилизации базовой аналитики.

---

## 3. Жесткое правило Git/GitHub

Все `git` и `gh` команды выполнять **только outside sandbox** из корня проекта:

```powershell
cd C:\Users\Rockaudit\LLM_CHAT\expense_splitter
```

Запрещено выполнять `git` и `gh` внутри Codex sandbox.

Перед каждым commit outside sandbox:

```powershell
git status --short
git diff --name-only
git diff --cached --name-only
git diff --cached --name-only | Select-String "\.venv|__pycache__|\.pytest_cache|\.ruff_cache|dist/|build/|\.egg-info|\.bak$|\.tmp$|\.part$|\.crdownload$"
```

После push outside sandbox:

```powershell
gh run list --limit 5
```

Если текущий run упал:

```powershell
gh run view --log
```

Не переходи к следующему этапу, если текущий commit сломал CI и failure не был явно deferred в progress report.

---

## 4. Outside-sandbox разрешения из-за проблем Codex sandbox

Codex уже выявил повторяющиеся проблемы sandbox:

- `PermissionError` на `C:\Users\Rockaudit\AppData\Local\Temp\pytest-of-Rockaudit`;
- `PermissionError` при `pip install -e` во временных директориях;
- PowerShell execution policy для `.ps1`;
- необходимость запускать `.venv\Scripts\*.exe` и `dist\*.exe` в реальной Windows-среде;
- PyInstaller build должен проверяться вне sandbox.

Поэтому следующие команды **сразу выполнять outside sandbox**, без предварительного запуска внутри sandbox:

```text
git / gh
python -m pip install ...
python -m pytest ...
python -m compileall ...
python -m PyInstaller ...
powershell -NoProfile -ExecutionPolicy Bypass -File ...
.\.venv\Scripts\expense-splitter.exe ...
.\.venv\Scripts\expense-splitter-launcher.exe ...
.\dist\expense-splitter.exe ...
.\dist\expense-splitter-launcher.exe ...
```

Если команда уже один раз дала sandbox `PermissionError`, не повторяй ее в sandbox. Выполняй outside sandbox и фиксируй это в финальном ответе.

---

## 5. UTF-8 и mojibake policy

Проект русскоязычный. Все Markdown, YAML, JSON, CSV, TXT, Python source, docs, CLI help и отчеты должны быть в UTF-8.

Перед проверками русского текста в PowerShell выполнять:

```powershell
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
chcp 65001
```

Python-файлы должны читать и писать текст только с явным `encoding="utf-8"`.

Добавить/поддерживать QA-скрипт:

```text
scripts/qa/check_text_encoding.py
```

Он должен искать признаки mojibake в tracked text files:

```text
П
А
Б
в
е
Ð
Ñ
╨
╤
�
```

Не считать бинарные файлы и generated artifacts. Скрипт должен пропускать `.venv`, `.git`, `dist`, `build`, `__pycache__`, `.pytest_cache`, `.ruff_cache`, `*.egg-info`.

Обязательные проверки после этапов с русским текстом:

```powershell
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
```

Если найден mojibake, этап не считается завершенным.

---

## 6. Не коммитить generated artifacts

Не коммитить:

```text
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
dist/
build/
*.egg-info/
*.bak
*.tmp
*.part
*.crdownload
reports/tmp/
```

Timestamped `.bak` user-data backups должны оставаться локальными пользовательскими файлами, не частью repository history.

---

## 7. Модель данных v2 и поле purchase_name

Нужно добавить новое пользовательское поле:

```text
Наименование покупки
```

Каноническое техническое имя:

```text
purchase_name
```

Default:

```text
н/д
```

### 7.1. Рассмотренные варианты

#### Вариант A — полностью переименовать `title` в `purchase_name`

Плюсы: чистая модель.  
Минусы: ломает старые YAML, тесты, CLI, отчеты и совместимость.  
Решение: не использовать как прямой одномоментный вариант.

#### Вариант B — хранить одновременно `title` и `purchase_name`

Плюсы: простая обратная совместимость.  
Минусы: риск рассинхронизации двух полей.  
Решение: не использовать как постоянную модель.

#### Вариант C — `purchase_name` как canonical field, `title` как legacy alias

Плюсы: совместимость + чистое новое API.  
Минусы: требуется migration/read compatibility layer.  
Решение: **выбранный вариант**.

### 7.2. Обязательное поведение

1. Новые YAML-файлы пишут `purchase_name`, а не `title`.
2. При чтении legacy YAML:
   - если есть `purchase_name`, использовать его;
   - если нет `purchase_name`, но есть `title`, использовать `title` как `purchase_name`;
   - если нет ни `purchase_name`, ни `title`, ставить `н/д`.
3. UI, CLI, launcher и отчеты показывают «Наименование покупки».
4. В Python-модели canonical field: `purchase_name`.
5. Старый `title` можно оставить только как read-only compatibility alias, если это нужно для безопасного перехода.
6. `validate-data` должен предупреждать о legacy `title` без `purchase_name`.

---

## 8. Хранение данных v2

В YAML добавить schema version:

```yaml
schema_version: 2
participants:
  - name: Павел
groups:
  - name: Кофе
    members: [Павел, Сергей]
purchases:
  - id: "..."
    date: "2026-06-18"
    purchase_name: "Кофе"
    amount: "1200.00"
    payer: "Павел"
    participants: [Павел, Сергей]
    category: "Напитки"
    comment: null
```

Если текущая storage layout использует отдельные YAML-файлы, не ломай ее без необходимости. Но каждый файл с доменными данными должен поддерживать schema metadata или совместимый migration layer.

Обязательные требования:

- backward compatibility со старыми YAML;
- atomic write сохраняется;
- timestamped `.bak` сохраняется;
- corrupted YAML остается дружелюбной ошибкой;
- migration не должна молча уничтожать данные;
- `validate-data` должен показывать schema version и warnings.

---

## 9. Аналитика: зафиксирован вариант 4

Выбран гибридный production-вариант.

### 9.1. Базовый production-ready уровень

Обязательно реализовать:

```text
Markdown summary
CSV tables
PNG charts
metadata.json
```

Форматы HTML dashboard и XLSX являются P2-расширениями и не блокируют первый production-ready релиз.

### 9.2. Периоды

Поддержать отчеты:

```text
month
quarter
year
```

Месяц:

```text
--period month --year YYYY --month 1..12
```

Квартал:

```text
--period quarter --year YYYY --quarter 1..4
```

Год:

```text
--period year --year YYYY
```

Покупки без даты по умолчанию не включаются в period analytics и попадают в warnings. Опция `--include-undated` может добавлять их только в summary/warnings, но не должна искажать month/quarter trend.

### 9.3. CLI contract

Основная команда:

```powershell
expense-splitter analytics --period month --year 2026 --month 6
expense-splitter analytics --period quarter --year 2026 --quarter 2
expense-splitter analytics --period year --year 2026
```

Форматы:

```powershell
expense-splitter analytics --period month --year 2026 --month 6 --format markdown
expense-splitter analytics --period month --year 2026 --month 6 --format csv
expense-splitter analytics --period month --year 2026 --month 6 --format png
expense-splitter analytics --period month --year 2026 --month 6 --format all
```

Для P1 обязательно поддержать `--format all`, который генерирует Markdown + CSV + PNG + metadata.json.

### 9.4. Output structure

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

`period-id`:

```text
month: YYYY-MM
quarter: YYYY-QN
year: YYYY
```

### 9.5. Обязательные таблицы

| Таблица | Назначение |
|---|---|
| `summary.csv` | период, всего расходов, количество покупок, средний чек, число участников |
| `purchases.csv` | покупки с `purchase_name`, датой, плательщиком, суммой, категорией, участниками |
| `by_category.csv` | сумма и количество покупок по категориям |
| `by_payer.csv` | сколько оплатил каждый плательщик |
| `by_participant.csv` | сколько расходов начислено каждому участнику |
| `balances.csv` | paid/share/net по каждому участнику |
| `settlements.csv` | кто кому переводит |
| `top_purchases.csv` | крупнейшие покупки периода |
| `warnings.csv` | покупки без даты, legacy fields, invalid/ambiguous data |

### 9.6. Обязательные графики PNG

Использовать `matplotlib`. Не использовать seaborn. Все графики должны использовать единую палитру из `src/expense_splitter/visual/palette.py`. Графики должны быть читаемыми в Windows, корректно работать с кириллицей и сохраняться в UTF-8-safe paths.

| График | Тип | Файл |
|---|---|---|
| Расходы по категориям | horizontal bar или pie только при <=6 категорий | `spending_by_category.png` |
| Расходы по плательщикам | horizontal bar | `spending_by_payer.png` |
| Доли расходов участников | horizontal bar | `participant_share.png` |
| Балансы участников | horizontal bar | `balances.png` |
| Тренд расходов | line | `period_trend.png` |
| Топ покупок | horizontal bar | `top_purchases.png` |

Для месяца trend строится по дням.  
Для квартала trend строится по месяцам внутри квартала.  
Для года trend строится по месяцам.

### 9.7. Расчет аналитики

Аналитика должна использовать существующие расчетные функции, а не дублировать бизнес-логику.

Обязательные принципы:

- денежные значения через `Decimal`;
- агрегация сумм без `float`;
- округление соответствует существующей политике проекта;
- settlement для выбранного периода считается только по покупкам периода;
- warnings не должны блокировать отчет, если данные валидны для расчета;
- corrupted YAML должен давать controlled error.

---

## 10. Единая цветовая палитра аналитики

В проекте должна быть единая палитра для всех PNG-графиков аналитики. Палитра задается внутри проекта Expense Splitter, а не импортируется из другого проекта.

Создать модуль:

```text
src/expense_splitter/visual/palette.py
```

Если пакета `visual` нет, создать:

```text
src/expense_splitter/visual/__init__.py
```

Модуль должен хранить только визуальные константы и небольшие helper-функции. Расчетная логика аналитики должна оставаться в профильных модулях аналитики, например `analytics.py`, `analytics_charts.py`, `analytics_reporting.py`.

### 10.1. Базовые цвета

Использовать палитру как основу визуального стиля Expense Splitter:

```python
QUALITATIVE_PALETTE = [
    "#001542",
    "#09C886",
    "#FF5A50",
    "#3A3377",
    "#822B93",
    "#2EA3D8",
    "#7D8AFA",
    "#166A75",
    "#B48DE9",
    "#60AEA1",
    "#E6D957",
    "#D8D8D8",
]

SEQUENTIAL_PALETTE = [
    "#D2ECF9",
    "#BFD5E9",
    "#ACBED9",
    "#90A7C8",
    "#737BAA",
    "#606998",
    "#4D4A87",
    "#3A3377",
]

CONTRAST_SEQUENTIAL_PALETTE = [
    "#D2ECF9",
    "#BFD5E9",
    "#ACBED9",
    "#90A7C8",
    "#737BAA",
    "#606998",
    "#4D4A87",
    "#3A3377",
]

STATUS_PALETTE = {
    "норма": "#09C886",
    "предупреждение": "#E6D957",
    "риск": "#FF5A50",
    "требует проверки": "#FF5A50",
    "нет данных": "#D8D8D8",
}
```

### 10.2. Expense Splitter specific maps

Не переносить OFZ-специфичные словари вроде `FORMAT_COLOR_MAP`, `MATURITY_COLOR_MAP`, `DIMENSION_COLOR_MAP` как доменные сущности. Вместо них создать карты, относящиеся к Expense Splitter:

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

WARNING_STATUS_PALETTE = STATUS_PALETTE
```

### 10.3. Helper functions

Реализовать helper-функции:

```python
def build_stable_color_map(labels: Sequence[object], palette: Sequence[str] = QUALITATIVE_PALETTE) -> dict[str, str]: ...

def color_for_label(label: object, labels: Sequence[object], palette: Sequence[str] = QUALITATIVE_PALETTE) -> str: ...

def build_period_color_map(periods: Sequence[object]) -> dict[str, str]: ...

def color_for_period(period: object, periods: Sequence[object]) -> str: ...

def color_for_balance_status(net_amount: Decimal | int | float | str) -> str: ...
```

Правила стабильности:

1. Одинаковые категории в разных отчетах получают одинаковые цвета, если порядок labels одинаковый.
2. Для категорий использовать отсортированный список категорий, кроме случаев, где порядок определяется таблицей top-N.
3. Для периодов использовать хронологический порядок.
4. Для участников использовать алфавитный порядок, если отчет не требует сортировки по сумме.
5. Для top purchases использовать цвета из `QUALITATIVE_PALETTE` по порядку рейтинга.
6. Если значений больше, чем цветов, палитра циклически повторяется.

### 10.4. Применение в PNG-графиках

Все графики аналитики должны использовать эту палитру:

| График | Цветовая логика |
|---|---|
| `spending_by_category.png` | категории через stable category color map |
| `spending_by_payer.png` | плательщики через qualitative palette |
| `participant_share.png` | участники через qualitative palette |
| `balances.png` | `к получению` зеленый, `к оплате` красный, `ноль` серый |
| `period_trend.png` | основная линия `#001542`, markers `#09C886` |
| `top_purchases.png` | top-N цвета из qualitative palette |
| warning/status charts, если появятся | `STATUS_PALETTE` |

Не использовать seaborn. Не полагаться на дефолтные цвета matplotlib. Не использовать случайные цвета.

### 10.5. PNG rendering rules

Для всех PNG:

1. `dpi >= 150`.
2. Размер не меньше `10x6` inches для сложных графиков.
3. Заголовки, подписи осей и легенды на русском языке в UTF-8.
4. Кириллица должна отображаться без mojibake.
5. Длинные подписи категорий и покупок переносить или обрезать безопасно с сохранением полного значения в CSV.
6. Для денежных значений использовать подписи в рублях.
7. Для отрицательных балансов использовать статусную окраску, а не случайный цвет.
8. После сохранения закрывать figure через `plt.close(fig)`.

### 10.6. Metadata по палитре

`metadata.json` аналитического отчета должен содержать:

```json
{
  "palette_name": "expense_splitter_default",
  "palette_version": 1,
  "qualitative_palette": ["#001542", "#09C886", "#FF5A50"],
  "charts": {
    "spending_by_category.png": {
      "color_strategy": "stable_category_map"
    }
  }
}
```

Не обязательно дублировать все цвета, но нужно зафиксировать название палитры, версию и стратегию цвета для каждого графика.

### 10.7. Проверки палитры

Добавить тесты:

```text
tests/test_palette.py
tests/test_analytics_charts.py
```

Проверить:

1. Все цвета валидные HEX `#[0-9A-Fa-f]{6}`.
2. `build_stable_color_map()` стабилен.
3. `color_for_period()` возвращает ожидаемый цвет для периода.
4. `color_for_balance_status()` различает положительный, отрицательный и нулевой баланс.
5. PNG-графики создаются и не пустые.
6. Создание графиков не вызывает mojibake в путях и названиях.
7. Analytics metadata содержит `palette_name` и `palette_version`.

---

## 11. UX launcher

Launcher должен получить пункт:

```text
Аналитика за период
```

Минимальный сценарий:

1. Выбрать период: месяц / квартал / год.
2. Ввести год.
3. Для месяца ввести месяц.
4. Для квартала ввести квартал.
5. Выбрать формат: all / markdown / csv / png.
6. Сформировать отчет.
7. Показать путь к `analytics_report.md` и папкам `tables/`, `charts/`.

Launcher также должен использовать поле «Наименование покупки» при добавлении покупки. Если пользователь оставил поле пустым, сохранять `н/д`.

---

## 12. Документация

Обновить:

```text
README.md
docs/USER_GUIDE.md
docs/INSTALLATION.md
docs/TROUBLESHOOTING.md
docs/reports/prod_ready_progress_report.md
```

При необходимости создать:

```text
docs/ANALYTICS.md
docs/DATA_SCHEMA.md
```

Документация должна описывать:

- поле `purchase_name` / «Наименование покупки»;
- default `н/д`;
- legacy compatibility с `title`;
- schema version;
- периодные отчеты;
- структуру output-папок;
- таблицы;
- PNG-графики;
- ограничения HTML/XLSX как будущие P2-функции;
- UTF-8/mojibake troubleshooting.

---

## 12. Финальный ответ Codex после каждого этапа

В каждом финальном ответе Codex обязан указать:

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
