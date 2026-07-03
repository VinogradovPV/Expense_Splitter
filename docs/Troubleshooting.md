# Решение проблем Expense Splitter

## PowerShell запрещает запуск скрипта

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-gui.ps1
```

Аналогично можно запускать `install.ps1` и `build-windows.ps1`. Постоянно менять системную Execution
Policy не требуется.

## GUI не запускается

Переустановите приложение и проверьте help:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1
.\.venv\Scripts\expense-splitter-gui.exe --help
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-gui.ps1 -Help
```

Если entry point отсутствует, убедитесь, что используется проектная `.venv`.

## Ошибка чтения YAML

Сообщение содержит путь проблемного файла. Сравните его с последним timestamped `.bak` и
восстановите корректный YAML вручную. Не удаляйте пользовательские данные без backup.

## HTML не открывается

Сначала создайте формат `html` или `all`. Файл `analytics_dashboard.html` должен оставаться рядом с
папками `tables/` и `charts/`; отчёт offline и использует относительные ссылки.

Для отчета текущих взаиморасчетов сначала нажмите `Создать отчет текущих взаиморасчетов` в GUI или
выполните:

```powershell
expense-splitter current-report --scope open --format all
```

HTML находится в `reports/current_state/open_<timestamp>/current_state_dashboard.html`.

В GUI и визуальных отчетах `open` отображается как `Открытые покупки`, а `snapshot` как
`Дата формирования отчета`. В CLI и `metadata.json` технические значения сохраняются намеренно.

Для отчета конкретного settlement period сначала выберите период в GUI и нажмите
`Создать отчет периода` либо выполните:

```powershell
expense-splitter settlement-period report settlement_2026_06_30_001 --format all
```

Если команда пишет `Период взаиморасчетов не найден: <id>`, проверьте id через
`expense-splitter settlement-period list`. Warning про `reopened` не является ошибкой: он означает,
что период позже переоткрывали, а отчет показывает сохраненный snapshot.

## XLSX не создаётся или восстанавливается Excel

Закройте XLSX перед повторной генерацией: открытый Excel блокирует замену файла. Новая версия
генератора не создаёт `xl/tables/*.xml`, поэтому recovery warning старых файлов устраняется после
пересоздания:

```powershell
expense-splitter analytics --period month --year 2026 --month 6 --format xlsx
```

Для текущего snapshot используйте:

```powershell
expense-splitter current-report --scope open --format xlsx
```

Файл находится в `reports/current_state/open_<timestamp>/current_state.xlsx`.

## Reset-test не выполняется

Введите точную строку `RESET_TEST_DATA`. Операция очищает только покупки и периоды после создания
backups. Для начала нового расчётного цикла без удаления истории используйте close period.

## Категория или участник не принимается

Новая категория сохраняется только после подтверждения. Неизвестные участники не создаются из
ручного поля автоматически: сначала добавьте их в справочник или исправьте имя.

Управляйте участниками и категориями на вкладке `Справочники`. Дубли без учета регистра запрещены.
Архивные участники и категории не показываются в новых покупках, но сохраняются в истории.

## Участник или категория не удаляется из справочника

Используемый участник не удаляется физически: его можно архивировать. Это сохраняет историю
покупок, settlement periods и расчеты.

Используемая категория удаляется только с typed confirm `DELETE_CATEGORY_USAGE`; после этого она
очищается из покупок. Более безопасный вариант — переименовать или архивировать категорию.

## Покупка не редактируется или не удаляется

Settled-покупки защищены. Переоткройте период либо создайте корректирующую покупку. Удаление
open-покупки требует `DELETE_PURCHASE` и создаёт backup.

## Русский текст отображается некорректно

В PowerShell включите UTF-8:

```powershell
chcp 65001
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
```

Для проверки исходников запустите `scripts/qa/check_text_encoding.py`.

## Generated artifacts

`reports/`, `.pytest_cache/`, `.ruff_cache/`, `__pycache__/`, `build/`, `dist/`, `*.egg-info/` и
`*.bak` не являются исходниками и не должны попадать в Git. Удаление `reports/` не удаляет YAML.

## Период не закрывается или не удаляется

Если GUI пишет, что период без покупок не создается обычным close flow, проверьте даты preview:
в выбранном диапазоне нет open-покупок. Скорректируйте `date_from/date_to` или сначала добавьте
покупки.

Если закрытие предлагает неожиданную дату, проверьте список периодов. Автоподстановка смотрит
только на последний содержательный `closed` period с покупками и суммой больше нуля. Пустые
тестовые и `reopened` periods намеренно игнорируются.

Непустой period удалить нельзя: это исторический snapshot. Используйте `Переоткрыть период`,
если покупки нужно вернуть в открытые расчеты, или создайте отчет периода для просмотра истории.
Пустые технические периоды удаляются только с typed confirm:

```powershell
expense-splitter settlement-period delete-empty <id> --confirm DELETE_EMPTY_PERIOD
expense-splitter settlement-period delete-empty-all --confirm DELETE_EMPTY_PERIODS
```

## PDF не создан

PDF создается нативно через ReportLab и локальный шрифт с кириллицей. Если команда сообщает, что
PDF font not found, установите Arial, Segoe UI, Tahoma, DejaVu Sans или Liberation Sans и
повторите отчет. Browser print не используется, поэтому настройки печати браузера не влияют на
layout PDF.

Если в PDF появилась пустая страница, одинокий заголовок таблицы без таблицы, служебное имя графика
вроде `spending_by_category` или отрицательная шкала у графика расходов, это дефект PDF-отчета.
Сгенерируйте отчет заново после обновления приложения и приложите проблемный PDF к issue/задаче.

Проверьте, что выбран формат `pdf` или `all`:

```powershell
expense-splitter analytics --period month --year 2026 --month 6 --format pdf
expense-splitter current-report --scope open --format pdf
expense-splitter settlement-period report <id> --format pdf
```

## PyInstaller не собирает exe

Установите dev-зависимости и запускайте сборку из корня:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-windows.ps1 -NoUpx
```

Подробности: [PACKAGING.md](PACKAGING.md).
