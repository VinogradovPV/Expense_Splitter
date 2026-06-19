# Expense Splitter: системный промпт P2 GUI usability v3
## Desktop GUI launcher, редактирование покупок, категории, reset тестовых данных

Дата актуализации: 2026-06-19.

## 1. Текущий статус проекта

Фактический статус проекта:

```text
P0 baseline: completed, pushed, CI success.
P1.0 schema v2 + purchase_name: completed, pushed, CI success.
P1.A analytics Markdown + CSV + PNG: completed, pushed, CI success.
P2.S.1 settlement periods foundation: completed, pushed, CI success.
P2.GUI.1 desktop GUI launcher foundation: implemented locally; commit/push may be pending if checks were blocked by outside-sandbox approval limit.
```

P2.GUI.1 уже добавил desktop GUI launcher на `tkinter`, entry point `expense-splitter-gui`, wrapper `scripts/run-gui.ps1`, пакет `src/expense_splitter/gui/`, PyInstaller target `expense-splitter-gui` с `console=False`, smoke tests и документацию.

Новый этап является доработкой UX поверх P2.GUI.1. Не переписывай GUI с нуля и не меняй settlement core без необходимости.

## 2. Главная цель этапа

Сделать desktop GUI launcher пригодным для реального ручного ввода данных:

1. Добавить редактирование покупки.
2. Сделать выбор участников удобным: checklist/multi-select плюс возможность ручного ввода.
3. Сделать выбор категории удобным: предустановленные категории, выпадающий список, возможность добавить новую категорию вручную.
4. Показывать категорию в главной таблице покупок.
5. Добавить безопасный сброс тестовых данных, внесенных в локальную базу.
6. Сохранить CLI, console launcher, analytics, settlement periods и существующие тесты.

## 3. Жесткие правила Git/GitHub

Все команды `git` и `gh` выполнять только outside sandbox из корня проекта:

```powershell
cd C:\Users\Rockaudit\LLM_CHAT\expense_splitter
```

Запрещено:

```text
- git reset --hard;
- git clean -fd;
- force push;
- rebase shared branch без отдельного разрешения;
- удаление пользовательских YAML без backup и typed confirm;
- коммит generated artifacts.
```

Перед каждым commit:

```powershell
git status --short --ignored
git diff --name-only
git diff --cached --name-only
```

Проверить, что в staged нет:

```text
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
dist/
build/
*.egg-info/
reports/
.tmp/
*.bak
*.tmp
*.part
*.crdownload
```

После push:

```powershell
gh run list --limit 5
gh run view <run-id> --log
```

Если GitHub Actions упал, не считать этап завершенным, пока failure не исправлен или явно не deferred с причиной.

## 4. Outside-sandbox разрешения

Следующие команды разрешено сразу выполнять outside sandbox, без первой попытки внутри sandbox, потому что ранее уже были стабильные проблемы с Windows Temp, pytest, pip, PowerShell ExecutionPolicy, PyInstaller и GUI runtime:

```text
- python -m pip install ...
- python -m pytest ...
- python -m compileall ...
- python scripts/qa/check_text_encoding.py
- .venv\Scripts\*.exe
- dist\*.exe
- powershell -NoProfile -ExecutionPolicy Bypass -File ...
- PyInstaller build commands
- tkinter GUI smoke/manual launch
- git and gh commands
```

Для PowerShell проверок использовать UTF-8 prelude:

```powershell
chcp 65001
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
```

## 5. UTF-8 и mojibake policy

Все новые и измененные текстовые файлы сохранять в UTF-8.

Обязательная проверка:

```powershell
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
```

Запрещены признаки mojibake в обычных исходниках и документации:

```text
Рџ
Рђ
Ð
Ñ
╨
╤
�
```

Если такие строки нужны в allow-list теста, явно добавлять исключение в `scripts/qa/check_text_encoding.py` и пояснять причину в progress report.

## 6. Архитектурные принципы GUI

GUI должен быть thin layer:

```text
GUI widgets/dialogs -> gui/actions.py -> domain/storage/analytics/settlement modules
```

Запрещено дублировать расчетную логику внутри tkinter callback-ов.

Рекомендованная структура:

```text
src/expense_splitter/gui/
├── __init__.py
├── app.py
├── actions.py
├── state.py
├── dialogs.py
├── widgets.py
└── categories.py  # опционально, если нужен GUI-specific helper
```

## 7. Доработка покупок

### 7.1. Главная таблица покупок

В таблице на вкладке `Покупки` должны отображаться минимум:

```text
Дата
Покупка
Сумма
Плательщик
Участники
Категория
Статус
```

Сейчас категория вводится в форме, но не отображается в главной таблице. Это дефект UX и должен быть исправлен.

### 7.2. Редактирование покупки

Добавить кнопку:

```text
Редактировать покупку
```

Поведение:

1. Кнопка активна, если выбрана строка покупки.
2. Открывается диалог редактирования с текущими значениями:
   - наименование покупки;
   - сумма;
   - плательщик;
   - участники;
   - дата;
   - категория;
   - комментарий.
3. После сохранения выполняется валидация.
4. Данные записываются через существующий storage layer с atomic write/backup.
5. Таблица обновляется.
6. Ошибки показываются через GUI messagebox без traceback.

Если покупка уже закрыта в settlement period (`settled=True` или есть `settlement_period_id`), редактирование по умолчанию блокируется. Сообщение:

```text
Покупка относится к закрытому периоду взаиморасчетов. Сначала переоткройте период или создайте корректирующую покупку.
```

Не разрешать незаметное редактирование закрытых покупок, потому что это ломает историю взаиморасчетов.

## 8. Участники: checklist + ручной ввод

Для поля участников в формах добавления/редактирования покупки реализовать удобный выбор:

1. Кнопка или выпадающий контрол `Выбрать участников`.
2. Открывается модальное окно со списком известных участников и checkbox для каждого.
3. Есть действия:
   - выбрать всех;
   - снять всех;
   - применить;
   - отмена.
4. Оставить ручной ввод через строку через запятую:

```text
Павел, Сергей, Владимир
```

5. Если пользователь вручную ввел нового участника, которого нет в справочнике, поведение должно быть безопасным:
   - показать предупреждение;
   - предложить добавить участника в справочник;
   - либо разрешить как разовый участник, если это уже поддержано доменной моделью.

Предпочтение: не создавать новых участников молча.

## 9. Категории: предустановленные + пользовательские

### 9.1. Предустановленные категории

Минимальный список:

```text
кофе
еда
безалкогольные напитки
алкоголь
техника
аксессуары
```

Дополнительно добавить рекомендуемые категории:

```text
продукты
транспорт
доставка
хозтовары
аптека и здоровье
развлечения
подарки
прочее
без категории
```

Категории должны отображаться по-русски, в UTF-8, без mojibake.

### 9.2. Хранение категорий

Реализовать persistent categories storage. Рекомендуемый файл:

```text
data/categories.yaml
```

Рекомендуемая структура:

```yaml
schema_version: 1
categories:
  - кофе
  - еда
  - безалкогольные напитки
  - алкоголь
  - техника
  - аксессуары
  - продукты
  - транспорт
  - доставка
  - хозтовары
  - связь и интернет
  - подписки
  - аренда и жилье
  - коммунальные услуги
  - аптека и здоровье
  - развлечения
  - подарки
  - прочее
  - без категории
```

Если `categories.yaml` отсутствует, приложение должно использовать default categories из `defaults.py` и создать файл при `init` или при первом сохранении новой категории.

Новые категории, введенные пользователем в GUI, должны добавляться в справочник только после подтверждения.

### 9.3. UI категории

Для категории в диалоге покупки использовать:

```text
ComboBox / выпадающий список + возможность ручного ввода
```

Если tkinter `ttk.Combobox` используется с `state="normal"`, пользователь может выбрать категорию из списка или ввести новую вручную.

При новой категории:

```text
Категория "..." отсутствует в справочнике. Добавить ее?
```

## 10. Сброс тестовых данных

Добавить отдельную функцию в GUI: `Сбросить тестовые данные`.

Разместить в разделе:

```text
Данные и обслуживание
```

### 10.1. Важно различать reset и закрытие периода

`Закрыть период и обнулить текущие взаиморасчеты` не удаляет покупки. Оно закрывает период и исключает закрытые покупки из текущих расчетов.

`Сбросить тестовые данные` предназначен для очистки локально внесенных тестовых покупок и расчетных периодов.

### 10.2. Безопасный default режим

По умолчанию кнопка должна делать безопасный reset:

```text
- создать backup;
- очистить purchases.yaml;
- очистить settlement_periods.yaml;
- сохранить participants/groups/categories;
- обновить GUI;
- показать путь к backup.
```

Не удалять участников, группы и категории по умолчанию.

### 10.3. Подтверждение

Перед reset обязательно показать диалог:

```text
Будет создан backup. Покупки и закрытые периоды взаиморасчетов будут очищены. Участники, группы и категории сохранятся. Продолжить?
```

Затем запросить typed confirm:

```text
RESET_TEST_DATA
```

Без typed confirm действие запрещено.

### 10.4. CLI companion command

Если удобно, добавить CLI-команду:

```powershell
expense-splitter data reset-test --confirm RESET_TEST_DATA
```

Но GUI-кнопка является обязательной. CLI companion желателен для тестируемости и автоматизации.

## 11. Тесты

Добавить или обновить тесты:

```text
tests/test_gui_smoke.py
tests/test_gui_actions.py
tests/test_categories.py
tests/test_storage.py
tests/test_cli.py  # если добавляется CLI reset-test
```

Покрыть:

1. default categories создаются/читаются;
2. custom category добавляется и сохраняется;
3. category отображается в purchase row model;
4. edit purchase меняет поля и сохраняет данные;
5. edit settled purchase blocked;
6. participants checklist helper возвращает выбранных участников;
7. manual participants parsing still works;
8. reset-test создает backup и очищает только purchases + settlement periods;
9. reset-test сохраняет participants/groups/categories;
10. GUI help не запускает event loop.

Реальный visual/manual GUI smoke фиксировать отдельно в progress report.

## 12. Документация

Обновить:

```text
README.md
docs/USER_GUIDE.md
docs/Troubleshooting.md
docs/DATA_SCHEMA.md
docs/SETTLEMENT_PERIODS.md  # если нужно пояснить различие reset vs close period
docs/reports/prod_ready_progress_report.md
```

Документировать:

- desktop GUI launcher;
- добавление и редактирование покупки;
- выбор участников через галочки;
- категории и пользовательские категории;
- отображение категории в таблице;
- сброс тестовых данных;
- отличие сброса тестовых данных от закрытия периода взаиморасчетов;
- что backup создается перед reset;
- generated artifacts не коммитятся.

## 13. Проверки качества

Минимальный набор:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m py_compile src\expense_splitter\gui\app.py src\expense_splitter\gui\actions.py src\expense_splitter\storage.py src\expense_splitter\models.py
.\.venv\Scripts\python.exe -m pytest tests\test_gui_smoke.py tests\test_gui_actions.py tests\test_categories.py -v
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
.\.venv\Scripts\python.exe -m ruff check src\expense_splitter\gui src\expense_splitter tests\test_gui_smoke.py tests\test_gui_actions.py tests\test_categories.py
.\.venv\Scripts\expense-splitter-gui.exe --help
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-gui.ps1 -Help
```

Manual GUI smoke:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-gui.ps1
```

Проверить вручную:

```text
- добавить покупку с категорией;
- увидеть категорию в главной таблице;
- отредактировать покупку;
- выбрать участников через галочки;
- ввести участников вручную;
- выбрать категорию из списка;
- добавить новую категорию;
- выполнить reset test data в изолированной test data directory;
- убедиться, что backup создан;
- убедиться, что участники/группы/категории сохранились.
```

## 14. Финальный ответ Codex

Финальный ответ после этапа должен содержать:

```text
1. Этап.
2. Статус.
3. Что изменено.
4. Какие проверки выполнены.
5. Какие проверки пропущены и почему.
6. Ошибки/warnings.
7. Измененные файлы.
8. Commit hash.
9. Push status.
10. GitHub Actions status, если был push.
11. Generated artifacts not staged.
12. UTF-8/mojibake check status.
13. Manual GUI smoke status.
14. Подтверждение: reset-test не удаляет participants/groups/categories по умолчанию.
15. Следующий рекомендуемый этап.
```
