# Аналитика Expense Splitter

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
