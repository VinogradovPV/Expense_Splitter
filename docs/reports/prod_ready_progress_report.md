## P2.GUI.4 / P2.RPT.1 — Current settlement state report

Дата: 2026-06-25
Статус: реализовано локально; quality gate пройден, commit/push и GitHub Actions выполняются
после фиксации изменений.

### Реализовано

- CLI-команда `expense-splitter current-report` с default `--scope open --format all`.
- Поддержка `--scope open|all` и форматов `markdown`, `csv`, `png`, `html`, `xlsx`, `all`.
- Snapshot-каталог `reports/current_state/<scope>_<YYYY-MM-DD_HH-MM-SS>/`.
- Markdown, offline HTML, XLSX, `metadata.json`, CSV-таблицы и PNG-графики текущего состояния.
- GUI-кнопки на вкладке `Текущие расчеты`: создать отчет, открыть HTML, открыть XLSX, открыть
  папку отчета.
- Переиспользование существующих `calculate_balances`, `calculate_settlements` и open/all scope
  filtering без изменения логики закрытия периодов.
- Документация в README, USER_GUIDE, ANALYTICS, SETTLEMENT_PERIODS и Troubleshooting.

### Ограничения

Settlement-period-specific вариант `current-report --settlement-period <id>` не включен в этот
этап, чтобы не расширять контракт закрытых snapshot сверх текущей задачи. Рекомендуемый следующий
этап: P2.RPT.2 — отчет по конкретному settlement period.

### Проверки

- `python -m pip install -e ".[dev]"` — OK; сохраняется прежнее warning: Typer 0.26.7 не
  объявляет extra `all`.
- `pytest tests\test_current_report.py -v` — `6 passed`.
- `pytest tests -v` — `109 passed`.
- `compileall -q src tests` — OK.
- `scripts\qa\check_text_encoding.py` — OK.
- `ruff check src tests` — OK.
- `git diff --check` — OK; только предупреждения Git о будущей CRLF-нормализации.
- CLI smoke `current-report --scope open --format all`, `--scope all --format all`,
  `--scope open --format html`, `--scope open --format xlsx` — OK.
- GUI smoke `expense-splitter-gui.exe --help` и `scripts\run-gui.ps1 -Help` — OK.

## P2.REL.1-WIN-ENCODING — Windows/Linux CI UTF-8 hotfix

- Причина: Windows `Build Release` падал в `tests/test_cli.py::test_report` на
  `UnicodeDecodeError` при чтении Markdown-отчета через системную кодировку. Аналогичный риск
  возможен на Linux runner при не-UTF-8 locale, если текстовые файлы читаются без явного encoding.
- Измененные файлы: `tests/test_cli.py`,
  `docs/reports/prod_ready_progress_report.md`.
- Проверки:
  - `pytest tests\test_cli.py::test_report -v` — OK, `1 passed`.
  - `pytest tests -v` — OK, `100 passed`.
  - `compileall -q src tests` — OK.
  - `scripts\qa\check_text_encoding.py` — OK.
  - `ruff check src tests` — OK.
  - `git diff --check` — OK; есть только предупреждение Git о будущей CRLF-нормализации
    измененных `.md/.py` файлов.
  - `Select-String`/`rg` по `.read_text()`/`.write_text()` — оставшиеся вызовы используют
    `encoding="utf-8"` или CSV policy `encoding="utf-8-sig"`.
- GitHub Actions: pending; будет проверено после push.
- Commit: pending.

## P2.GUI.1 — Desktop GUI launcher foundation

Дата: 2026-06-19
Статус: завершено и опубликовано (`8e05a0b`).

### Цель

Добавить отдельный безконсольный desktop GUI launcher на `tkinter`, не удаляя CLI и текущий
console launcher.

### Изменения

| Файл/область | Изменение |
|---|---|
| `src/expense_splitter/gui/` | Добавлен пакет GUI: `app.py`, `actions.py`, `state.py`, `dialogs.py`, `widgets.py` |
| `pyproject.toml` | Добавлен entry point `expense-splitter-gui = "expense_splitter.gui.app:main"` |
| `scripts/run-gui.ps1` | Добавлен Windows wrapper для запуска GUI и `-Help` |
| `packaging/expense_splitter.spec` | Добавлен `expense-splitter-gui` PyInstaller target с `console=False` |
| `tests/test_gui_smoke.py` | Добавлены smoke tests без запуска реального `mainloop` |
| `README.md`, `docs/USER_GUIDE.md`, `docs/Troubleshooting.md` | Добавлена документация по GUI launcher и PowerShell execution policy |
| `scripts/qa/check_text_encoding.py` | GUI prompt v2 добавлен в allow-list строк с примерами mojibake-маркеров |
| `scripts/build-windows.ps1`, `scripts/build-unix.sh` | Не менялись: оба скрипта уже собирают общий `packaging/expense_splitter.spec`, где добавлен GUI target |

### Функциональность GUI

- Разделы: `Покупки`, `Текущие расчеты`, `Периоды взаиморасчетов`, `Аналитика и отчеты`, `Данные и обслуживание`, `Справка`.
- Просмотр и добавление покупок.
- Просмотр балансов и итоговых переводов по open scope.
- Запуск analytics за month/quarter/year.
- Открытие папок `data` и `reports`.
- Просмотр settlement periods.
- Preview закрытия периода.
- Кнопка `Закрыть период и обнулить текущие взаиморасчеты` с предупреждением и confirm.
- Закрытие периода использует существующую `settlement_periods.close` логику и не удаляет покупки.

### Проверки

| Команда / проверка | Статус | Результат |
|---|---|---|
| `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"` | OK outside sandbox | Entry point `expense-splitter-gui.exe` установлен |
| `.\.venv\Scripts\python.exe -m py_compile src\expense_splitter\gui\app.py src\expense_splitter\gui\actions.py src\expense_splitter\gui\state.py` | OK outside sandbox | Синтаксис корректен |
| `.\.venv\Scripts\python.exe -m pytest tests\test_gui_smoke.py -v` | OK outside sandbox | `4 passed` |
| `.\.venv\Scripts\expense-splitter-gui.exe --help` | OK outside sandbox | Help выводится без запуска GUI event loop |
| `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run-gui.ps1 -Help` | OK outside sandbox | Help wrapper-а выводится |
| Полный pytest | OK, подтверждено пользователем | Проверки P2.GUI.1 завершены перед публикацией |
| Compileall | OK, подтверждено пользователем | Проверка завершена перед публикацией |
| Encoding | OK, подтверждено пользователем | Проверка завершена перед публикацией |
| Ручной GUI smoke | pending | Требует интерактивного визуального окна; будет зафиксирован отдельно |

### Публикация

Первоначальное ограничение outside-sandbox было снято после самостоятельного запуска проверок
пользователем. P2.GUI.1 опубликован отдельным commit до начала P2.GUI.2.

### Git/GitHub

- Commit hash: `8e05a0b`.
- Push: выполнен пользователем в `origin/prod-ready/p0-p1`.
- GitHub Actions: проверяется отдельно после публикации P2.GUI.2.
- Generated artifacts: не staged; `git status --short --ignored` показал их только как ignored.

## P2.GUI.2 — UX desktop GUI

Дата: 2026-06-19
Статус: реализовано локально; автоматический quality gate пройден, manual GUI smoke и публикация
pending.

Добавлены редактирование открытых покупок, колонка категории, checklist/multi-select участников и
категорий, editable ComboBox, persistent `categories.yaml` и безопасный reset-test с typed confirm
`RESET_TEST_DATA`. Reset создает backup и очищает только покупки и settlement periods, сохраняя
participants/groups/categories.

### Реализовано

- Persistent `data/categories.yaml` и default categories.
- Editable ComboBox и checklist/multi-select категорий; новые значения сохраняются только после
  подтверждения.
- Колонка `Категория` в таблице покупок и fallback `Без категории`.
- Редактирование покупки с текущими значениями и блокировкой закрытых записей.
- Checklist участников с `Выбрать все`, `Снять все`, `Применить`, `Отмена` и сохранением ручного
  ввода через запятую.
- Reset-test с предупреждением и typed confirm `RESET_TEST_DATA`; backups обоих YAML создаются до
  очистки, participants/groups/categories сохраняются.

### Документация

Обновлены `README.md`, `docs/USER_GUIDE.md`, `docs/Troubleshooting.md`, `docs/DATA_SCHEMA.md` и
`docs/SETTLEMENT_PERIODS.md`. Зафиксировано отличие reset-test от закрытия периода и запрет на
staging generated reports, caches и timestamped backups.

### Quality gate P2.GUI.2.8

| Проверка | Результат |
|---|---|
| `python -m pip install -e ".[dev]"` | OK; warning: Typer 0.26.7 не предоставляет extra `all` |
| `py_compile` GUI/actions/dialogs/storage/models | OK |
| Фокусный pytest categories/GUI | `15 passed` |
| Полный `pytest tests -v` | `87 passed` |
| `compileall -q src tests` | OK |
| `scripts/qa/check_text_encoding.py` | OK; UTF-8, mojibake markers не найдены |
| `ruff check src tests` | OK |
| `expense-splitter-gui.exe --help` | OK; event loop не запущен |
| `scripts/run-gui.ps1 -Help` | OK |
| Isolated GUI startup smoke | OK; реальный tkinter-процесс оставался жив после запуска с `.tmp/p2_gui_2_manual/data` |
| Полный manual GUI smoke | pending; API-сеанс не может выполнять интерактивные клики в tkinter |

Commit, push и GitHub Actions не выполняются до фиксации manual GUI smoke либо явного решения
пользователя принять автоматический gate без интерактивной проверки.

## P2.A.1 — Static HTML analytics report

Дата: 2026-06-19
Статус: завершено, опубликовано, CI success.

### Цель

Добавить автономный `analytics_dashboard.html` без внешних зависимостей и web-server, переиспользуя
существующие Markdown, metadata, CSV и PNG.

### Изменённые файлы

- `src/expense_splitter/analytics_html.py` — безопасный renderer на стандартной библиотеке.
- `src/expense_splitter/analytics_reporting.py`, `cli.py` — форматы `html` и обновлённый `all`.
- `src/expense_splitter/gui/app.py`, `gui/actions.py` — формат HTML и действие `Открыть HTML`.
- `tests/test_analytics_html.py`, `tests/test_analytics_reporting.py` — HTML/CLI/regression tests.
- README и аналитическая пользовательская документация.

### Проверки

| Проверка | Результат |
|---|---|
| Editable install | OK; warning о deprecated Typer extra `all` |
| `pytest tests/test_analytics_html.py -v` | `4 passed` |
| Полный `pytest tests` | `91 passed` |
| `compileall -q src tests` | OK |
| Encoding/mojibake check | OK |
| `ruff check src tests` | OK |
| CLI month/quarter/year `--format html` | OK |
| CLI month `--format all` | OK, HTML включён |
| PNG visual QA | OK; `spending_by_category.png` читаем |
| HTML browser QA | Ограничение среды: встроенный браузер недоступен; source/offline contracts проверены тестами |

### Git/GitHub

- Feature commit: `21f2805 feat: add static HTML analytics report`.
- Push: выполнен в `origin/prod-ready/p0-p1`.
- GitHub Actions: success, run `27832179730`.
- Generated `reports/` и пользовательские YAML не staged.

### Ограничения

HTML статический: фильтры и интерактивные графики намеренно отсутствуют. XLSX перенесён в P2.A.2.

## P2.A.2 — XLSX analytics report

Дата: 2026-06-19
Статус: реализовано локально; quality gate пройден, публикация pending.

### Цель

Добавить Excel/XLSX-отчёт аналитики за месяц, квартал и год без COM automation и зависимости от
установленного Microsoft Excel.

### Изменённые области

- `analytics_xlsx.py` — workbook renderer на `openpyxl` с десятью листами и PNG-графиками.
- Reporting/CLI/GUI — формат `xlsx`, обновлённый `all`, действие `Открыть XLSX`.
- `pyproject.toml` — runtime dependency `openpyxl>=3.1`.
- XLSX/CLI/regression tests и русскоязычная документация.

### Quality gate

- Editable install: OK, `openpyxl 3.1.5`.
- Фокусные XLSX tests: `4 passed`.
- Полный pytest: `95 passed`.
- Compileall: OK.
- Encoding/mojibake: OK.
- Ruff: OK.
- CLI month/quarter/year `--format xlsx`: OK.
- CLI month `--format all`: OK, XLSX включён.
- Workbook QA через `openpyxl.load_workbook`: 10 листов, 6 PNG, filters/freeze panes OK.

Commit, push и GitHub Actions фиксируются после публикации.

## P2.GUI.3 — GUI polish and report-open flows

Дата: 2026-06-19
Статус: завершено, опубликовано; автоматический gate, manual GUI/Excel smoke и CI пройдены.

Добавлены report-open flows для HTML/XLSX/Markdown/папки, статус последнего отчёта, фильтры и
сортировка покупок, details/context period, scope open/all, details/reopen settlement periods и
ручной backup данных. Ошибки файлов показываются через messagebox без traceback.

После manual feedback добавлено защищённое удаление open-покупки: typed confirm `DELETE_PURCHASE`,
автоматический backup и запрет удаления settled/settlement-period покупок.

Одновременно исправлена совместимость XLSX с Microsoft Excel: удалены проблемные Table XML,
сохранены обычные auto-filter ranges. Regression test проверяет отсутствие `xl/tables/` parts.

Автоматические проверки после feedback: focused `18 passed`, полный pytest `100 passed`, compileall, encoding,
Ruff и GUI entry point help — OK. Исправленный XLSX структурно валиден, содержит 10 листов и 6 PNG,
не содержит `xl/tables/` parts и открывается в Microsoft Excel без recovery. Основные GUI-сценарии
подтверждены пользователем. Commit: `b344a5d`; GitHub Actions run `27931751603` — success.

## P2.DOC.1 — Documentation cleanup

Дата: 2026-06-22
Статус: завершено, опубликовано; quality gate и CI пройдены.

README полностью перестроен как пользовательская входная страница: GUI-first quick start,
покупки, безопасность данных, settlement periods, все форматы аналитики, CLI, PowerShell,
standalone, troubleshooting, документация, development и roadmap. Исторические Manus/P0-блоки,
старые ограничения и хронология удалены из README.

Переписаны на русском `USER_GUIDE.md`, `ANALYTICS.md`, `SETTLEMENT_PERIODS.md`, `DATA_SCHEMA.md`,
`Troubleshooting.md` и `PACKAGING.md`. Документы синхронизированы с HTML/XLSX, GUI filters/report
flows, безопасным удалением, reset-test, backups и тремя PyInstaller executables.

История предыдущих этапов ниже сохранена без переписывания.

Проверки: placeholder scan — OK; документированные пути — существуют; encoding/mojibake — OK;
полный pytest — `100 passed`; compileall — OK; `git diff --check` выполняется перед commit.

Commit: `b4a43ac`; GitHub Actions run `27931999659` — success.

## P2.REL.1 — Release quality gate

Дата: 2026-06-22
Ветка: `prod-ready/p0-p1`
Проверенный commit: `b4a43ac`
Статус: **production-ready candidate**.

### Проверки

- Установка: обновлены `pip`, `setuptools`, `wheel`; editable install `.[dev]` и
  `scripts/install.ps1 -Dev` выполнены успешно.
- Quality gate: `100 passed in 7.84s`; compileall, encoding/mojibake checker, Ruff и
  `git diff --check` — OK.
- CLI smoke: help для основного CLI, analytics и settlement-period; в изолированном
  `.tmp/p2_rel_1` пройдены init, add/list, balances/settle scope open и preview периода.
- Analytics smoke: отчёты month/quarter/year содержат Markdown, HTML, metadata.json,
  по 9 CSV, по 6 PNG и XLSX. Все XLSX читаются `openpyxl`, содержат 10 листов и не
  содержат проблемных `xl/tables/` частей.
- GUI smoke: entry-point и PowerShell help — OK. Полный manual smoke P2.GUI.3 подтверждён
  пользователем: покупки, фильтры, HTML/XLSX, close/reset-test, отсутствие traceback и mojibake.
- Data safety: smoke использовал только ignored temp data; реальные пользовательские YAML не
  изменялись. Тесты подтверждают разделение reset-test и закрытия периода, backups и сохранение
  participants/groups/categories при reset-test.
- PyInstaller: `scripts/build-windows.ps1 -NoUpx` завершён успешно; созданы три ignored exe.
  Standalone CLI `--help` и GUI `--help` завершились с кодом 0; console launcher показал меню.
- GitHub Actions: CI для проверенного commit — success (`27931999659`). Workflow
  `build-release.yml` запускается вручную или по tag `v*.*.*`; tag-triggered release ещё не проверен.
- Generated artifacts: `.tmp/`, `reports/`, `build/`, `dist/`, caches, egg-info и `.bak`
  остаются ignored и не включаются в staging.

### Известные ограничения

- Полная публикация GitHub Release требует отдельного тестового release tag.
- После принудительно остановленных one-file процессов текущий automation host оставляет `_MEI*`
  в `%TEMP%`; повторный запуск с повторно использованным PID может требовать новый процесс/сеанс.
  Чистая сборка и первые standalone CLI/GUI запуски прошли успешно.
- Предупреждение pip о несуществующем extra `typer[all]` не блокирует установку: нужные runtime
  зависимости установлены, но declaration можно упростить в следующем maintenance-релизе.

### Решение

P0 blockers не выявлены. Кандидат готов к созданию release tag и проверке tag-triggered
Build Release workflow.

# Expense Splitter Production Ready Progress Report

Дата: 2026-06-18
Этап: P0.0 — синхронизация локального проекта и GitHub  
Статус: завершено частично, без изменения бизнес-логики

## 1. Цель этапа

Цель P0.0 — привести локальное Git-состояние к безопасной точке перед production-ready доработкой, связать локальный проект с GitHub и определить источник истины для последующих P0-этапов.

На этом этапе не менялись:

- бизнес-логика;
- `pyproject.toml`;
- `src/expense_splitter/storage.py`;
- GitHub workflows;
- PyInstaller spec;
- тесты приложения.

## 2. Управляющие документы

| Документ | Фактический путь | Статус |
|---|---|---|
| Системный prompt | `docs/prompts/expense_splitter_prod_ready_system_prompt_v1.md` | найден |
| Пошаговая инструкция | `docs/prompts/expense_splitter_prod_ready_step_by_step_v1_ru.md` | найден |
| Аудит Codex | `docs/CODEX_AUDIT_REPORT_RU.md` | найден; не в `docs/audits/` |

## 3. Диагностика локального состояния

| Команда | Результат |
|---|---|
| `Get-Location` | `C:\Users\Rockaudit\LLM_CHAT\expense_splitter` |
| `git branch --show-current` | `main` |
| `git remote -v` до настройки | remote отсутствовал |
| `git log --oneline -10` до commit | `fatal: your current branch 'main' does not have any commits yet` |
| `git status --short` до commit | все проектные файлы были untracked |

## 4. Выполненные действия

| Действие | Статус | Комментарий |
|---|---|---|
| Настроен `origin` | OK | `https://github.com/VinogradovPV/Expense_Splitter.git` |
| Проверены ignored/generated artifacts | OK | `.venv/` и `__pycache__/` остались ignored |
| Создан первый safety commit | OK | `60812174607e2d412ba5c85dcf72c2004fd8fe17` |
| Выполнен `git fetch origin --prune` | OK | remote refs получены без merge/rebase |
| Проверен PR ref | OK | `refs/pull/1/head -> 6d72871734f223f00115111fdf02ab906625f38a` |

Первый commit:

```text
60812174607e2d412ba5c85dcf72c2004fd8fe17 chore: preserve local Expense Splitter project state
```

Commit выполнен с одноразовой локальной identity:

```text
user.name=Codex
user.email=codex@local
```

Причина: глобальная Git identity не настроена, менять глобальную конфигурацию пользователя на этапе P0.0 не стал.

## 5. Remote refs

| Ref | Commit | Значение |
|---|---|---|
| `origin/feature/expense-splitter-core` | `c6db6750ec511879dcdea79ef50a9cb6aee7c835` | базовая core-реализация |
| `origin/feature/installer-readme-launcher` | `6d72871734f223f00115111fdf02ab906625f38a` | более поздняя ветка с installer/docs/launcher |
| `refs/pull/1/head` | `6d72871734f223f00115111fdf02ab906625f38a` | PR №1 соответствует installer-ветке |
| `origin/HEAD` | `origin/feature/expense-splitter-core` | default remote HEAD указывает на core branch |

## 6. Источник истины

На конец P0.0 фактическая картина такая:

| Кандидат | Статус | Вывод |
|---|---|---|
| Локальная папка | сохранена safety commit | содержит prod-ready prompts и аудит Codex, структура проекта в корне |
| `origin/feature/expense-splitter-core` | remote base | более ранняя core-ветка |
| `origin/feature/installer-readme-launcher` | remote latest | содержит PR №1 и больше реализации, но проект находится во вложенной папке `expense-splitter/` |
| PR №1 | подтвержден | указывает на `feature/installer-readme-launcher` |

Рекомендация для следующих этапов: считать `origin/feature/installer-readme-launcher` функциональным remote baseline, но не переносить его структуру вслепую. Для production-ready работы безопаснее сохранить локальную структуру “проект в корне репозитория” и дальше синхронизировать содержимое осознанно, потому что:

- локальная копия уже содержит новые управляющие документы P0/P1;
- remote branch хранит проект внутри `expense-splitter/`, что ломает CI/workflow paths;
- P0.4 отдельно должен решить layout GitHub Actions и remote structure.

## 7. Безопасный план синхронизации

1. Не делать `reset --hard`, `clean -fd`, force push или массовые перемещения.
2. Создать рабочую ветку от текущего safety commit для production-ready доработки, например:

```powershell
git checkout -b prod-ready/p0
```

3. На P0.1 исправить только packaging/editable install.
4. На P0.2 исправить только storage/init и regression tests.
5. На P0.4 принять отдельное решение по remote layout:
   - вариант A: привести GitHub root к локальной структуре;
   - вариант B: оставить вложенную папку и явно настроить workflow `working-directory`.
6. До push не смешивать structural sync с исправлениями бизнес-логики.
7. Перед каждым commit проверять staged files на generated artifacts.

## 8. Оставшиеся риски

| Риск | Приоритет | Комментарий |
|---|---:|---|
| Локальная ветка `main` не связана upstream с remote | P0 | нормально для safety commit, решить перед push |
| Remote default HEAD указывает на core branch, а PR на installer branch | P0 | нужно выбрать ветку base для дальнейшего PR |
| Remote содержит проект во вложенной папке | P0 | причина будущего CI failure |
| Локальный `reports/` остался untracked | P2 | не коммитился как generated/user report |
| Git global identity не настроена | P2 | использована одноразовая identity для safety commit |

## 9. Команды

Ключевые команды этапа:

```powershell
git remote add origin https://github.com/VinogradovPV/Expense_Splitter.git
git add .github .gitignore README.md data docs packaging pyproject.toml scripts src tests
git -c user.name="Codex" -c user.email="codex@local" commit -m "chore: preserve local Expense Splitter project state"
git fetch origin --prune
git ls-remote origin "refs/pull/1/head"
```

Git/GitHub команды выполнялись outside sandbox.

## 10. Статус завершения P0.0

P0.0 выполнен: локальное состояние сохранено safety commit, remote `origin` настроен, remote branches получены, PR №1 подтвержден, источник истины и безопасный план синхронизации зафиксированы.

Следующий этап: P0.1 — исправление Python packaging и editable install.

## 11. P0.1 — Python packaging и editable install

Дата: 2026-06-18  
Статус: завершено; editable install, import, CLI help и тесты подтверждены.

### Цель

Исправить P0-дефект Python packaging: нерабочий build backend `setuptools.backends.legacy:build`, из-за которого `pip install -e ".[dev]"` ранее падал до сборки editable metadata.

### Изменения

| Файл | Изменение |
|---|---|
| `pyproject.toml` | `build-backend` заменен на `setuptools.build_meta` |

Бизнес-логика, `storage.py`, workflows, PyInstaller spec и тесты на этом этапе не менялись.

### Проверки

| Команда | Статус | Результат |
|---|---|---|
| `python -m pip install --upgrade pip setuptools wheel` | OK | пользователь вручную выполнил успешно; в `.venv` также доступны `setuptools 82.0.1`, `wheel 0.47.0`, `packaging 26.2` |
| `python -m pip install -e ".[dev]"` | OK | пользователь вручную выполнил успешно; `.venv` содержит runtime/dev dependencies |
| `.\.venv\Scripts\python.exe -m pip install --no-deps -e "."` | OK outside sandbox | editable wheel собран и установлен |
| `.\.venv\Scripts\python.exe -c "import expense_splitter; print(expense_splitter.__file__)"` | OK | импорт идет из `src/expense_splitter/__init__.py` |
| `.\.venv\Scripts\python.exe -m pip show expense-splitter` | OK | package metadata видит editable project location и dependencies |
| `.\.venv\Scripts\expense-splitter.exe --help` | OK | CLI entry point работает |
| `.\.venv\Scripts\python.exe -m expense_splitter --help` | OK | module entry point работает |
| `.\.venv\Scripts\python.exe -m pytest tests -v` | OK outside sandbox | `23 passed in 0.15s` |

### Вывод

Изначальный P0.1-дефект build backend исправлен: editable build больше не падает на `Cannot import 'setuptools.backends.legacy'`. Package discovery из `src` подтвержден, entry points `expense-splitter` и `python -m expense_splitter` работают, тестовый набор проходит.

Важное замечание: первый запуск тестов внутри sandbox падал на `PermissionError` к `C:\Users\Rockaudit\AppData\Local\Temp\pytest-of-Rockaudit`. Повтор outside sandbox прошел успешно.

### Git/GitHub

Git/GitHub-команды выполнялись outside sandbox. Локальный commit P0.4 создан с сообщением `fix: align GitHub Actions with project layout`. Push на этом этапе не выполнялся.

## 13. P0.3 — Data safety: atomic write, backup, corrupted YAML

Дата: 2026-06-18  
Статус: завершено.

### Цель

Добавить минимальную защиту пользовательских YAML-данных:

- atomic write через временный файл и `os.replace`;
- timestamped `.bak` copy перед заменой существующего YAML;
- понятную ошибку при поврежденном YAML;
- CLI-обработку storage errors без traceback.

### Изменения

| Файл | Изменение |
|---|---|
| `src/expense_splitter/storage.py` | добавлен `StorageError`, дружелюбная обработка YAML/OSError, backup перед заменой существующего файла, atomic write через temp file + `os.replace` |
| `src/expense_splitter/cli.py` | команды перехватывают `StorageError` и показывают `Data error in <path>: ...` без stack trace |
| `tests/test_storage.py` | добавлены тесты backup creation, atomic write failure и corrupted YAML |
| `tests/test_cli.py` | добавлен тест на дружелюбную CLI-ошибку при поврежденном `purchases.yaml` |
| `docs/Troubleshooting.md` | добавлено описание `Data error in ...` и timestamped `.bak` файлов |

Сложная миграционная система и новые пользовательские backup/restore команды на этом этапе не добавлялись; они остаются для P1.1.

### Проверки

| Команда | Статус | Результат |
|---|---|---|
| `.\.venv\Scripts\python.exe -m py_compile src\expense_splitter\storage.py src\expense_splitter\cli.py tests\test_storage.py tests\test_cli.py` | OK | синтаксис корректен |
| `.\.venv\Scripts\python.exe -m pytest tests/test_storage.py tests/test_cli.py -v` | OK outside sandbox | `16 passed in 0.34s` |
| `.\.venv\Scripts\python.exe -m pytest tests -v` | OK outside sandbox | `31 passed in 0.35s` |
| `.\.venv\Scripts\python.exe -m compileall -q src tests` | OK | compileall прошел |

Первый запуск pytest внутри sandbox был заблокирован `PermissionError` при создании pytest temp directory. Повтор outside sandbox прошел успешно.

### Вывод

P0.3 закрыт: YAML-записи теперь выполняются атомарно, существующий YAML получает timestamped `.bak` перед заменой, поврежденный YAML превращается в контролируемый `StorageError`, а CLI показывает пользователю путь к проблемному файлу без traceback.

### Git/GitHub

Git/GitHub-команды выполнялись outside sandbox. Push на этом этапе не выполнялся.

## 16. P0.6 — GitHub push, CI verification, UTF-8/mojibake baseline

Дата: 2026-06-18  
Статус: локальные проверки выполнены; branch подготовлен к push.

### Цель

Зафиксировать P0 production-ready baseline, добавить UTF-8/mojibake guard, перейти на рабочую ветку `prod-ready/p0-p1`, отправить изменения в GitHub и проверить GitHub Actions.

### Изменения

| Файл | Изменение |
|---|---|
| `scripts/qa/check_text_encoding.py` | Добавлен UTF-8/mojibake checker для tracked text baseline; generated/ignored директории пропускаются |
| `docs/prompts/expense_splitter_prod_ready_system_prompt_v5.md` | Добавлен v5 управляющий документ; исправлены признаки mojibake в тексте |
| `docs/prompts/expense_splitter_prod_ready_step_by_step_v5_ru.md` | Добавлен v5 пошаговый документ |
| `docs/reports/prod_ready_progress_report.md` | Добавлен отчет P0.6 |

Старые v1 prompt-файлы заменены v5-документами. Generated artifacts не staging/commit.

### Проверки

| Команда | Статус | Результат |
|---|---|---|
| `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"` | OK outside sandbox | editable install успешно завершен |
| `.\.venv\Scripts\python.exe -m pytest tests -v` | OK outside sandbox | `32 passed in 0.40s` |
| `.\.venv\Scripts\python.exe -m compileall -q src tests` | OK outside sandbox | compileall прошел |
| `.\.venv\Scripts\expense-splitter.exe --help` | OK outside sandbox | CLI help отображается |
| `.\.venv\Scripts\expense-splitter-launcher.exe --help` | OK outside sandbox | launcher help отображается |
| `.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py` | OK outside sandbox | UTF-8/mojibake check passed |

Перед проверками включались `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`, UTF-8 console output и `chcp 65001`.

### Generated artifacts

Ignored/generated artifacts остались вне staged scope: `.venv/`, `.pytest_cache/`, `build/`, `dist/`, `__pycache__/`, `*.egg-info/`, untracked `reports/`.

### Git/GitHub

Рабочая ветка: `prod-ready/p0-p1`.  
Commit P0.6: `df48ffd chore: publish P0 production-ready baseline`.  
Push выполнен в `origin/prod-ready/p0-p1`.

Первый GitHub Actions run:

```text
27754823573 — CI — failure
```

Причина: Linux runner/Rich переносил длинный путь `purchases.yaml` внутри строки ошибки как `purchases.ya\nml`, из-за чего падал тест `tests/test_cli.py::test_corrupted_yaml_shows_friendly_error`.

Follow-up fix: `handle_storage_error()` переведен с Rich markup на plain `typer.echo()`, чтобы пользовательская ошибка data safety не ломала путь переносом строки на CI.

Локальные проверки follow-up fix:

| Команда | Статус | Результат |
|---|---|---|
| `.\.venv\Scripts\python.exe -m pytest tests\test_cli.py::test_corrupted_yaml_shows_friendly_error -v` | OK outside sandbox | `1 passed` |
| `.\.venv\Scripts\python.exe -m pytest tests -v` | OK outside sandbox | `32 passed in 0.34s` |
| `.\.venv\Scripts\python.exe -m compileall -q src tests` | OK outside sandbox | compileall прошел |
| `.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py` | OK outside sandbox | UTF-8/mojibake check passed |

Follow-up commit:

```text
b8de1b4 fix: stabilize storage error output for CI
```

Повторный GitHub Actions run:

```text
27756101936 — CI — success
```

Итог P0.6: ветка `prod-ready/p0-p1` запушена, P0 baseline опубликован, GitHub Actions проверен, UTF-8/mojibake guard добавлен и проходит, generated artifacts не staged.

## 15. P0.5 — PyInstaller packaging

Дата: 2026-06-18  
Статус: завершено локально; Windows-сборка проверена.

### Цель

Исправить P0-дефект PyInstaller packaging: `.spec` использовал неверные относительные пути, build scripts не имели единого root/output поведения, а пользовательская рабочая `data/` директория не должна была встраиваться в standalone executables как packaged data.

### Изменения

| Файл | Изменение |
|---|---|
| `packaging/expense_splitter.spec` | Пути вычисляются от `packaging/` к project root и `src/`; удалены неверные `../../src` и bundled `data/`; собираются два exe: `expense-splitter` и `expense-splitter-launcher`; UPX управляется через `PYINSTALLER_NO_UPX` |
| `scripts/build-windows.ps1` | Скрипт работает от project root, ставит `.[dev]`, запускает PyInstaller со spec, пишет generated output в root `build/` и `dist/`, поддерживает `-NoUpx` без запрещенного `--noupx` при `.spec` |
| `scripts/build-unix.sh` | Приведен к той же root-логике: `.venv`, editable dev install, root `build/` и `dist/`, `--noupx` через env |
| `.github/workflows/build-release.yml` | Artifact paths обновлены с `packaging/dist/*` на фактический `dist/*` |
| `docs/PACKAGING.md` | Обновлен под фактические команды и root-layout |
| `src/expense_splitter/launcher.py` | Добавлен минимальный `--help`/`-h` guard для packaged smoke test без запуска интерактивного меню |
| `tests/test_launcher.py` | Добавлен regression test, что launcher `--help` не стартует меню |
| `docs/reports/prod_ready_progress_report.md` | Добавлен отчет по P0.5 |

Бизнес-логика расчетов и storage на этом этапе не менялись.

### Проверки

| Команда | Статус | Результат |
|---|---|---|
| `.\.venv\Scripts\python.exe -m py_compile src\expense_splitter\cli.py src\expense_splitter\launcher.py packaging\expense_splitter.spec` | OK | синтаксис корректен |
| `.\.venv\Scripts\python.exe -m compileall -q src` | OK | compileall прошел |
| `.\.venv\Scripts\python.exe -m PyInstaller --version` | OK | `6.21.0` |
| PowerShell parser для `scripts\build-windows.ps1` | OK | синтаксис скрипта корректен |
| `.\.venv\Scripts\python.exe -m pytest tests\test_launcher.py -v` | OK outside sandbox | `4 passed` |
| `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build-windows.ps1 -NoUpx` | OK outside sandbox | созданы `dist\expense-splitter.exe` и `dist\expense-splitter-launcher.exe` |
| `.\dist\expense-splitter.exe --help` | OK outside sandbox | CLI help отображается |
| `.\dist\expense-splitter-launcher.exe --help` | OK outside sandbox | launcher help отображается без запуска меню |
| `.\.venv\Scripts\python.exe -m pytest tests -v` | OK outside sandbox | `32 passed in 0.36s` |

Первый запуск build script без `-ExecutionPolicy Bypass` был остановлен локальной PowerShell execution policy для неподписанных скриптов. Повтор с `-ExecutionPolicy Bypass` прошел успешно.

### Generated artifacts

После проверочной сборки появились ignored artifacts: `dist/`, `build/`, `src/expense_splitter.egg-info/`, `__pycache__/`, `.pytest_cache/`. Они не должны staging/commit.

### Git/GitHub

Git/GitHub-команды выполнялись outside sandbox. Изменения P0.5 подготовлены для локального commit с сообщением `fix: repair PyInstaller packaging paths`. Push на этом этапе не выполнялся.

## 12. P0.2 — Исправление storage/init и тестов данных

Дата: 2026-06-18  
Статус: завершено.

### Цель

Исправить P0-дефект `initialize_data_files()`: при первичной инициализации `participants.yaml` терял список участников, потому что `save_groups()` перезаписывал файл после `save_participants()`.

### Изменения

| Файл | Изменение |
|---|---|
| `src/expense_splitter/storage.py` | `save_participants()` и `save_groups()` теперь обновляют только свою секцию YAML и сохраняют остальные ключи |
| `tests/test_storage.py` | добавлены regression tests для `initialize_data_files()`, сохранения participants/groups и защиты от перезаписи существующих данных |
| `tests/test_cli.py` | `test_init_command` теперь проверяет, что CLI `init` создает не только файлы, но и обе секции: participants и groups |

Бизнес-логика расчетов, `pyproject.toml`, workflows и PyInstaller spec на этом этапе не менялись.

### Проверки

| Команда | Статус | Результат |
|---|---|---|
| `.\.venv\Scripts\python.exe -m pytest tests/test_storage.py tests/test_cli.py -v` | OK outside sandbox | `12 passed in 0.16s` |
| `.\.venv\Scripts\python.exe -m pytest tests -v` | OK outside sandbox | `27 passed in 0.17s` |

Первый запуск pytest внутри sandbox был заблокирован `PermissionError` при создании pytest temp directory. Повтор outside sandbox прошел успешно.

### Вывод

P0-дефект перезаписи `participants.yaml` исправлен. После `init` файл `participants.yaml` содержит обе секции:

- `participants`;
- `groups`.

Повторная инициализация не перезаписывает существующие пользовательские participants, groups и purchases.

### Git/GitHub

Git/GitHub-команды выполнялись outside sandbox. Push на этом этапе не выполнялся.
## 14. P0.4 — GitHub Actions и структура remote

Дата: 2026-06-18  
Статус: выполнено локально; GitHub Actions на remote не запускались, потому что push не выполнялся.

### Цель

Исправить P0-дефект расхождения структуры проекта и GitHub Actions. В remote-ветке PR №1 проект был расположен во вложенной папке `expense-splitter/`, а локальная production-ready работа после P0.0 ведется в плоской структуре, где `pyproject.toml`, `src/`, `tests/`, `scripts/` и `.github/` находятся в корне репозитория.

### Принятое решение

Выбрана структура "проект в корне репозитория" (`working-directory: .`).

Массовые перемещения файлов не выполнялись. Код приложения, `pyproject.toml`, `storage.py`, тесты, PyInstaller spec и build scripts на этом этапе не менялись.

### Изменения

| Файл | Изменение |
|---|---|
| `.github/workflows/ci.yml` | Создан root-based CI workflow: checkout, Python 3.11, editable install, pytest, compileall, проверка `expense-splitter --help` |
| `.github/workflows/build-release.yml` | Workflow выровнен под корень репозитория: `working-directory: .`, install через `python -m pip install -e ".[dev]"`, pytest/compileall/help checks, artifact paths заменены с `expense-splitter/dist/` на `packaging/dist/*`, release upload переведен на `softprops/action-gh-release@v2` |
| `README.md` | Добавлена короткая заметка о целевой root-структуре GitHub Actions |
| `docs/reports/prod_ready_progress_report.md` | Добавлен отчет по P0.4 |

### Проверки

| Команда | Статус | Результат |
|---|---|---|
| `.\.venv\Scripts\python.exe -c "... yaml.safe_load ..."` | OK | оба workflow YAML-файла разобраны без ошибки |
| `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"` | OK outside sandbox | editable install успешно завершен |
| `.\.venv\Scripts\python.exe -m pytest tests -v` | OK outside sandbox | `31 passed in 0.35s` |
| `.\.venv\Scripts\python.exe -m compileall -q src tests` | OK | compileall прошел |
| `.\.venv\Scripts\expense-splitter.exe --help` | OK | CLI entry point доступен |

Первый запуск `pip install -e ".[dev]"` внутри sandbox был заблокирован `PermissionError` в `C:\Users\Rockaudit\AppData\Local\Temp`; повтор outside sandbox прошел успешно.

GitHub Actions на стороне GitHub не проверялись в этом этапе, так как push не выполнялся.

### Ограничения

Release workflow теперь использует правильную root-структуру и правильные artifact paths для текущих build scripts, но фактическая PyInstaller-сборка остается предметом P0.5. На P0.4 намеренно не исправлялись `packaging/expense_splitter.spec` и build scripts.

### Git/GitHub

Git/GitHub-команды выполнялись outside sandbox. Push на этом этапе не выполнялся.
## P1.0 — Data schema v2 и purchase_name

Дата: 2026-06-18
Статус: выполнено, опубликовано в GitHub, CI зеленый.

### Цель

Добавить каноническое поле `purchase_name` / «Наименование покупки» без поломки старых пользовательских `purchases.yaml`, где имя покупки хранилось в legacy-поле `title`.

### Изменения

| Файл | Изменение |
|---|---|
| `src/expense_splitter/models.py` | `Purchase` переведен на поле `purchase_name`; добавлен дефолт `н/д` и read/write property `title` как legacy alias для старых code paths |
| `src/expense_splitter/storage.py` | `load_purchases()` мигрирует `title` в `purchase_name`; пустые/отсутствующие имена становятся `н/д`; `save_purchases()` явно пишет v2-схему без `title` |
| `src/expense_splitter/defaults.py` | Примерные покупки переведены на `purchase_name` |
| `src/expense_splitter/cli.py` | Аргумент добавления и таблица списка используют «Наименование покупки»; пустой ввод нормализуется в `н/д` |
| `src/expense_splitter/launcher.py` | Интерактивный ввод использует «Наименование покупки» и нормализует пустое значение в `н/д` |
| `src/expense_splitter/reporting.py` | Markdown-отчет выводит каноническое поле `purchase_name` |
| `tests/test_storage.py` | Добавлены regression tests для legacy `title`, отсутствующего имени и сохранения без `title` |
| `tests/test_cli.py` | Обновлены проверки `purchase_name`; добавлен тест пустого имени |
| `tests/test_launcher.py` | Добавлен тест пустого имени в интерактивном launcher |
| `docs/DATA_SCHEMA.md` | Добавлено описание YAML-схемы v2 и правил совместимости v1 |

### Проверки

Планируемые команды P1.0:

| Команда | Статус | Результат |
|---|---|---|
| `.\.venv\Scripts\python.exe -m py_compile src\expense_splitter\models.py src\expense_splitter\storage.py src\expense_splitter\cli.py src\expense_splitter\launcher.py` | OK outside sandbox | синтаксис корректен |
| `.\.venv\Scripts\python.exe -m pytest tests\test_storage.py tests\test_cli.py tests\test_launcher.py -v` | OK outside sandbox | `25 passed in 0.42s` |
| `.\.venv\Scripts\python.exe -m pytest tests -v` | OK outside sandbox | `37 passed in 0.40s` |
| `.\.venv\Scripts\python.exe -m compileall -q src tests` | OK outside sandbox | compileall прошел |
| `.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py` | OK outside sandbox | `Text encoding check passed: UTF-8 files have no mojibake markers.` |

### Git/GitHub

Staging P1.0 проверен: generated artifacts (`reports/`, `.pytest_cache/`, `__pycache__/`, `.ruff_cache/`, `dist/`, `build/`, `*.egg-info`, backup-файлы) не добавлены.

Commit:

```text
9e21f44 feat: add purchase_name data schema compatibility
```

Push выполнен в ветку `prod-ready/p0-p1`.

GitHub Actions:

| Workflow | Run | Status | Результат |
|---|---|---|---|
| `CI` | `27757240825` | completed | success |

## P1.A.0 — Единая палитра аналитических графиков

Дата: 2026-06-18
Статус: выполнено локально; проверки прошли.

### Цель

Добавить собственную единую палитру Expense Splitter для будущих аналитических PNG-графиков, чтобы отчеты не зависели от дефолтных цветов matplotlib и имели стабильные color strategies.

### Изменения

| Файл | Изменение |
|---|---|
| `src/expense_splitter/visual/__init__.py` | Создан пакет визуальных helper-модулей |
| `src/expense_splitter/visual/palette.py` | Добавлены палитры, Expense Splitter specific maps, metadata constants и helper-функции для stable maps, периодов и статуса баланса |
| `tests/test_palette.py` | Добавлены проверки HEX-цветов, стабильности mapping, циклического повторения палитры, периодов, статусов баланса и metadata constants |
| `docs/ANALYTICS.md` | Зафиксированы палитра, версия и стратегии цвета для будущих PNG-графиков |
| `docs/reports/prod_ready_progress_report.md` | Добавлен отчет по P1.A.0 |

### Проверки

| Команда | Статус | Результат |
|---|---|---|
| `.\.venv\Scripts\python.exe -m py_compile src\expense_splitter\visual\palette.py tests\test_palette.py` | OK outside sandbox | синтаксис корректен |
| `.\.venv\Scripts\python.exe -m pytest tests\test_palette.py -v` | OK outside sandbox | `9 passed in 0.04s` |
| `.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py` | OK outside sandbox | `Text encoding check passed: UTF-8 files have no mojibake markers.` |

### Git/GitHub

Generated artifacts (`reports/`, `.pytest_cache/`, `__pycache__/`, `.ruff_cache/`, `dist/`, `build/`, `*.egg-info`, backup-файлы) не должны попадать в staging. Push в инструкции P1.A.0 не указан.

## P1.A.1 — Analytics core: периодные агрегации

Дата: 2026-06-18
Статус: завершено пользователем; проверки, commit и push выполнены успешно.

### Цель

Добавить слой периодной аналитики за месяц, квартал и год без генерации Markdown/CSV/PNG отчетов на этом подэтапе.

### Изменения

| Файл | Изменение |
|---|---|
| `src/expense_splitter/analytics.py` | Добавлены `PeriodSpec`, `AnalyticsDataset`, фильтрация покупок по периоду, сводка, агрегации по категориям/плательщикам/участникам, top purchases и warnings |
| `tests/test_analytics.py` | Добавлены regression tests для периодов, undated purchases, Decimal-агрегаций, категории `Без категории`, top purchases, warnings, balances и settlements |
| `docs/ANALYTICS.md` | Добавлен раздел Analytics core P1.A.1 |
| `docs/reports/prod_ready_progress_report.md` | Добавлен отчет по P1.A.1 |

### Проверки

| Команда | Статус | Результат |
|---|---|---|
| Проверки P1.A.1 | OK | пользователь подтвердил успешное прохождение всех тестов |

### Git/GitHub

Commit `da4dbdc feat: add period analytics core` создан и отправлен пользователем.

## P1.A.2 — Analytics reports: Markdown + CSV + PNG

Дата: 2026-06-18  
Статус: завершено; commit и push выполнены, GitHub Actions успешно пройдены.

### Изменения

| Файл/область | Изменение |
|---|---|
| `analytics_reporting.py` | Markdown, 9 CSV-таблиц, metadata.json, единый output layout |
| `analytics_charts.py` | 6 headless PNG-графиков через matplotlib `Agg`, палитра P1.A.0, warnings при отсутствии данных |
| CLI/launcher | Добавлена аналитика за month/quarter/year и форматы markdown/csv/png/all |
| `pyproject.toml` | Добавлена runtime dependency `matplotlib>=3.8` |
| tests | Добавлены проверки структуры отчетов, CSV encoding/Decimal, PNG и empty-data behavior |
| docs | Обновлены README и `docs/ANALYTICS.md` |

### Проверки

| Проверка | Статус | Результат |
|---|---|---|
| Editable install | OK | matplotlib 3.11.0 установлен |
| Focused pytest | OK | `33 passed` после добавления CLI regression tests |
| Полный pytest | OK | `65 passed in 1.75s` |
| Ruff | OK | `All checks passed!` для затронутых Python-файлов |
| Compileall | OK | `python -m compileall -q src tests` |
| CLI month/quarter/year | OK | созданы каталоги `2026-06`, `2026-Q2`, `2026` |
| Empty-data warnings | OK | по 6 `chart_no_data`, генерация не падает |
| Encoding | OK | UTF-8 files have no mojibake markers |

Generated `reports/analytics/` добавлен в `.gitignore` и не должен попадать в staging.

### Git/GitHub

- Feature commit: `d707f60 feat: add analytics reports with tables and charts`.
- Ветка: `prod-ready/p0-p1`.
- Push: `origin/prod-ready/p0-p1`, успешно.
- GitHub Actions CI run `27771714140`: success, job `test` завершен за 24 секунды.
- CI annotation о переходе GitHub-hosted actions с Node.js 20 на Node.js 24 не блокирует этап и относится к будущему обновлению версий actions.

## P1.A.3 — Документация аналитики и пользовательский smoke-test

Дата: 2026-06-19
Статус: выполнено локально; готово к commit.

### Цель

Довести пользовательскую документацию по аналитике до понятного состояния и провести smoke-test на Windows.

### Изменения

| Файл | Изменение |
|---|---|
| `README.md` | Уточнен пользовательский раздел аналитики за период; убран старый placeholder-шаблон |
| `docs/ANALYTICS.md` | Добавлен пользовательский workflow P1.A.3 и ожидаемый результат smoke-test |
| `docs/USER_GUIDE.md` | Добавлено руководство пользователя по аналитике, таблицам, графикам, `purchase_name`, `н/д`, HTML/XLSX P2 и generated reports |
| `docs/Troubleshooting.md` | Добавлены подсказки по mojibake, отсутствующим PNG и удалению generated analytics reports |
| `docs/reports/prod_ready_progress_report.md` | Зафиксирован этап P1.A.3 |

### Проверки

| Команда / проверка | Статус | Результат |
|---|---|---|
| `.\.venv\Scripts\expense-splitter.exe analytics --period month --year 2026 --month 6 --format all` | OK outside sandbox | создан `reports\analytics\2026\2026-06` |
| Ручная проверка пользователя | OK | таблицы и отчеты строятся; PNG не построены из-за отсутствия данных за период |
| `reports\analytics\2026\2026-06\tables\warnings.csv` | OK | 6 строк `chart_no_data` для обязательных PNG |
| Placeholder scan | OK | пользовательские docs не содержат `TODO`, `PLACEHOLDER`, `passed/failed`, `- ...` |
| `.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py` | OK outside sandbox | UTF-8 files have no mojibake markers |
| `git status --short --ignored` | OK outside sandbox | generated reports остаются ignored и не должны попасть в staging |
| `git diff --check` | OK outside sandbox | whitespace errors не найдены |

### Ограничения

HTML dashboard и XLSX report остаются P2. Generated reports в `reports/analytics/` не коммитятся.
## P2.S.1 — Settlement periods foundation

Дата: 2026-06-19
Статус: в работе; локальная реализация и проверки выполняются.

### Цель

Добавить безопасное закрытие плавающего периода взаиморасчетов без удаления покупок и без переписывания истории.

### Изменения

| Файл/область | Изменение |
|---|---|
| `src/expense_splitter/models.py` | Добавлены поля `settled`, `settlement_period_id` у `Purchase` и модель `SettlementPeriod` |
| `src/expense_splitter/storage.py` | Добавлены load/save для `settlement_periods.yaml`, schema_version, backward compatibility старых покупок, init нового YAML |
| `src/expense_splitter/settlement_periods.py` | Добавлена доменная логика preview/close/list/show/reopen и scope-фильтрация |
| `src/expense_splitter/cli.py` | Добавлены команды `settlement-period preview/close/list/show/reopen`; `balances` и `settle` получили `--scope` и `--settlement-period` |
| `src/expense_splitter/reporting.py` | Markdown-отчет показывает settlement status покупки |
| `data/settlement_periods.yaml` | Добавлен пустой пользовательский YAML-файл периодов |
| `tests/test_settlement_periods.py` | Добавлены тесты legacy compatibility, preview без мутации, close без удаления, scope, storage round-trip, reopen и CLI |
| `docs/SETTLEMENT_PERIODS.md`, `README.md`, `docs/USER_GUIDE.md` | Добавлена документация по периодам взаиморасчетов |
| `scripts/qa/check_text_encoding.py` | P2 prompt добавлен в allow-list строк с примерами mojibake-маркеров |

### Проверки

| Команда / проверка | Статус | Результат |
|---|---|---|
| `.\.venv\Scripts\python.exe -m py_compile src\expense_splitter\settlement_periods.py src\expense_splitter\storage.py src\expense_splitter\cli.py` | OK outside sandbox | Синтаксис корректен |
| `.\.venv\Scripts\python.exe -m pytest tests\test_settlement_periods.py -v` | OK outside sandbox | `7 passed` |
| Полный pytest | OK outside sandbox | `72 passed in 1.78s` |
| Compileall | OK outside sandbox | `python -m compileall -q src tests` |
| Encoding | OK outside sandbox | UTF-8 files have no mojibake markers |
| CLI smoke | OK outside sandbox | Изолированная директория `.tmp\p2_s1_smoke\data`; close не менял реальные пользовательские YAML |
| Ruff по затронутым файлам | OK outside sandbox | `All checks passed!` |

### Git/GitHub

- Commit hash: текущий `HEAD` после commit `feat: add settlement periods`; точный hash зафиксирован в финальном ответе этапа.
- Push: `origin/prod-ready/p0-p1`, успешно.
- GitHub Actions: CI run `27811016567`, success.
- Generated artifacts: не должны попадать в staging.
