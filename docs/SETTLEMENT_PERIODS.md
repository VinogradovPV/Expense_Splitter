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

## Close и reset-test

Close сохраняет историю и исключает покупки из текущего scope. Reset-test после backups физически
очищает `purchases.yaml` и `settlement_periods.yaml`, сохраняя participants/groups/categories.
Для обычного расчётного цикла используйте close; reset предназначен для тестовых данных.

Запись purchases и periods выполняется через storage с timestamped backup и атомарной заменой.
