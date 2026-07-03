# Expense Splitter

## Что это

Expense Splitter — локальное приложение для учёта совместных покупок, расчёта долгов, закрытия
периодов взаиморасчётов и формирования аналитических отчётов. Основной интерфейс — desktop GUI на
`tkinter`; CLI доступен для автоматизации и продвинутых сценариев.

Приложение работает с локальными YAML-файлами, не требует web-server и создаёт offline HTML/XLSX.

## Основные возможности

- добавление, редактирование и защищённое удаление открытых покупок;
- участники и категории через checklist, ComboBox или ручной ввод;
- управление справочниками участников и категорий из GUI без ручного редактирования YAML;
- фильтры по статусу, категории, датам и названию, сортировка таблицы;
- расчёты в scope `open` или по всей истории `all`;
- закрытие и переоткрытие периодов без удаления истории;
- аналитика в Markdown, CSV, PNG, offline HTML и XLSX;
- исторический отчет по конкретному settlement period snapshot;
- безопасные backups и reset-test с typed confirmation;
- Windows standalone executables через PyInstaller.

## Быстрый старт Windows

Требуется Python 3.11+.

```powershell
cd C:\path\to\expense_splitter
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-gui.ps1
```

Для разработки:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1 -Dev
```

## Запуск Desktop GUI

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-gui.ps1
```

Или после установки:

```powershell
expense-splitter-gui
```

GUI содержит вкладки `Покупки`, `Текущие расчёты`, `Периоды взаиморасчётов`, `Аналитика и отчёты`,
`Справочники`, `Данные и обслуживание`, `Справка`. Консольное меню для GUI не требуется.

## Пользовательские термины

GUI и визуальные отчеты используют русские подписи: `open` отображается как `Открытые покупки`,
`all` как `Все покупки с историей`, `snapshot` как `Дата формирования отчета`, а статусы периодов
`closed/reopened` как `Закрыт/Переоткрыт`. CLI-параметры и `metadata.json` сохраняют технические
значения `open/all/closed/reopened`, потому что они нужны для совместимости и автоматизации.
Raw `settlement_period_id` показывается в деталях или служебной информации, но не как основной
статус покупки.

## Первый сценарий

1. Инициализируйте данные командой `expense-splitter init` либо запустите GUI — недостающие файлы
   будут созданы автоматически.
2. На вкладке `Покупки` нажмите `Добавить покупку`, заполните сумму, плательщика, участников,
   категорию и дату.
3. Для исправления выберите строку и нажмите `Редактировать покупку`. Закрытые покупки защищены.
4. На вкладке `Справочники` можно добавить, переименовать, архивировать или удалить неиспользуемых
   участников и категории. Переименование каскадно обновляет покупки.
5. Откройте `Текущие расчёты`: режим `Открытые покупки` показывает балансы и необходимые переводы
   только по незакрытым покупкам.
6. На вкладке периодов выполните preview и нажмите `Закрыть период и обнулить текущие
   взаиморасчёты`. Покупки останутся в истории.
7. Для исторического snapshot выберите период и нажмите `Создать отчет периода`, затем откройте
   HTML, XLSX или папку отчета.
8. В разделе аналитики выберите месяц, квартал или год, формат `all`, затем откройте HTML/XLSX или
   папку отчёта.

## Данные и безопасность

По умолчанию данные находятся в `data/`:

- `purchases.yaml` — покупки schema v2;
- `participants.yaml` — участники и группы;
- `categories.yaml` — категории;
- `settlement_periods.yaml` — закрытые и переоткрытые периоды.

Перед перезаписью YAML storage создаёт timestamped `.bak` и выполняет атомарную замену файла.
Кнопка `Создать backup данных` копирует все YAML в отдельную папку `data/backups/<timestamp>/`.

`Сбросить тестовые данные` требует `RESET_TEST_DATA`, очищает только покупки и периоды, сохраняя
участников, группы и категории. Удаление открытой покупки требует `DELETE_PURCHASE`; settled-покупки
удалить нельзя.

Участники и категории имеют статус `active` или `archived`. Архивные значения не предлагаются в
новых покупках, но остаются в истории. Используемого участника нельзя физически удалить; сначала
нужно переоткрыть/исправить данные или архивировать участника. Используемую категорию можно удалить
только с typed confirm `DELETE_CATEGORY_USAGE`, при этом она очищается из покупок.

## Периоды взаиморасчётов

Close period не удаляет покупки: они получают `settled: true` и `settlement_period_id` и перестают
участвовать в scope `open`. Reopen возвращает покупки периода в текущие расчёты.

- `open` — только незакрытые покупки;
- `all` — вся история;
- конкретный `settlement_period_id` — snapshot выбранного периода.

Reset-test отличается от close: reset физически очищает тестовые покупки и список периодов после
backup, а close сохраняет историю.

## Аналитика

```powershell
expense-splitter analytics --period month --year 2026 --month 6 --format all
expense-splitter analytics --period quarter --year 2026 --quarter 2 --format all
expense-splitter analytics --period year --year 2026 --format all
```

## Отчет по текущим взаиморасчетам

Текущий отчет отличается от analytics month/quarter/year: это snapshot текущего scope, а не
календарная аналитика. По умолчанию используется `open`, поэтому закрытые покупки не входят в
отчет. Команда ничего не закрывает, не создает settlement period и не меняет YAML-данные.

```powershell
expense-splitter current-report --scope open --format all
expense-splitter current-report --scope all --format html
```

Результаты сохраняются в `reports/current_state/open_<YYYY-MM-DD_HH-MM-SS>/` или
`reports/current_state/all_<YYYY-MM-DD_HH-MM-SS>/`. Полный формат `all` создает
`current_state_report.md`, `current_state_dashboard.html`, `current_state.xlsx`,
`metadata.json`, CSV-таблицы в `tables/` и PNG-графики в `charts/`. Закрытие периода выполняется
отдельной кнопкой или командой `settlement-period close`.

В таблице `Расходы по плательщикам` во всех форматах выводится `Доля оплат, %`: доля суммы,
оплаченной конкретным плательщиком, от общей суммы отчета.

## Отчет по settlement period

Отчет по settlement period отличается от analytics и current-report: это исторический snapshot
конкретного закрытого или переоткрытого периода. Источником истины служит запись в
`settlement_periods.yaml`: `purchase_ids`, `total_amount`, `settlements`, даты и статус. Детали
покупок догружаются из текущего `purchases.yaml` по snapshot id; если запись покупки отсутствует,
отчет не падает и пишет warning. Команда не меняет YAML-данные.

```powershell
expense-splitter settlement-period report settlement_2026_06_30_001 --format all
```

Результаты сохраняются в
`reports/settlement_periods/<settlement_period_id>_<YYYY-MM-DD_HH-MM-SS>/`: Markdown, offline HTML,
XLSX, `metadata.json`, CSV-таблицы в `tables/` и PNG-графики в `charts/`. Warning для `reopened`
означает, что период уже возвращали в открытые расчеты, а отчет показывает сохраненный snapshot
периода.

Таблица `Расходы по плательщикам` также содержит `Доля оплат, %`; значение рассчитывается от
snapshot `total_amount` периода и не меняет сохраненные переводы.

Форматы:

- `markdown` — `analytics_report.md`;
- `csv` — таблицы в `tables/`;
- `png` — графики в `charts/`;
- `html` — offline `analytics_dashboard.html` с embedded CSS и локальными PNG;
- `xlsx` — `expense_analytics_<period-id>.xlsx` с таблицами и PNG;
- `all` — полный комплект плюс `metadata.json`.

Результаты сохраняются в `reports/analytics/<year>/<period-id>/` и не коммитятся.

## CLI для продвинутых пользователей

```powershell
expense-splitter --help
expense-splitter init
expense-splitter add-purchase --help
expense-splitter list-purchases
expense-splitter balances --scope open
expense-splitter settle --scope open
expense-splitter settlement-period --help
expense-splitter analytics --help
```

Полный набор параметров показывается через `--help` соответствующей команды.

## Установка и PowerShell-скрипты

```powershell
.\scripts\install.ps1
.\scripts\install.ps1 -Dev
.\scripts\run-gui.ps1
.\scripts\run-gui.ps1 -Help
.\scripts\run-cli.ps1 --help
.\scripts\run-launcher.ps1 --help
```

При ограниченной Execution Policy используйте
`powershell -NoProfile -ExecutionPolicy Bypass -File <script>`. Аналоги для Unix находятся в
`scripts/*.sh`.

## Сборка standalone

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-windows.ps1 -NoUpx
```

Ожидаются:

- `dist/expense-splitter.exe` — CLI;
- `dist/expense-splitter-launcher.exe` — console launcher;
- `dist/expense-splitter-gui.exe` — desktop GUI без консольного окна (`console=False`).

`build/` и `dist/` являются generated artifacts. Подробнее: [docs/PACKAGING.md](docs/PACKAGING.md).

## Troubleshooting

Решения для Execution Policy, запуска GUI, HTML/XLSX, reset-test, категорий, UTF-8 и generated
artifacts собраны в [docs/Troubleshooting.md](docs/Troubleshooting.md).

## Документация

- [Руководство пользователя](docs/USER_GUIDE.md)
- [Аналитика](docs/ANALYTICS.md)
- [Периоды взаиморасчётов](docs/SETTLEMENT_PERIODS.md)
- [Схема данных](docs/DATA_SCHEMA.md)
- [Упаковка и standalone](docs/PACKAGING.md)
- [История production-ready этапов](docs/reports/prod_ready_progress_report.md)

## Development

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
.\.venv\Scripts\python.exe -m ruff check src tests
```

Перед commit проверяйте `git status --short --ignored`; не добавляйте `.venv/`, caches, `reports/`,
`build/`, `dist/`, `*.egg-info/` и `*.bak`.

## Settlement period UX

Вкладка `Периоды взаиморасчетов` автоматически предлагает следующий период закрытия. Если есть
последний содержательный закрытый период, новый диапазон начинается на следующий день после него.
Пустые и `reopened` периоды не используются как граница; если содержательных закрытий еще нет,
берется дата первой открытой покупки, а при отсутствии покупок - сегодняшняя дата.

Обычный close flow не создает нулевые периоды без покупок. Закрытый период с покупками можно
безопасно переименовать и дополнить notes, но его даты, покупки, сумма и snapshot переводов не
меняются. Пустые тестовые периоды можно удалить только через typed confirm
`DELETE_EMPTY_PERIOD` или массово через `DELETE_EMPTY_PERIODS`.

CLI-команды для этих сценариев:

```powershell
expense-splitter settlement-period suggest
expense-splitter settlement-period rename settlement_2026_06_30_001 --name "Июнь"
expense-splitter settlement-period delete-empty settlement_2026_06_30_001 --confirm DELETE_EMPTY_PERIOD
expense-splitter settlement-period delete-empty-all --confirm DELETE_EMPTY_PERIODS
```

## Native PDF reports

Reports support native PDF generation through ReportLab. PDF is not produced through browser
printing, Playwright, Selenium, wkhtmltopdf, WeasyPrint, Excel COM, or external web services.
The generator discovers a local Cyrillic-capable font such as Arial, Segoe UI, Tahoma,
DejaVu Sans, or Liberation Sans; if no such font is available, install one and rerun the report.

PDF is available for:

- analytics: `expense_analytics_<period-id>.pdf`;
- current-report: `current_state.pdf`;
- settlement-period report: `settlement_period.pdf`.

Use `--format pdf` to create only PDF or `--format all` to include PDF with the existing
Markdown, CSV, PNG, HTML and XLSX outputs.

PDF reports keep table section headings with the table header and first data row, so a heading
does not remain alone at the bottom of a page. Empty PDF pages are treated as a report defect.
Visual report labels are user-facing Russian text: internal chart keys stay in filenames and
metadata, expense charts start from zero, and the balance table explains the sign of the final
balance.

Purchase tables in all report formats use the same business sorting: payers are ordered by
`payer_total` descending, then payer name ascending. Purchases inside each payer are ordered by
amount descending, date descending, purchase name ascending and id ascending. CSV purchases tables
include machine-readable `payer_total` and `payer_rank` columns.

## Roadmap

- Release dry-run notes: [v0.1.1 release notes](docs/releases/RELEASE_NOTES_v0.1.1.md)
  and [v0.1.1 checklist](docs/releases/RELEASE_CHECKLIST_v0.1.1.md).
- P2.REL.1 — release quality gate и проверка standalone-сборки;
- release tag и публикация проверенных Windows artifacts;
- дальнейшие улучшения UX без изменения стабильного расчётного ядра.
