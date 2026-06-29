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

## PyInstaller не собирает exe

Установите dev-зависимости и запускайте сборку из корня:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-windows.ps1 -NoUpx
```

Подробности: [PACKAGING.md](PACKAGING.md).
