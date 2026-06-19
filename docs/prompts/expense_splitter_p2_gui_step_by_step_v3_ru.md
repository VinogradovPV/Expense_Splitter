# Expense Splitter: пошаговая инструкция P2.GUI.2
## UX-доработка desktop GUI launcher после P2.GUI.1

Дата актуализации: 2026-06-19.

## 0. Назначение

Эта инструкция описывает следующий этап после P2.GUI.1.

P2.GUI.1 уже добавил desktop GUI launcher на `tkinter`, но ручной smoke-test выявил UX-проблемы:

1. Нет редактирования покупки.
2. Участники вводятся неудобной строкой, нужен checklist/multi-select и сохранение ручного ввода.
3. Категория вводится, но не отображается в главной таблице покупок.
4. Нужны предустановленные и пользовательские категории.
5. Нужна безопасная кнопка сброса тестовых данных.

Цель P2.GUI.2 — исправить эти проблемы без переписывания проекта.

---

## 1. Общие правила

### 1.1. Рабочая директория

```powershell
cd C:\Users\Rockaudit\LLM_CHAT\expense_splitter
```

### 1.2. Git/GitHub

Все `git` и `gh` команды выполнять outside sandbox.

Перед commit:

```powershell
git status --short --ignored
git diff --name-only
git diff --cached --name-only
```

Не коммитить:

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
```

### 1.3. UTF-8

Перед проверками:

```powershell
chcp 65001
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
```

Обязательная проверка:

```powershell
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
```

---

# P2.GUI.2.1 — Предпроверка и фиксация состояния P2.GUI.1

## Цель

Убедиться, что рабочая копия содержит P2.GUI.1, понять, создан ли commit/push, и не потерять локальные изменения.

## Команды

```powershell
git status --short --ignored
git branch --show-current
git log --oneline -10
git remote -v
```

Проверить GUI entry point:

```powershell
.\.venv\Scripts\expense-splitter-gui.exe --help
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-gui.ps1 -Help
```

## Действия

1. Если P2.GUI.1 изменения не закоммичены, не начинать UX-доработку до решения:
   - либо создать commit P2.GUI.1 после минимальных проверок;
   - либо зафиксировать blocker.
2. Если P2.GUI.1 уже закоммичен, перейти к P2.GUI.2.
3. Обновить `docs/reports/prod_ready_progress_report.md`.

---

# P2.GUI.2.2 — Категории: storage, defaults, GUI selection

## Цель

Добавить справочник категорий и удобный выбор категории в GUI.

## Создать/изменить файлы

```text
src/expense_splitter/defaults.py
src/expense_splitter/storage.py
src/expense_splitter/gui/dialogs.py
src/expense_splitter/gui/actions.py
src/expense_splitter/gui/state.py
data/categories.yaml
tests/test_categories.py
docs/DATA_SCHEMA.md
docs/USER_GUIDE.md
README.md
```

## Default categories

```text
кофе
еда
безалкогольные напитки
алкоголь
техника
аксессуары
продукты
хозтовары
аптека и здоровье
развлечения
подарки
прочее
без категории
```

## Требования

1. Добавить `data/categories.yaml` со schema_version.
2. Если файла нет, использовать default categories.
3. При `init` создавать categories.yaml.
4. GUI должен показывать категорию через editable combobox.
5. Новая категория добавляется только после подтверждения.
6. Все сохранения через atomic write/backup.

## Проверки

```powershell
.\.venv\Scripts\python.exe -m py_compile src\expense_splitter\storage.py src\expense_splitter\defaults.py
.\.venv\Scripts\python.exe -m pytest tests\test_categories.py -v
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
```

---

# P2.GUI.2.3 — Отображение категории в таблице покупок

## Цель

Исправить UX-дефект: категория вводится, но не отображается в главном окне.

## Файлы

```text
src/expense_splitter/gui/app.py
src/expense_splitter/gui/widgets.py
src/expense_splitter/gui/actions.py
tests/test_gui_smoke.py
tests/test_gui_actions.py
```

## Требования

1. Добавить колонку `Категория` в таблицу покупок.
2. Показывать `Без категории`, если категория пустая.
3. После добавления или редактирования покупки обновлять таблицу.
4. Не ломать сортировку/выбор строк.

## Проверки

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_gui_smoke.py tests\test_gui_actions.py -v
```

Manual smoke:

```text
Добавить покупку с категорией кофе и убедиться, что категория видна в главной таблице.
```

---

# P2.GUI.2.4 — Редактирование покупки

## Цель

Добавить возможность исправлять ошибки ручного ввода.

## Файлы

```text
src/expense_splitter/gui/dialogs.py
src/expense_splitter/gui/actions.py
src/expense_splitter/gui/app.py
tests/test_gui_actions.py
tests/test_storage.py
```

## Требования

1. Добавить кнопку `Редактировать покупку`.
2. Если строка не выбрана, показать сообщение.
3. Открыть форму с текущими значениями покупки.
4. Разрешить менять:
   - наименование;
   - сумму;
   - плательщика;
   - участников;
   - дату;
   - категорию;
   - комментарий.
5. Валидировать сумму, дату, плательщика и участников.
6. Сохранять через storage с backup/atomic write.
7. Обновлять таблицу после сохранения.
8. Блокировать редактирование закрытой покупки.

## Проверки

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_gui_actions.py -v
```

Manual smoke:

```text
Добавить покупку, затем отредактировать сумму/категорию/участников и проверить таблицу.
```

---

# P2.GUI.2.5 — Участники: checklist + ручной ввод

## Цель

Заменить неудобный ввод участников одной строкой на удобный выбор с галочками, сохранив ручной ввод.

## Файлы

```text
src/expense_splitter/gui/dialogs.py
src/expense_splitter/gui/widgets.py
src/expense_splitter/gui/actions.py
tests/test_gui_actions.py
```

## Требования

1. В форме покупки добавить кнопку `Выбрать участников`.
2. Открывать modal checklist со всеми известными участниками.
3. Добавить кнопки:
   - выбрать всех;
   - снять всех;
   - применить;
   - отмена.
4. Рядом оставить ручное поле через запятую.
5. Синхронизировать checklist и ручное поле.
6. Новых участников не добавлять молча.

## Проверки

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_gui_actions.py -v
```

Manual smoke:

```text
Выбрать участников галочками, затем изменить список вручную и сохранить покупку.
```

---

# P2.GUI.2.6 — Сброс тестовых данных

## Цель

Добавить безопасную очистку тестовых покупок и закрытых settlement periods без удаления справочников.

## Файлы

```text
src/expense_splitter/gui/app.py
src/expense_splitter/gui/actions.py
src/expense_splitter/storage.py
src/expense_splitter/cli.py  # если добавляется CLI companion
tests/test_gui_actions.py
tests/test_storage.py
docs/USER_GUIDE.md
docs/Troubleshooting.md
README.md
```

## Требования

Default reset:

```text
- создать backup;
- очистить purchases.yaml;
- очистить settlement_periods.yaml;
- сохранить participants/groups/categories;
- обновить GUI;
- показать путь к backup.
```

Подтверждение:

```text
RESET_TEST_DATA
```

Без typed confirm reset не выполняется.

Если добавляется CLI companion:

```powershell
expense-splitter data reset-test --confirm RESET_TEST_DATA
```

## Проверки

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_storage.py tests\test_gui_actions.py -v
```

Manual smoke в изолированной директории:

```text
1. Создать тестовую покупку.
2. Создать/закрыть settlement period.
3. Нажать `Сбросить тестовые данные`.
4. Подтвердить RESET_TEST_DATA.
5. Проверить, что purchases и settlement periods очищены.
6. Проверить, что participants/groups/categories сохранились.
7. Проверить наличие backup.
```

---

# P2.GUI.2.7 — Документация

## Обновить

```text
README.md
docs/USER_GUIDE.md
docs/Troubleshooting.md
docs/DATA_SCHEMA.md
docs/SETTLEMENT_PERIODS.md
docs/reports/prod_ready_progress_report.md
```

## Документировать

```text
- как запускать desktop GUI;
- как добавить покупку;
- как редактировать покупку;
- как выбрать участников галочками;
- как использовать ручной ввод участников;
- как выбирать и добавлять категории;
- список предустановленных категорий;
- почему категория отображается в таблице;
- как сбросить тестовые данные;
- отличие reset-test от close settlement period;
- какие backup создаются;
- что generated reports/data backups не коммитятся.
```

---

# P2.GUI.2.8 — Quality gate

## Команды

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m py_compile src\expense_splitter\gui\app.py src\expense_splitter\gui\actions.py src\expense_splitter\gui\dialogs.py src\expense_splitter\storage.py src\expense_splitter\models.py
.\.venv\Scripts\python.exe -m pytest tests\test_categories.py tests\test_gui_smoke.py tests\test_gui_actions.py -v
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\expense-splitter-gui.exe --help
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-gui.ps1 -Help
```

Manual GUI smoke:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-gui.ps1
```

## Commit

После успешных проверок:

```powershell
git status --short --ignored
git add src tests data docs README.md pyproject.toml scripts
# Добавлять только реально измененные файлы.
git commit -m "feat: improve desktop GUI purchase editing and data reset"
git push
```

После push:

```powershell
gh run list --limit 5
```

## Критерии завершения

```text
- Редактирование покупки работает.
- Категория отображается в главной таблице.
- Категории выбираются из списка и могут дополняться.
- Участники выбираются галочками и могут вводиться вручную.
- Reset-test очищает только purchases/settlement periods и сохраняет справочники.
- Backup создается перед reset-test.
- Полный pytest проходит.
- Encoding check проходит.
- CI после push success.
```
