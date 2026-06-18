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
