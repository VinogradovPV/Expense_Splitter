# Аналитика Expense Splitter

## Запуск

```powershell
expense-splitter analytics --period month --year 2026 --month 6 --format all
expense-splitter analytics --period quarter --year 2026 --quarter 2 --format all
expense-splitter analytics --period year --year 2026 --format all
```

GUI предоставляет те же периоды и форматы без командной строки.

## Текущий snapshot взаиморасчетов

`expense-splitter current-report` не является календарной analytics-командой. Он строит отчет по
текущему scope `open` или `all`, отвечает на вопрос "из чего сейчас состоят долги" и не фильтрует
покупки по месяцу, кварталу или году.

```powershell
expense-splitter current-report --scope open --format all
expense-splitter current-report --scope all --format xlsx
```

Default: `--scope open --format all`. Закрытые покупки не входят в `open`; отчет не закрывает
период, не помечает покупки settled и не меняет YAML-данные.

Output:

```text
reports/current_state/open_<YYYY-MM-DD_HH-MM-SS>/
├── current_state_report.md
├── current_state_dashboard.html
├── current_state.xlsx
├── metadata.json
├── tables/
│   ├── summary.csv
│   ├── purchases.csv
│   ├── by_category.csv
│   ├── by_payer.csv
│   ├── by_participant.csv
│   ├── balances.csv
│   ├── settlements.csv
│   └── warnings.csv
└── charts/
    ├── spending_by_category.png
    ├── spending_by_payer.png
    ├── participant_share.png
    ├── balances.png
    └── top_purchases.png
```

## Форматы

- `markdown` — читабельный `analytics_report.md`;
- `csv` — точные таблицы в UTF-8 with BOM;
- `png` — статические графики;
- `html` — offline dashboard с embedded CSS и локальными PNG;
- `xlsx` — Excel-книга через `openpyxl`, без COM и установленного Excel;
- `all` — все форматы и `metadata.json`.

## Структура output

```text
reports/analytics/<year>/<period-id>/
├── analytics_report.md
├── analytics_dashboard.html
├── expense_analytics_<period-id>.xlsx
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

## Таблицы и предупреждения

Таблицы строятся из единого `AnalyticsDataset`; расчётная логика не дублируется в renderers.
`warnings.csv` содержит покупки без даты и причины отсутствия графиков. Если данных нет, пустые
графики не создаются, а HTML/XLSX показывают понятное сообщение.

## HTML

`analytics_dashboard.html` не использует CDN, Plotly, внешний CSS/JS или web-server. Его нужно
хранить рядом с `tables/` и `charts/`, поскольку ссылки относительные.

## XLSX

Книга содержит листы Summary, Purchases, By Category, By Payer, By Participant, Balances,
Settlements, Top Purchases, Warnings и Charts. Денежные значения записываются числами с форматом
`#,##0.00`. Табличные листы имеют freeze panes и auto-filter. Для совместимости с Microsoft Excel
используются обычные диапазоны без `xl/tables` XML; на Charts вставляются готовые PNG.

## Generated artifacts

Вся папка `reports/` является generated artifact и исключена из Git. Её можно удалить и создать
заново; исходные YAML в `data/` при этом не затрагиваются.
