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

`expense-splitter current-report --scope open --format all` использует тот же набор открытых покупок, но
только строит отчет о текущем состоянии взаиморасчетов. Команда не закрывает период, не меняет
`settled` и не записывает `settlement_period_id`. Для фиксации периода используйте
`settlement-period close`.

В GUI этот режим отображается как `Открытые покупки`, а режим `all` как `Все покупки с историей`.
CLI сохраняет технические значения `open/all`, потому что они являются параметрами команд.

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

Таблица `Расходы по плательщикам` включает `Доля оплат, %`. Для settlement-period report эта доля
считается от сохраненной `total_amount` периода, поэтому reopened-период остается историческим
snapshot, а не новым пересчетом текущего `open`.

В Markdown/HTML/PDF/XLSX статус периода отображается по-русски: `closed` как `Закрыт`,
`reopened` как `Переоткрыт`. Raw `settlement_period_id` остается в metadata, CSV и деталях периода,
но основной статус покупки в GUI показывает название периода или сообщение `период не найден`.

В GUI выберите строку на вкладке `Периоды взаиморасчетов`, нажмите `Создать отчет периода`, затем
используйте `Открыть HTML отчета периода`, `Открыть XLSX отчета периода` или
`Открыть папку отчета периода`.

## Close и reset-test

Close сохраняет историю и исключает покупки из текущего scope. Reset-test после backups физически
очищает `purchases.yaml` и `settlement_periods.yaml`, сохраняя participants/groups/categories.
Для обычного расчётного цикла используйте close; reset предназначен для тестовых данных.

Запись purchases и periods выполняется через storage с timestamped backup и атомарной заменой.

## Автоподстановка следующего периода

GUI и CLI-команда `settlement-period suggest` подбирают следующий диапазон закрытия без изменения
YAML-данных. Правила:

- если есть последний содержательный `closed` period с покупками и суммой больше нуля, `date_from`
  равен следующему дню после его `date_to`, а `date_to` равен сегодняшней дате;
- пустые технические периоды и `reopened` periods не используются как граница для нового закрытия;
- если содержательных закрытых периодов нет, используется дата первой open-покупки;
- если open-покупок нет, предлагается период за сегодняшнюю дату.

Имя по умолчанию формируется как `Период с YYYY-MM-DD по YYYY-MM-DD` или
`Период за YYYY-MM-DD`. Поля остаются редактируемыми перед preview.

```powershell
expense-splitter settlement-period suggest
```

## Редактирование и удаление периодов

Содержательный закрытый или переоткрытый период хранит исторический snapshot. Для него разрешены
только безопасные metadata-изменения: `name` и `notes`. Даты, `purchase_ids`, `total_amount`,
`settlements` и `status` не редактируются напрямую; если период закрыт ошибочно, используйте
`reopen` и затем закройте новый корректный диапазон.

Пустой период определяется как запись без `purchase_ids`, с `total_amount: 0.00` и без
`settlements`. Только такие периоды можно удалить:

```powershell
expense-splitter settlement-period rename settlement_2026_06_30_001 --name "Новое имя"
expense-splitter settlement-period delete-empty settlement_2026_06_30_001 --confirm DELETE_EMPTY_PERIOD
expense-splitter settlement-period delete-empty-all --confirm DELETE_EMPTY_PERIODS
```

Перед сохранением `settlement_periods.yaml` создается backup. Удаление непустого периода
запрещено: для сохранения истории используйте reopen или исторический отчет периода.

В GUI таблица периодов по умолчанию скрывает пустые записи. Можно сменить фильтр на
`empty`, `with_purchases`, `closed`, `reopened` или `all`, отредактировать metadata выбранного
периода, удалить один пустой период или удалить все пустые тестовые периоды после typed confirm.

## PDF отчета периода

`settlement-period report <id> --format pdf` создает `settlement_period.pdf` в каталоге
`reports/settlement_periods/<id>_<timestamp>/`. Формат `all` также включает PDF.

PDF использует тот же исторический snapshot периода, что Markdown/HTML/XLSX: `purchase_ids`,
`total_amount` и `settlements` берутся из `settlement_periods.yaml`, а детали покупок догружаются
по snapshot id. Порядок покупок единый для всех форматов: сначала payer с максимальной общей
суммой, затем покупки этого payer по сумме убыванию.
Денежные значения в PDF всегда отображаются с двумя знаками после запятой (например,
`1 567,28`), с той же точностью, что XLSX; расчетная логика и snapshot периода не меняются.
