# Expense Splitter

## Что это

Expense Splitter — локальное приложение для учёта совместных покупок, расчёта долгов, закрытия
периодов взаиморасчётов и формирования аналитических отчётов. Основной интерфейс — desktop GUI на
`tkinter`; CLI доступен для автоматизации и продвинутых сценариев.

Приложение работает с локальными YAML-файлами, не требует web-server и создаёт offline HTML/XLSX.

## Основные возможности

- добавление, редактирование и защищённое удаление открытых покупок;
- участники и категории через checklist, ComboBox или ручной ввод;
- фильтры по статусу, категории, датам и названию, сортировка таблицы;
- расчёты в scope `open` или по всей истории `all`;
- закрытие и переоткрытие периодов без удаления истории;
- аналитика в Markdown, CSV, PNG, offline HTML и XLSX;
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
`Данные и обслуживание`, `Справка`. Консольное меню для GUI не требуется.

## Первый сценарий

1. Инициализируйте данные командой `expense-splitter init` либо запустите GUI — недостающие файлы
   будут созданы автоматически.
2. На вкладке `Покупки` нажмите `Добавить покупку`, заполните сумму, плательщика, участников,
   категорию и дату.
3. Для исправления выберите строку и нажмите `Редактировать покупку`. Закрытые покупки защищены.
4. Откройте `Текущие расчёты`: scope `open` показывает балансы и необходимые переводы только по
   незакрытым покупкам.
5. На вкладке периодов выполните preview и нажмите `Закрыть период и обнулить текущие
   взаиморасчёты`. Покупки останутся в истории.
6. В разделе аналитики выберите месяц, квартал или год, формат `all`, затем откройте HTML/XLSX или
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

## Roadmap

- P2.REL.1 — release quality gate и проверка standalone-сборки;
- release tag и публикация проверенных Windows artifacts;
- дальнейшие улучшения UX без изменения стабильного расчётного ядра.
