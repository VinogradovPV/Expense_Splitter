# Периоды взаиморасчётов

## Что делает закрытие

Закрытие периода выбирает open-покупки в диапазоне дат, рассчитывает snapshot переводов и помечает
покупки `settled: true` с `settlement_period_id`. Покупки остаются в `purchases.yaml`.

GUI всегда показывает preview и предупреждение: покупки не удаляются, а новые расчёты начинаются
по открытым покупкам.

## CLI

```powershell
expense-splitter settlement-period preview --from 2026-06-01 --to 2026-06-30
expense-splitter settlement-period close --from 2026-06-01 --to 2026-06-30 --name "Июнь" --confirm CLOSE_PERIOD
expense-splitter settlement-period list
expense-splitter settlement-period show settlement_2026_06_30_001
expense-splitter settlement-period reopen settlement_2026_06_30_001 --confirm REOPEN_PERIOD
expense-splitter settlement-period report settlement_2026_06_30_001 --format all
```

## Reopen

Reopen меняет статус периода и возвращает связанные покупки в scope `open`. В GUI доступны
`Детали периода` и `Переоткрыть период`; перед reopen требуется подтверждение.

## Scope

- `open` — только незакрытые покупки;
- `all` — вся история;
- `--settlement-period <id>` — покупки конкретного snapshot.

```powershell
expense-splitter balances --scope open
expense-splitter balances --scope all
expense-splitter settle --settlement-period settlement_2026_06_30_001
```

`expense-splitter current-report --scope open --format all` использует тот же open scope, но
только строит отчет о текущем состоянии взаиморасчетов. Команда не закрывает период, не меняет
`settled` и не записывает `settlement_period_id`. Для фиксации периода используйте
`settlement-period close`.

## Отчет периода

`settlement-period report <id>` создает исторический отчет по snapshot периода. Это не analytics за
месяц/квартал/год и не current-report `open/all`: отчет отвечает, какие покупки входили в закрытый
период, сколько было потрачено, как расходы распределились по категориям, плательщикам и
участникам, какие балансы восстановлены по покупкам периода и какие итоговые переводы были
сохранены в snapshot. Snapshot settlements не пересчитываются.

Если id не найден, команда завершится с ошибкой без traceback:

```text
Период взаиморасчетов не найден: <id>
```

Файлы создаются в `reports/settlement_periods/<id>_<YYYY-MM-DD_HH-MM-SS>/`:
`settlement_period_report.md`, `settlement_period_dashboard.html`, `settlement_period.xlsx`,
`metadata.json`, таблицы `tables/*.csv` и графики `charts/*.png`. Если период был `reopened`, в
warnings будет пояснение, что отчет показывает сохраненный snapshot периода.

В GUI выберите строку на вкладке `Периоды взаиморасчетов`, нажмите `Создать отчет периода`, затем
используйте `Открыть HTML отчета периода`, `Открыть XLSX отчета периода` или
`Открыть папку отчета периода`.

## Close и reset-test

Close сохраняет историю и исключает покупки из текущего scope. Reset-test после backups физически
очищает `purchases.yaml` и `settlement_periods.yaml`, сохраняя participants/groups/categories.
Для обычного расчётного цикла используйте close; reset предназначен для тестовых данных.

Запись purchases и periods выполняется через storage с timestamped backup и атомарной заменой.
