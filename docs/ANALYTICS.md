# Аналитика Expense Splitter

## Static HTML

Формат `html` создаёт полностью автономный отчёт `analytics_dashboard.html` с embedded CSS,
локальными PNG-графиками, таблицами и относительными ссылками на CSV и Markdown. Внешний интернет,
CDN, Plotly, Jinja2 и web-server не используются.

```powershell
expense-splitter analytics --period month --year 2026 --month 6 --format html
expense-splitter analytics --period quarter --year 2026 --quarter 2 --format html
expense-splitter analytics --period year --year 2026 --format html
```

`--format html` и `--format all` создают полный комплект Markdown/metadata/CSV/доступных PNG/HTML.
Если данных для графика нет, HTML показывает понятное сообщение вместо битого изображения.

## XLSX

Формат `xlsx` создаёт `expense_analytics_<period-id>.xlsx` через `openpyxl`, без Excel COM,
Microsoft Excel, pandas или web-server. В книге есть листы Summary, Purchases, By Category,
By Payer, By Participant, Balances, Settlements, Top Purchases, Warnings и Charts.

Денежные значения записываются числовыми ячейками с форматом `#,##0.00`; это позволяет Excel и
LibreOffice сортировать, суммировать и фильтровать значения без потери отображаемой точности до
копеек. Табличные листы используют существующие CSV-структуры аналитики, freeze panes и filters.
На Charts вставляются уже сформированные PNG; при пустом периоде выводится понятное сообщение.

Документ фиксирует решения для аналитических отчетов Expense Splitter.

## Единая палитра P1.A.0

Палитра аналитических графиков хранится внутри проекта:

```text
src/expense_splitter/visual/palette.py
```

Модуль содержит только визуальные константы и небольшие helper-функции. Расчетная логика аналитики остается в будущих профильных модулях `analytics.py`, `analytics_charts.py` и `analytics_reporting.py`.

## Метаданные палитры

Текущие значения:

| Поле | Значение |
|---|---|
| `palette_name` | `expense_splitter_default` |
| `palette_version` | `1` |

Для будущих PNG-графиков закреплены стратегии:

| График | Стратегия цвета |
|---|---|
| `spending_by_category.png` | `stable_category_map` |
| `spending_by_payer.png` | `qualitative_palette_by_payer` |
| `participant_share.png` | `qualitative_palette_by_participant` |
| `balances.png` | `balance_status_map` |
| `period_trend.png` | `period_chronological_sequential` |
| `top_purchases.png` | `qualitative_palette_by_rank` |

## Правила применения

- Категории должны получать цвета через stable color map по отсортированному списку категорий.
- Периоды должны получать цвета в хронологическом порядке.
- Балансы должны использовать статусную окраску: положительный net — `к получению`, отрицательный — `к оплате`, нулевой — `ноль`.
- Если значений больше, чем цветов, палитра циклически повторяется.
- Не использовать seaborn, случайные цвета и дефолтные цвета matplotlib для production PNG-графиков.

## Analytics core P1.A.1

Периодная аналитика реализуется в модуле:

```text
src/expense_splitter/analytics.py
```

Поддерживаемые периоды:

| Период | Параметры | Диапазон |
|---|---|---|
| `month` | `year`, `month` 1..12 | с первого по последний день месяца |
| `quarter` | `year`, `quarter` 1..4 | кварталы Q1, Q2, Q3, Q4 |
| `year` | `year` | с 1 января по 31 декабря |

Core-функции:

- `parse_period()` возвращает `PeriodSpec` с `start_date`, `end_date` и `period_id`.
- `filter_purchases_by_period()` фильтрует покупки по датам; покупки без даты по умолчанию исключаются.
- `build_analytics_dataset()` собирает сводку, агрегации, balances, settlements, top purchases и warnings.
- `aggregate_summary()`, `aggregate_by_category()`, `aggregate_by_payer()`, `aggregate_by_participant()` возвращают табличные структуры для будущего CSV/Markdown слоя.
- `build_top_purchases()` сортирует крупнейшие покупки периода.
- `build_warnings()` фиксирует покупки без даты.

Правила:

- Денежные значения считаются через `Decimal`, без `float`.
- Балансы и settlements строятся через существующие `calculate_balances()` и `calculate_settlements()`.
- `None` в категории отображается как `Без категории`.
- `purchase_name` всегда присутствует; пустые значения нормализуются моделью в `н/д`.

## Analytics reports P1.A.2

Команда формирует отчеты за месяц, квартал или год:

```powershell
expense-splitter analytics --period month --year 2026 --month 6 --format all
expense-splitter analytics --period quarter --year 2026 --quarter 2 --format all
expense-splitter analytics --period year --year 2026 --format all
```

Поддерживаются форматы `markdown`, `csv`, `png` и `all`. Результаты сохраняются в `reports/analytics/<year>/<period-id>/`.

`all` создает `analytics_report.md`, `metadata.json`, девять CSV-таблиц в `tables/` и до шести PNG-графиков в `charts/`. CSV записываются в `utf-8-sig`, денежные значения имеют два знака после запятой.

Графики строятся через matplotlib с backend `Agg` и единой палитрой проекта. Если за период нет данных, генерация не падает: отсутствующий график фиксируется в `tables/warnings.csv`. Кириллица отображается шрифтом DejaVu Sans, поставляемым с matplotlib; при системной подмене шрифта возможен fallback matplotlib.

HTML и XLSX не входят в P1.A.2 и остаются для P2.

## Пользовательский workflow P1.A.3

Минимальный пользовательский smoke-test на Windows:

```powershell
.\.venv\Scripts\expense-splitter.exe analytics --period month --year 2026 --month 6 --format all
Get-ChildItem reports\analytics -Recurse
```

Ожидаемый результат:

- создан каталог `reports/analytics/2026/2026-06/`;
- есть `analytics_report.md` и `metadata.json`;
- есть папка `tables/` с обязательными CSV;
- есть папка `charts/` с PNG, если за период есть данные;
- если графики не созданы из-за отсутствия данных, в `tables/warnings.csv` есть строки `chart_no_data`.

Подробное пользовательское руководство находится в `docs/USER_GUIDE.md`.
