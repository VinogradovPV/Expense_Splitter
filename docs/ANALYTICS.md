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

В визуальных отчетах `open` отображается как `Открытые покупки`, `all` как `Все покупки с
историей`, а `snapshot` как `Дата формирования отчета`. CLI и `metadata.json` сохраняют
технические значения для совместимости.

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
    ├── balances.png
    ├── participant_share.png
    ├── operations_by_day.png  # только если есть минимум две уникальные даты
    ├── spending_by_category.png
    ├── spending_by_payer.png
    └── top_purchases.png
```

Current-report строит график `operations_by_day.png` с пользовательским названием `Операции по
дням`, если в выбранном scope есть минимум две уникальные даты покупок. Несколько покупок в один
день агрегируются в дневную сумму. Если уникальная дата одна, график не создается, а отчет
показывает предупреждение `Недостаточно дат для построения графика операций по дням.`. PDF, HTML,
XLSX и ReportService используют только графики текущего запуска, поэтому старый
`operations_by_day.png` не попадает в новый отчет.

## Исторический отчет settlement period

`expense-splitter settlement-period report <id>` строит отчет по конкретному snapshot периода, а не
по календарному month/quarter/year и не по текущему `open/all` scope. Snapshot settlements и
`total_amount` берутся из `settlement_periods.yaml`; детали покупок восстанавливаются из текущего
`purchases.yaml` по `purchase_ids`. Если покупка уже отсутствует, отчет добавляет warning и
продолжает генерацию.

```powershell
expense-splitter settlement-period report settlement_2026_06_30_001 --format all
expense-splitter settlement-period report settlement_2026_06_30_001 --format html
expense-splitter settlement-period report settlement_2026_06_30_001 --format xlsx
```

Команда ничего не меняет в данных. Результаты лежат в
`reports/settlement_periods/<id>_<YYYY-MM-DD_HH-MM-SS>/` и включают
`settlement_period_report.md`, `settlement_period_dashboard.html`, `settlement_period.xlsx`,
`metadata.json`, CSV в `tables/` и PNG в `charts/`. Warning `period_reopened` означает, что период
позже переоткрывали, но отчет показывает сохраненный исторический snapshot.

## Форматы

- `markdown` — читабельный `analytics_report.md`;
- `csv` — точные таблицы в UTF-8 with BOM;
- `png` — статические графики;
- `html` — offline dashboard с embedded CSS и локальными PNG;
- `xlsx` — Excel-книга через `openpyxl`, без COM и установленного Excel;
- `pdf` — нативный PDF через ReportLab;
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
    ├── period_trend.png  # только если есть минимум две уникальные даты
    └── top_purchases.png
```

## Таблицы и предупреждения

Таблицы строятся из единого `AnalyticsDataset`; расчётная логика не дублируется в renderers.
`warnings.csv` содержит покупки без даты и причины отсутствия графиков. Если данных нет, пустые
графики не создаются.

График `period_trend.png` строится только при минимум двух уникальных датах покупок. Несколько
покупок в один день агрегируются в дневную сумму, например `619.00 + 550.00 = 1169.00`. Если
уникальная дата одна, график динамики пропускается, в warnings добавляется
`chart_not_enough_data`, а `period_trend` не попадает в `metadata.files`, `charts_generated`, PDF,
HTML, XLSX и delivery result. Local CLI, GUI и ReportService используют один и тот же chart policy:
пользователь видит предупреждение `Недостаточно дат для построения динамики расходов.`, а не
сообщение `Предупреждений нет.`.

В таблице `Расходы по плательщикам` для analytics, current-report и settlement-period report есть
колонка `Доля оплат, %`. Она показывает `оплачено плательщиком / общая сумма отчета * 100`, с
округлением до двух знаков; при нулевой общей сумме выводится `0.00`.

## HTML

`analytics_dashboard.html` не использует CDN, Plotly, внешний CSS/JS или web-server. Его нужно
хранить рядом с `tables/` и `charts/`, поскольку ссылки относительные.

## XLSX

Книга содержит русские листы `Сводка`, `Покупки`, `По категориям`, `По плательщикам`,
`Объем расходов на человека`, `Балансы участников`, `Итоговые переводы`, `Крупнейшие покупки`,
`Предупреждения` и `Графики`. Денежные значения записываются числами с форматом `#,##0.00`.
Табличные листы имеют freeze panes и auto-filter. Для совместимости с Microsoft Excel используются
обычные диапазоны без `xl/tables` XML; на лист `Графики` вставляются готовые PNG.

## Generated artifacts

Вся папка `reports/` является generated artifact и исключена из Git. Её можно удалить и создать
заново; исходные YAML в `data/` при этом не затрагиваются.
## PDF reports

Analytics reports support `--format pdf` and include PDF in `--format all`.

```powershell
expense-splitter analytics --period month --year 2026 --month 6 --format pdf
expense-splitter analytics --period quarter --year 2026 --quarter 2 --format pdf
expense-splitter analytics --period year --year 2026 --format pdf
```

The file is saved as `reports/analytics/<year>/<period-id>/expense_analytics_<period-id>.pdf`.
PDF is generated natively with ReportLab and local fonts; it is not browser print output.
PDF layout keeps table headings together with the table header and first data row; empty pages are
considered a defect. Chart sections use Russian user-facing titles, while internal chart keys remain
only in filenames and metadata. Non-negative expense charts start their X scale at zero; the balance
chart may use negative values and the balance table includes an explanation of the sign.

The compact A4 landscape layout uses KPI cards, two-column table sections and an adaptive chart
grid: four compact charts use 2x2, while two remaining charts are stacked at full width.
The main analytics pages no longer repeat the summary table or print every purchase. Full purchase
detail is rendered in `Приложение: все покупки` and remains unchanged in CSV/XLSX.
Participant, payer, category and purchase labels are sourced from the real report dataset. Every
PDF purchase row preserves the complete participant list and wraps it inside the cell without
`и еще N` or `+N`. Compact chart labels may be truncated with an ellipsis, while the analytics
appendix preserves the full purchase name and participant list. There is no implicit runtime
anonymization.
PDF monetary values always show two decimal places with a comma decimal separator, for example
`1 567,28`. PDF and XLSX therefore use the same monetary precision; calculation logic and CSV/XLSX
values are unchanged. Percentages use their own two-decimal format, and counts are not formatted
as money.

The purchases table is sorted by payer total descending, then by purchase amount descending inside
each payer. CSV adds `payer_total` and `payer_rank` so the grouping remains machine-readable.
