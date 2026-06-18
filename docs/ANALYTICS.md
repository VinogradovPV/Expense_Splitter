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
