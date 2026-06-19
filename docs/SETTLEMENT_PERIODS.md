# Периоды взаиморасчетов

Период взаиморасчетов позволяет закрыть выбранные покупки без удаления истории. В пользовательском смысле это безопасное "обнуление расчетов": покупки остаются в `data/purchases.yaml`, но помечаются как закрытые и больше не участвуют в текущих `balances` и `settle` по умолчанию.

## Основной сценарий

1. Посмотреть предварительный расчет:

```powershell
expense-splitter settlement-period preview --from 2026-06-01 --to 2026-06-19
```

2. Закрыть период с явным подтверждением:

```powershell
expense-splitter settlement-period close --from 2026-06-01 --to 2026-06-19 --name "Июнь до 19.06" --confirm CLOSE_PERIOD
```

3. Посмотреть закрытые периоды:

```powershell
expense-splitter settlement-period list
expense-splitter settlement-period show settlement_2026_06_19_001
```

4. Вернуть покупки периода в текущий расчет, если закрытие нужно отменить:

```powershell
expense-splitter settlement-period reopen settlement_2026_06_19_001 --confirm REOPEN_PERIOD
```

## Scope для текущих расчетов

По умолчанию `balances` и `settle` считают только открытые покупки:

```powershell
expense-splitter balances --scope open
expense-splitter settle --scope open
```

Старое полное поведение доступно через `--scope all`:

```powershell
expense-splitter balances --scope all
expense-splitter settle --scope all
```

Чтобы пересмотреть snapshot конкретного закрытого периода:

```powershell
expense-splitter balances --settlement-period settlement_2026_06_19_001
expense-splitter settle --settlement-period settlement_2026_06_19_001
```

## Данные и безопасность

- `data/settlement_periods.yaml` хранит список закрытых периодов, даты, выбранные покупки, итоговую сумму и snapshot переводов.
- `data/purchases.yaml` хранит покупки как раньше, но у закрытых покупок появляются поля `settled: true` и `settlement_period_id`.
- Старые покупки без этих полей считаются открытыми.
- Закрытие периода не удаляет покупки и не архивирует их физически.
- Запись идет через существующий storage-layer: перед перезаписью создается `.bak`, а сам файл заменяется атомарно.
- `preview` не меняет YAML-файлы.
- `close` требует `--confirm CLOSE_PERIOD`.
- `reopen` требует `--confirm REOPEN_PERIOD`.

## Отличие от сброса тестовых данных

Закрытие периода сохраняет все покупки: оно помечает их закрытыми и исключает из open scope.
Кнопка GUI `Сбросить тестовые данные` предназначена для тестовой локальной базы и после typed
confirm `RESET_TEST_DATA` физически очищает покупки и периоды. Перед reset создаются `.bak`;
участники, группы и категории не удаляются. Для обычного завершения расчетного цикла используйте
закрытие периода, а не reset-test.
