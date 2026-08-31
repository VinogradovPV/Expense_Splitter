# TG-PREP.3 — Server Readiness Audit

Дата: 2026-07-01
Ветка: `cloud/telegram-prep`
Статус: initial audit; код не менялся, Telegram-бот и cloud resources не добавлялись.

## Цель

Понять, какие части Expense Splitter можно переиспользовать в серверном контуре Telegram/Yandex
Cloud, а какие завязаны на локальный YAML, filesystem, CLI или Tkinter GUI.

## Выполненные проверки

Команды поиска:

```powershell
rg "Path\(|open\(|read_text|write_text|mkdir|reports|data_dir|load_purchases|save_purchases" src tests
rg "typer|messagebox|tkinter|click|Console|Table" src/expense_splitter
rg "calculate_balances|calculate_settlements|generate_current_report|generate_analytics|settlement-period" src tests
```

Дополнительно просмотрены:

- `src/expense_splitter/models.py`
- `src/expense_splitter/calculator.py`
- `src/expense_splitter/settlement.py`
- `src/expense_splitter/settlement_periods.py`
- `src/expense_splitter/analytics.py`
- `src/expense_splitter/current_report.py`
- `src/expense_splitter/settlement_period_report.py`
- `src/expense_splitter/report_pdf.py`
- `src/expense_splitter/analytics_xlsx.py`
- `src/expense_splitter/storage.py`
- `src/expense_splitter/cli.py`
- `src/expense_splitter/gui/`

## Pure Domain Modules

### `models.py`

Готовность к серверу: высокая, но с важным ограничением по identity.

Модели `Participant`, `Group`, `CategoryEntry`, `Purchase`, `Balance`, `Settlement`,
`SettlementPeriod` являются dataclass-структурами без прямой зависимости от filesystem, Typer или
Tkinter. Их можно переиспользовать в backend/service layer.

Ограничения:

- `Participant` идентифицируется `name`, а не стабильным `participant_id`.
- `Group.members`, `Purchase.payer`, `Purchase.participants`, `Balance.participant`,
  `Settlement.from_participant` и `Settlement.to_participant` используют display-name.
- `Purchase.id` есть, но формат и генерация живут выше по стеку, не в модели.
- `SettlementPeriod.purchase_ids` уже лучше подходит для server snapshot, но settlements внутри
  периода все еще хранят имена участников.

Вывод: модели можно оставить как DTO/domain baseline для offline mode, но перед cloud mode нужен
план stable IDs и миграции display-name references.

### `calculator.py`

Готовность к серверу: высокая.

`calculate_balances(purchases, all_participants)` не читает и не пишет файлы. Расчет работает на
`Purchase` и списке участников, использует `Decimal`, валидирует наличие payer/participants и
возвращает `Balance`.

Ограничения:

- Валидация завязана на имена участников.
- Fair rounding policy реализована как "последний участник получает остаток". Для server/API это
  нужно явно задокументировать или заменить согласованной политикой.

### `settlement.py`

Готовность к серверу: высокая.

`calculate_settlements(balances)` является чистым greedy minimizer: принимает `Balance`, возвращает
`Settlement`, не зависит от storage/interface/reporting.

Ограничения:

- Результат зависит от имен участников.
- При равных суммах порядок может зависеть от входного порядка balances; для API желательно
  зафиксировать deterministic ordering policy.

### `analytics.py`

Готовность к серверу: высокая для dataset/aggregation слоя.

`parse_period`, `filter_purchases_by_period`, `build_analytics_dataset`,
`aggregate_summary`, `aggregate_by_category`, `aggregate_by_payer`,
`aggregate_by_participant`, `build_top_purchases`, `build_warnings` работают с объектами и
коллекциями, а не с файлами. Их можно вызывать из backend, если данные уже загружены из repository.

Ограничения:

- Dataset использует participant display names.
- Периоды аналитики date-based, не multi-tenant aware.
- Warnings ориентированы на отчетный UX, но пригодны как service-level diagnostics.

### `settlement_periods.py`

Готовность к серверу: средняя-высокая для доменной логики, но требует transaction boundary.

Чистые или почти чистые функции:

- `parse_period_date`
- `validate_date_range`
- `default_period_name`
- `suggest_next_settlement_period`
- `filter_purchases_by_settlement_scope`
- `select_open_purchases_for_period`
- `preview_settlement_period`
- `generate_settlement_period_id`
- `get_settlement_period`
- `close_settlement_period`
- `reopen_settlement_period`
- `update_settlement_period_metadata`
- `delete_empty_settlement_period`
- `delete_empty_settlement_periods`

Модуль не пишет файлы сам, но `close_settlement_period` и `reopen_settlement_period` мутируют списки
`purchases` и `periods`. В CLI/GUI это затем сохраняется в YAML.

Серверный риск:

- Close/reopen должен стать transactional unit of work: изменить purchases и periods атомарно.
- `generate_settlement_period_id` основан на текущем списке периодов и счетчике; в конкурентном
  backend нужна уникальность на уровне БД или lock.
- `created_by` сейчас строка (`cli`/`gui`), в cloud нужен actor/user id.

## Filesystem-Bound Modules

### `storage.py`

Готовность к серверу: низкая как backend storage, высокая как offline repository adapter.

Модуль напрямую завязан на:

- `Path`
- YAML (`yaml.safe_load`, `yaml.dump`)
- локальные файлы `participants.yaml`, `purchases.yaml`, `settlement_periods.yaml`,
  `categories.yaml`
- локальные backup-файлы `*.bak`
- `tempfile.NamedTemporaryFile`, `os.replace`, `shutil.copy2`

Сильные стороны для offline mode:

- Явный UTF-8.
- Friendly `StorageError`.
- Atomic-ish write через temp file + `os.replace`.
- Backup перед перезаписью.

Ограничения для cloud:

- Single-user filesystem storage; нет транзакций между несколькими YAML файлами.
- Нет optimistic locking/version checks.
- Backup logic локальная и не подходит напрямую для Object Storage/DB.
- Нет tenant/user isolation.

Рекомендация: оставить как `YamlExpenseRepository` для desktop/offline mode, но выделить
интерфейс repository до добавления Telegram/API.

### Report output paths

Локальная запись отчетов находится в:

- `current_report.py`: default `Path("reports/current_state")`
- `settlement_period_report.py`: default `Path("reports/settlement_periods")`
- `analytics_reporting.py`: default `Path("reports/analytics")`
- `report_pdf.py`: пишет PDF в `output_path`
- `analytics_xlsx.py`: читает CSV tables и пишет XLSX

Эти модули создают `tables/`, `charts/`, metadata/json, HTML/Markdown/PDF/XLSX и используют
`mkdir`, `write_text`, `path.open`.

Вывод: report writers не являются server-pure. Но их можно запускать в backend worker с temp dir, а
готовые файлы затем загружать в Object Storage.

## Interface-Bound Modules

### `cli.py`

Готовность к серверу: низкая как reusable service, хорошая как current adapter.

CLI завязан на:

- Typer (`typer.Option`, `typer.Argument`, `typer.Exit`)
- Rich (`Console`, `Table`)
- `Path("data")`, `Path("reports/...")`
- прямые вызовы `load_*`/`save_*`

В CLI есть orchestration/business workflow:

- add/list purchases
- balances/settle
- settlement-period preview/close/list/show/reopen/report
- analytics/current-report generation

Риск: часть use-case логики сейчас живет в CLI, например загрузить YAML, выбрать scope, посчитать,
сохранить. Для server/API это нужно вынести в service layer, а CLI оставить тонким adapter.

### `src/expense_splitter/gui/`

Готовность к серверу: низкая как reusable backend, но `gui/actions.py` полезен как карта use cases.

GUI завязан на:

- Tkinter (`tkinter`, `ttk`, `messagebox`, `simpledialog`)
- локальные `GuiState.data_dir`, `reports_dir`, `analytics_dir`, `current_state_dir`
- `subprocess.Popen` для открытия файлов/папок
- локальные backup operations

`gui/actions.py` содержит много orchestration logic:

- CRUD purchases
- CRUD participants/categories
- settlement periods close/reopen/delete empty
- report generation
- opening report files
- backup data

Риск: GUI actions смешивают storage, domain logic и desktop behavior. Для Telegram/API нужно
перенести reusable use cases в сервисы, а GUI оставить consumer-ом этих сервисов.

### PowerShell wrappers / launcher

`launcher.py` и scripts запускают локальный CLI/GUI сценарий и не должны попадать в server core.
Они пригодны только как local desktop entry points.

## Report-Generation Modules

### Что можно вызывать из backend

Можно переиспользовать dataset builders, если входные данные уже получены из repository:

- `analytics.build_analytics_dataset`
- `current_report.build_current_report_dataset`
- `settlement_period_report.build_settlement_period_report_dataset`
- analytics aggregation helpers
- charts/table/PDF/XLSX writers при наличии temp output dir

Сильный плюс: current-report и settlement-period report уже разделяют "build dataset" и "write
formats" лучше, чем ранний CLI-код.

### Что нужно адаптировать

- Output должен идти в temp dir/job workspace, затем в Object Storage.
- Metadata должен возвращать storage keys/URLs, а не только local paths.
- HTML сейчас offline и с локальными ссылками на PNG/CSV. Для Telegram/backend нужен delivery
  contract: zip bundle, signed URLs или attachment list.
- XLSX/PDF читают CSV/PNG из локальной структуры. Это можно сохранить как internal build
  directory, но публичный contract не должен требовать локальную папку `reports/`.
- `report_pdf.py` ищет системные шрифты на runner/host. Для Yandex Cloud нужно упаковать или
  явно установить кириллический font asset.

## Main Risks Before Telegram/Yandex Cloud

1. **Display names вместо stable IDs.**
   Участники, группы, покупки, балансы и переводы завязаны на имена. Rename сейчас переписывает
   YAML-ссылки. В multi-user cloud это риск потери связности и audit trail.

2. **YAML как single-user хранилище.**
   YAML подходит для desktop/offline mode, но не для конкурентных записей Telegram users. Нужен DB
   repository с transaction boundaries.

3. **Отчеты пишутся в локальную папку.**
   Current reports используют `reports/...`, `tables/`, `charts/`. Для backend нужен temp dir +
   Object Storage/upload contract.

4. **GUI/CLI содержат use-case orchestration.**
   Добавление покупки, закрытие периода, reopen, directory management и report generation должны
   стать сервисами, чтобы GUI/CLI/Telegram/API не дублировали бизнес-логику.

5. **Close/reopen periods требуют атомарности.**
   Сейчас CLI/GUI загружают purchases/periods, вызывают domain mutation, затем сохраняют два YAML
   файла. Для cloud это должен быть один transaction.

6. **Report PDF font dependency.**
   PDF требует кириллический шрифт на host. В serverless/container контуре это надо закрепить как
   packaged asset или image dependency.

7. **Local file opening behavior.**
   `subprocess.Popen(["open"|"xdg-open"])` и Windows open logic являются desktop-only и не должны
   попасть в backend path.

## Recommended Next Refactoring Boundary

Перед Telegram bot стоит выделить service/repository слой без большого переписывания:

1. `ExpenseRepository` protocol:
   - load/save participants;
   - load/save groups;
   - load/save categories;
   - load/save purchases;
   - load/save settlement periods;
   - optional transaction/unit-of-work API.

2. `YamlExpenseRepository`:
   - тонкая обертка над текущим `storage.py`;
   - сохраняет offline desktop behavior.

3. Use-case services:
   - `PurchaseService`;
   - `DirectoryService`;
   - `SettlementPeriodService`;
   - `ReportService`.

4. Interface adapters:
   - CLI вызывает services;
   - GUI вызывает services;
   - будущий Telegram/API вызывает те же services.

5. Report delivery abstraction:
   - `ReportBuildResult` с файлами, metadata и warnings;
   - local filesystem adapter для desktop;
   - Object Storage adapter для cloud.

## Server Reuse Summary

| Area | Server readiness | Notes |
|---|---:|---|
| Models | Medium-high | Pure dataclasses, but display-name identity |
| Balance calculation | High | Pure, reusable |
| Settlement minimizer | High | Pure, reusable |
| Analytics aggregations | High | Pure after repository load |
| Settlement period domain | Medium-high | Reusable, but mutation needs transaction boundary |
| YAML storage | Low for cloud | Keep as offline repository adapter |
| Current/settlement/analytics reports | Medium | Build in temp dir, upload artifacts |
| PDF/XLSX writers | Medium | Need packaged fonts and temp artifact strategy |
| CLI | Low as backend | Keep as adapter after service extraction |
| GUI | Low as backend | Keep as adapter after service extraction |

## Decision

Текущий проект уже имеет переиспользуемое расчетное ядро. Главная подготовка перед Telegram/Yandex
Cloud — не писать bot напрямую, а сначала отделить use-case services от YAML/Tkinter/Typer
adapters и ввести stable ID/data model plan.
