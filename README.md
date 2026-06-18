# Инструкция для Manus: этап 2 — установщик, UX launcher, полный README и улучшения проекта Expense Splitter

## 0. Цель этапа

Доработать уже реализованный проект `expense-splitter` до состояния, пригодного для установки и использования на обычной машине без ручной разработки в терминале.

Нужно реализовать:

1. Установщик проекта.
2. Кроссплатформенные сценарии запуска.
3. UX launcher для пользователя.
4. Полный README с описанием проекта и инструкциями.
5. Обновление `REPORT.md` на каждом этапе.
6. Улучшения качества, упаковки, GitHub workflow и пользовательского сценария.

Важно: не переписывать рабочее ядро проекта без причины. Сначала сохранить работоспособность текущего CLI, потом добавлять упаковку и UX.

---

## 1. Исходное состояние по приложенному отчету

По текущему `Implementation Report.md` проект завершен как базовая CLI-реализация:

- проект называется `expense-splitter`;
- агент: Manus;
- ветка: `feature/expense-splitter-core`;
- GitHub remote не настроен;
- репозиторий создан локально;
- реализованы модели, YAML-хранение, расчет балансов, минимизация переводов, CLI, Markdown-отчеты и README;
- доступны команды `init`, `add-purchase`, `list-purchases`, `balances`, `settle`, `report`;
- тесты по расчетам, settlement и CLI были успешно пройдены.

Текущие ограничения:

1. Нет полноценного установщика.
2. Нет UX launcher для обычного пользователя.
3. README описывает в основном установку через `pip install -e .`, то есть сценарий разработчика, а не обычного пользователя.
4. Не описан полный жизненный цикл: установка, первый запуск, обновление, резервное копирование, удаление, восстановление данных.
5. GitHub remote не настроен, поэтому push/PR невозможны без URL.
6. Нужно проверить, существует ли реально `.github/workflows/ci.yml`, а не только упоминание в отчете.
7. Нужно обновить `REPORT.md` и документировать каждый новый этап.

---

## 2. Главный результат этапа

После выполнения этапа пользователь должен получить простой сценарий:

### Windows PowerShell, вариант для обычного пользователя

```powershell
.\scripts\install.ps1
.\scripts\run-launcher.ps1
```

или после установки:

```powershell
expense-splitter-launcher
```

### CLI-вариант

```powershell
expense-splitter init --with-examples
expense-splitter add-purchase
expense-splitter balances
expense-splitter settle
expense-splitter report
```

### Standalone-вариант, если реализован

Пользователь скачивает архив из GitHub Releases, распаковывает и запускает:

```powershell
ExpenseSplitter.exe
```

Если standalone exe невозможен в текущей среде, нужно подготовить инфраструктуру сборки через GitHub Actions и явно описать это в README и `REPORT.md`.

---

## 3. Обязательные задачи

### 3.1. Проверка состояния проекта

1. Перейти в корень проекта `expense-splitter`.
2. Выполнить:

```bash
git status
git branch --show-current
git remote -v
```

3. Проверить структуру проекта.
4. Проверить наличие файлов:
   - `pyproject.toml`;
   - `README.md`;
   - `REPORT.md`;
   - `src/expense_splitter/cli.py`;
   - `src/expense_splitter/__main__.py`;
   - `.github/workflows/ci.yml`;
   - `tests/`.

5. Запустить текущие тесты до внесения изменений:

```bash
python -m pytest
```

Если тесты не проходят, сначала зафиксировать причину в `REPORT.md`, потом исправить.

---

### 3.2. Git и GitHub

1. Создать новую ветку:

```bash
git checkout -b feature/installer-readme-launcher
```

Если такая ветка уже есть, переключиться на нее.

2. Если remote отсутствует, не выдумывать URL. Зафиксировать в `REPORT.md`:

```text
GitHub remote is not configured. Push and PR creation require repository URL from user.
```

3. Если remote есть, после успешной реализации выполнить:

```bash
git push -u origin feature/installer-readme-launcher
```

4. Подготовить текст Pull Request в `docs/PULL_REQUEST_INSTALLER.md`.

5. Не пушить напрямую в `main`.

---

### 3.3. Обновление REPORT.md

`REPORT.md` должен обновляться после каждого крупного этапа.

Добавить раздел:

```markdown
## Stage 2 — Installer, Launcher, README and Distribution
```

Для каждого подэтапа фиксировать:

- статус;
- дата/время;
- измененные файлы;
- что сделано;
- какие команды запускались;
- результат проверок;
- найденные проблемы;
- решения;
- commit hash после коммита, если коммит создан.

Минимальные подэтапы:

1. Pre-check and baseline tests.
2. Installer design.
3. Windows PowerShell installer.
4. Cross-platform install scripts.
5. UX launcher.
6. README expansion.
7. GitHub Actions / release workflow.
8. Tests and quality checks.
9. Final delivery notes.

Не писать в чат длинные логи. Подробности заносить в `REPORT.md`.

---

## 4. Установщик

### 4.1. Требования к установщику

Нужно реализовать понятный установочный сценарий минимум для Windows PowerShell.

Создать:

```text
scripts/
├── install.ps1
├── run-launcher.ps1
├── run-cli.ps1
├── uninstall.ps1
├── install.sh
└── run-launcher.sh
```

Если часть кроссплатформенной поддержки невозможна, реализовать best-effort и документировать ограничения.

---

### 4.2. Windows install.ps1

`scripts/install.ps1` должен:

1. Проверить наличие Python.
2. Проверить версию Python.
3. Создать виртуальное окружение `.venv`, если его нет.
4. Установить проект:

```powershell
python -m pip install --upgrade pip
pip install -e .
```

5. Проверить доступность команд:

```powershell
expense-splitter --help
```

6. Создать удобные wrapper-скрипты для запуска.
7. Вывести короткую инструкцию:

```text
Installation completed.
Run launcher:
.\scripts\run-launcher.ps1

Run CLI:
.\scripts\run-cli.ps1 --help
```

8. Не требовать прав администратора.
9. Не менять системный PATH без явного параметра пользователя.
10. Все ошибки выводить понятным текстом.

Дополнительный параметр:

```powershell
.\scripts\install.ps1 -Dev
```

Устанавливает dev-зависимости:

```powershell
pip install -e ".[dev]"
```

---

### 4.3. run-launcher.ps1

`scripts/run-launcher.ps1` должен:

1. Активировать `.venv`.
2. Запустить UX launcher.
3. Если `.venv` отсутствует, предложить выполнить `install.ps1`.

Пример:

```powershell
.\scripts\run-launcher.ps1
```

---

### 4.4. run-cli.ps1

`scripts/run-cli.ps1` должен прокидывать аргументы в CLI.

Пример:

```powershell
.\scripts\run-cli.ps1 balances
.\scripts\run-cli.ps1 settle
.\scripts\run-cli.ps1 report
```

---

### 4.5. uninstall.ps1

`scripts/uninstall.ps1` должен:

1. Удалять `.venv`.
2. Не удалять пользовательские данные по умолчанию.
3. Предлагать отдельный параметр для удаления локальных данных:

```powershell
.\scripts\uninstall.ps1 -RemoveData
```

4. Документировать, какие папки удаляются.

---

### 4.6. Linux/macOS install.sh

`scripts/install.sh` должен:

1. Проверять Python 3.
2. Создавать `.venv`.
3. Устанавливать проект.
4. Показывать команды запуска.
5. Работать без sudo.

---

## 5. UX launcher

### 5.1. Назначение

Нужен UX launcher для пользователя, которому неудобно запоминать команды CLI.

Это не обязательно графическое приложение. Достаточно интерактивного терминального меню на `rich`/`typer`, если оно удобно и понятно.

---

### 5.2. Обязательные команды launcher

Добавить модуль:

```text
src/expense_splitter/launcher.py
```

Добавить entry point в `pyproject.toml`:

```toml
expense-splitter-launcher = "expense_splitter.launcher:main"
```

Launcher должен показывать меню:

```text
Expense Splitter

1. Добавить покупку
2. Показать покупки
3. Показать балансы
4. Показать итоговые переводы
5. Создать отчет
6. Открыть папку с данными
7. Открыть папку с отчетами
8. Проверить данные
9. Выход
```

Требования:

1. Не ломать существующий CLI.
2. Использовать существующие функции из модулей проекта, а не дублировать бизнес-логику.
3. Понятно обрабатывать ошибки.
4. После действия возвращаться в меню.
5. Для добавления покупки использовать интерактивные вопросы:
   - название;
   - сумма;
   - плательщик;
   - группа или ручной список участников;
   - дата;
   - категория;
   - комментарий.
6. Для ручного списка участников принимать имена через запятую.
7. Для группы показывать доступные группы.
8. После добавления покупки показывать краткое подтверждение.

---

### 5.3. UX launcher smoke test

Добавить тесты или хотя бы smoke-тесты:

1. Проверка импорта `expense_splitter.launcher`.
2. Проверка существования `main`.
3. Проверка, что entry point определен в `pyproject.toml`.
4. Проверка, что launcher не импортирует тяжелые или внешние зависимости без необходимости.

---

## 6. Standalone-сборка и GitHub Releases

### 6.1. PyInstaller

Добавить опциональную сборку standalone-приложения через PyInstaller.

Файлы:

```text
packaging/
├── expense_splitter.spec
└── README_PACKAGING.md
```

Скрипты:

```text
scripts/
├── build-windows.ps1
└── build-unix.sh
```

`build-windows.ps1` должен:

1. Установить dev/build зависимости.
2. Запустить PyInstaller.
3. Сложить результат в `dist/`.
4. Вывести путь к `ExpenseSplitter.exe`.

Если PyInstaller не подходит или не запускается в текущей среде, не имитировать успех. Зафиксировать ограничение в `REPORT.md`.

---

### 6.2. GitHub Actions release workflow

Создать workflow:

```text
.github/workflows/build-release.yml
```

Назначение:

1. Сборка на Windows.
2. Сборка на Linux.
3. Запуск тестов.
4. Создание build artifacts.
5. Подготовка к публикации Release по tag.

Минимальный workflow:

- Python 3.11;
- install dependencies;
- `python -m pytest`;
- PyInstaller build;
- upload artifact.

Не усложнять. Сначала рабочий workflow, потом красота. Красота без артефакта — это просто театр.

---

## 7. Полный README

Текущий README нужно расширить до полноценной пользовательской документации.

Обязательные разделы:

1. Название и назначение проекта.
2. Для кого проект.
3. Что умеет приложение.
4. Быстрый старт для Windows.
5. Быстрый старт для Linux/macOS.
6. Установка через PowerShell installer.
7. Установка через pip/uv для разработчика.
8. Запуск UX launcher.
9. Запуск CLI.
10. Первый сценарий: создать данные, добавить покупку, посмотреть балансы, сформировать переводы.
11. Описание участников и групп.
12. Где хранятся данные.
13. Как сделать резервную копию.
14. Как восстановить данные.
15. Как обновить проект.
16. Как удалить проект.
17. Как собрать standalone exe.
18. Как скачать GitHub Release, если релизы настроены.
19. Все CLI-команды с примерами.
20. Формат YAML-файлов.
21. Алгоритм расчета балансов.
22. Алгоритм минимизации переводов.
23. Округления и денежные расчеты.
24. Отчеты.
25. Тестирование.
26. Troubleshooting.
27. FAQ.
28. Ограничения текущей версии.
29. Roadmap.

README должен быть на русском языке.

---

## 8. Документация для пользователя

Дополнительно создать:

```text
docs/
├── USER_GUIDE.md
├── INSTALLATION.md
├── PACKAGING.md
├── TROUBLESHOOTING.md
└── PULL_REQUEST_INSTALLER.md
```

Назначение:

- `USER_GUIDE.md` — обычное использование.
- `INSTALLATION.md` — установка на Windows/Linux/macOS.
- `PACKAGING.md` — сборка standalone.
- `TROUBLESHOOTING.md` — типовые ошибки.
- `PULL_REQUEST_INSTALLER.md` — описание изменений для PR.

Если README получается слишком большим, вынести подробности в docs, а README сделать главным входом.

---

## 9. Проверки качества

После реализации запустить:

```bash
python -m pytest
python -m ruff check .
```

Если есть mypy:

```bash
python -m mypy src
```

Проверить команды:

```bash
expense-splitter --help
expense-splitter-launcher --help
```

Проверить Windows scripts синтаксически, если среда позволяет:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1 -Dev
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-cli.ps1 --help
```

Если текущая среда не Windows, зафиксировать в `REPORT.md`, что PowerShell scripts не были полноценно выполнены на Windows, и проверить хотя бы статически.

---

## 10. Экономия токенов и режима работы Manus

1. Не пересказывать весь код в чат.
2. Не вставлять полные логи тестов в чат.
3. Подробные логи и решения писать в `REPORT.md`.
4. В чат выводить только краткий статус:
   - этап;
   - что сделано;
   - есть ли блокер.
5. Не читать полностью большие файлы, если достаточно заголовков, структуры и релевантных фрагментов.
6. Не переписывать README целиком в чат.
7. Не генерировать длинные объяснения алгоритмов, если они уже есть в docs.
8. Не делать косметические изменения вне задачи.
9. Не запускать тяжелую сборку несколько раз без причины.
10. Не создавать новые зависимости без необходимости.

---

## 11. Возможные улучшения сверх обязательного минимума

Если обязательные задачи выполнены и тесты проходят, можно добавить улучшения:

### 11.1. Проверка данных

Команда:

```bash
expense-splitter validate
```

Проверяет:

- неизвестных участников;
- пустые группы;
- покупки без участников;
- отрицательные или нулевые суммы;
- дубли имен;
- некорректные даты;
- расхождение итогов балансов.

### 11.2. Экспорт отчетов

Добавить:

```bash
expense-splitter report --format markdown
expense-splitter report --format csv
expense-splitter report --format xlsx
```

XLSX делать только если это не ломает простоту проекта.

### 11.3. Импорт из Excel

Если исходный Excel-файл доступен, добавить отдельную команду:

```bash
expense-splitter import-excel path/to/file.xlsx
```

На первом этапе можно сделать только каркас и документацию, если структура Excel нестабильна.

### 11.4. История периодов

Добавить поддержку периодов:

```bash
expense-splitter period create 2026-06
expense-splitter period use 2026-06
```

### 11.5. Backup

Добавить:

```bash
expense-splitter backup
expense-splitter restore path/to/backup.zip
```

### 11.6. Улучшение settlement

Добавить проверку:

- сумма долгов равна сумме кредитов;
- итог после переводов закрывается в ноль;
- количество транзакций не превышает `debtors + creditors - 1` в типичном случае.

---

## 12. Критерии готовности этапа

Этап считается завершенным, если:

1. Есть `scripts/install.ps1`.
2. Есть `scripts/run-launcher.ps1`.
3. Есть `scripts/run-cli.ps1`.
4. Есть `scripts/uninstall.ps1`.
5. Есть хотя бы best-effort `install.sh`.
6. Есть `src/expense_splitter/launcher.py`.
7. В `pyproject.toml` есть entry point для launcher.
8. README полностью обновлен.
9. Есть документация в `docs/`.
10. Есть packaging-инструкция.
11. Есть GitHub Actions workflow для тестов и, желательно, release build.
12. `REPORT.md` обновлен по всем этапам.
13. Тесты проходят.
14. Старые CLI-команды не сломаны.
15. Финальный отчет Manus содержит:
    - список измененных файлов;
    - команды проверки;
    - результаты проверки;
    - commit hashes;
    - статус GitHub remote/push/PR;
    - ограничения.

---

## 13. Финальное сообщение Manus

В конце вывести кратко:

```markdown
## Stage 2 completed

### Implemented
- ...

### Files changed
- ...

### Checks
- `python -m pytest` — passed/failed
- `python -m ruff check .` — passed/failed

### Git
- Branch:
- Commits:
- Remote:
- Push:
- PR:

### User commands
```powershell
.\scripts\install.ps1
.\scripts\run-launcher.ps1
```

### Remaining limitations
- ...
```

Не писать роман. Роман уже написал README.
## GitHub Actions и структура проекта

Целевая production-ready структура локального проекта использует корень
репозитория как корень Python-пакета. GitHub Actions должны запускаться из `.`
и устанавливать пакет командой:

```bash
python -m pip install -e ".[dev]"
```

Предыдущая remote-структура с вложенной папкой `expense-splitter/` не считается
целевой production-ready структурой для локальной P0-доработки.

## Аналитика за период

Expense Splitter создает Markdown, CSV и PNG-отчеты за месяц, квартал или год:

```powershell
expense-splitter analytics --period month --year 2026 --month 6 --format all
```

Результат сохраняется в `reports/analytics/<year>/<period-id>/`. Доступные значения `--format`: `markdown`, `csv`, `png`, `all`. CSV совместимы с Excel на Windows благодаря кодировке UTF-8 with BOM.
