# Руководство пользователя Expense Splitter

## Быстрый сценарий аналитики

1. Установите проект и подготовьте данные:

```powershell
.\scripts\install.ps1 -Dev
.\.venv\Scripts\expense-splitter.exe init --with-examples
```

2. Создайте аналитический отчет за месяц:

```powershell
.\.venv\Scripts\expense-splitter.exe analytics --period month --year 2026 --month 6 --format all
```

3. Откройте папку:

```powershell
explorer reports\analytics\2026\2026-06
```

## Периоды

Аналитика поддерживает три периода:

| Период | Команда | Что попадает в отчет |
|---|---|---|
| Месяц | `--period month --year 2026 --month 6` | Покупки с 1 по последний день месяца |
| Квартал | `--period quarter --year 2026 --quarter 2` | Покупки за Q1/Q2/Q3/Q4 |
| Год | `--period year --year 2026` | Покупки с 1 января по 31 декабря |

Покупки без даты не включаются в периодные расчеты по умолчанию и попадают в `warnings.csv`.

## Что создается

`--format all` создает:

- `analytics_report.md` — основной Markdown-отчет;
- `metadata.json` — период, версия палитры, список файлов и число предупреждений;
- `tables/*.csv` — таблицы для Excel и ручной проверки;
- `charts/*.png` — графики, если за период есть данные для построения.

## CSV-таблицы

| Файл | Назначение |
|---|---|
| `summary.csv` | Сводка: период, общая сумма, число покупок, средний чек, участники |
| `purchases.csv` | Список покупок с `purchase_name`, датой, суммой, плательщиком и участниками |
| `by_category.csv` | Расходы по категориям |
| `by_payer.csv` | Сколько оплатил каждый плательщик |
| `by_participant.csv` | Какая доля расходов начислена каждому участнику |
| `balances.csv` | Paid/share/net по участникам |
| `settlements.csv` | Минимальные переводы между участниками |
| `top_purchases.csv` | Крупнейшие покупки периода |
| `warnings.csv` | Покупки без даты и отсутствующие графики при пустых данных |

CSV записываются в `utf-8-sig`, поэтому обычно корректно открываются в Excel на Windows.

## Графики

| Файл | Что показывает |
|---|---|
| `spending_by_category.png` | Расходы по категориям |
| `spending_by_payer.png` | Расходы по плательщикам |
| `participant_share.png` | Доли расходов участников |
| `balances.png` | Итоговые балансы |
| `period_trend.png` | Динамика расходов по дням или месяцам |
| `top_purchases.png` | Крупнейшие покупки |

Если данных нет, график не создается, а причина фиксируется в `warnings.csv`.

## Как открыть файлы

- Markdown: откройте `analytics_report.md` в VS Code, GitHub или любом Markdown-viewer.
- CSV: откройте файл из `tables/` в Excel, LibreOffice Calc или текстовом редакторе.
- PNG: откройте файл из `charts/` двойным кликом или через просмотр изображений Windows.

## `purchase_name` и `н/д`

`purchase_name` — каноническое поле v2 для наименования покупки.

Если имя покупки пустое или отсутствует, Expense Splitter подставляет `н/д`, то есть "нет данных". Старые YAML-файлы с полем `title` читаются как legacy-данные, но новые сохранения используют `purchase_name`.

## HTML и XLSX

HTML dashboard и XLSX-отчет пока не реализованы. Они отложены на P2, чтобы базовый production-ready CLI оставался простым и проверяемым.

## Generated reports и Git

Папка `reports/analytics/` является generated artifact и не должна попадать в commit. Перед коммитом проверяйте:

```powershell
git status --short --ignored
```

Если нужно удалить локальные generated reports:

```powershell
Remove-Item -Recurse -Force reports\analytics
```

Эта команда удаляет только сгенерированные аналитические отчеты, но не YAML-данные приложения.
## Периоды взаиморасчетов

Период взаиморасчетов закрывает выбранные открытые покупки за диапазон дат и сохраняет snapshot переводов. Покупки не удаляются: они остаются в истории и получают `settled: true` и `settlement_period_id`.

Предварительный просмотр:

```powershell
expense-splitter settlement-period preview --from 2026-06-01 --to 2026-06-19
```

Закрытие периода:

```powershell
expense-splitter settlement-period close --from 2026-06-01 --to 2026-06-19 --name "Июнь до 19.06" --confirm CLOSE_PERIOD
```

Просмотр истории:

```powershell
expense-splitter settlement-period list
expense-splitter settlement-period show settlement_2026_06_19_001
```

Повторное открытие периода:

```powershell
expense-splitter settlement-period reopen settlement_2026_06_19_001 --confirm REOPEN_PERIOD
```

`balances` и `settle` по умолчанию считают только открытые покупки. Для всей истории используйте `--scope all`, для конкретного закрытого периода - `--settlement-period <id>`.
