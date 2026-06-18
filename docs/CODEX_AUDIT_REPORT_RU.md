# Уточненный аудит Expense Splitter

Дата аудита: 2026-06-18  
Аудитор: Codex  
Проект: `expense-splitter`  
GitHub: https://github.com/VinogradovPV/Expense_Splitter

## 1. Executive Summary

Проект нельзя считать production-ready. GitHub-репозиторий действительно создан, и Pull Request №1 подтверждается через `refs/pull/1/head`, однако отчет Manus завышает готовность проекта: ключевые проверки не воспроизводятся в текущей среде, установка пакета ломается, данные инициализируются некорректно, release workflow и PyInstaller packaging почти наверняка не соберутся без исправлений.

Главный вывод: проект находится на уровне рабочего прототипа с частично готовой структурой, но требует P0/P1 исправлений перед первым релизом.

## 2. Источники аудита

| Источник | Статус | Что проверено |
|---|---:|---|
| Локальная папка `C:\Users\Rockaudit\LLM_CHAT\expense_splitter` | Проверена | Структура, код, тесты, scripts, packaging, docs |
| Локальный отчет Manus `docs/Report_ Expense Splitter` | Проверен | Заявления о тестах, GitHub, PR, готовности |
| GitHub `VinogradovPV/Expense_Splitter` | Проверен через `git ls-remote` и clone | Ветки, PR ref, содержимое ветки `feature/installer-readme-launcher` |

Открытие GitHub через web-инструмент вернуло 403/Cloudflare, поэтому содержимое проверялось через `git ls-remote` и временный read-only clone.

## 3. GitHub Readiness

| Проверка | Факт | Оценка |
|---|---|---|
| Remote repository | Есть: `VinogradovPV/Expense_Splitter` | OK |
| Ветки | Есть `feature/expense-splitter-core` и `feature/installer-readme-launcher` | PARTIAL |
| `main/master` в remote | В `ls-remote --heads --tags` не обнаружены | RISK |
| Pull Request №1 | Подтвержден: `refs/pull/1/head -> 6d728717...` | OK |
| Tags/releases | Tags не обнаружены | MISSING |
| Локальный remote | В текущей локальной папке не настроен | MISSING |
| Локальный git status | Все файлы остаются untracked, коммитов в локальной `main` нет | BROKEN |
| Структура remote | Проект лежит во вложенной папке `expense-splitter/` | RISK |

Важно: локальная копия не синхронизирована с GitHub. В локальной папке нет remote, нет commits, все файлы untracked. Это не соответствует отчету Manus о завершенном push/PR как локальному состоянию проекта.

## 4. Проверка отчета Manus

| Заявление Manus | Факт аудита | Вердикт |
|---|---|---|
| "Проект полностью соответствует системному промпту" | Не соответствует: есть P0-дефекты установки, storage, packaging, docs | Не подтверждено |
| "23 теста успешно прошли" | В текущей среде `pytest` отсутствует; `pip install -e .[dev]` не проходит | Не воспроизведено |
| "Код отправлен в удаленный репозиторий" | Remote существует, ветки загружены | Подтверждено частично |
| "Создан Pull Request №1" | `refs/pull/1/head` существует | Подтверждено |
| "Проект завершен" | Нет: installation, data safety, release workflow и docs требуют исправлений | Опровергнуто |

## 5. Критические находки

| ID | Приоритет | Область | Проблема | Файл |
|---|---:|---|---|---|
| F-01 | P0 | Packaging | `build-backend = "setuptools.backends.legacy:build"` не импортируется в текущей среде: `Cannot import 'setuptools.backends.legacy'`. Из-за этого editable install не проходит. | `pyproject.toml:3` |
| F-02 | P0 | Storage | `initialize_data_files()` сначала пишет participants, затем `save_groups()` перезаписывает тот же `participants.yaml`. В remote `data/participants.yaml` фактически пуст, а данные ушли/остались в `purchases.yaml`. | `src/expense_splitter/storage.py:98-99` |
| F-03 | P0 | CLI/tests | `expense-splitter --help` не работает без успешной установки: command not found. `python -m expense_splitter --help` падает без `typer`. | `pyproject.toml`, `cli.py` |
| F-04 | P0 | GitHub Actions | Remote проект лежит во вложенной папке `expense-splitter/`, но workflow запускает `pip install -e .[dev]` из repo root. В таком виде CI/release likely fail. | `.github/workflows/*.yml` |
| F-05 | P0 | PyInstaller | Spec использует пути `../../src` и `../../data` при запуске из `packaging`; для фактической структуры это указывает за пределы проекта. | `packaging/expense_splitter.spec` |
| F-06 | P1 | Data safety | Нет atomic write, backup/restore, schema version, validate-data; поврежденный YAML не обрабатывается дружелюбно. | `storage.py`, `cli.py` |
| F-07 | P1 | Расчеты | Остаток округления всегда получает последний участник списка, что может давать систематическое смещение. | `calculator.py:29-34` |
| F-08 | P1 | UX launcher | Launcher не имеет `--help`, полностью интерактивен, не поддерживает управление участниками/группами и редактирование/удаление покупок. | `launcher.py` |
| F-09 | P1 | Документация | README содержит placeholders `YOUR_GITHUB_USERNAME`; локально docs имеют другой регистр имен, remote исправлен частично. | `README.md`, `docs/*.md` |
| F-10 | P2 | Tests | `tests/test_storage.py` в remote пустой; критичная storage-регрессия не покрыта тестом. | `tests/test_storage.py` |

## 6. Проверки, выполненные Codex

| Команда | Результат |
|---|---|
| `git remote -v` локально | remote отсутствует |
| `git status --short` локально | все проектные файлы untracked |
| `git log --oneline -10` локально | нет коммитов в `main` |
| `git ls-remote --heads --tags GitHub` | найдены только две feature-ветки |
| `git ls-remote refs/pull/*/head` | найден `refs/pull/1/head` |
| `git clone --depth 1 --branch feature/installer-readme-launcher` | успешно во временную папку |
| `python -m pip install -e .[dev]` | неуспешно; sandbox Temp permission, вне sandbox ранее: `Cannot import setuptools.backends.legacy` |
| `python -m pytest tests -v` | не запущено: `No module named pytest` |
| `python -m py_compile ...` | основные модули компилируются |
| `expense-splitter --help` | command not found |

## 7. Оценка расчетной надежности

Статус: **acceptable after significant fixes**.

Плюсы: используется `Decimal`, есть базовая валидация положительной суммы и непустых participants, баланс net сохраняется на простом сценарии. Минусы: остаток округления всегда назначается последнему участнику; нет явной политики fairness; нет защиты от дублей участников; greedy settlement может быть приемлемым для типовой задачи, но не доказан тестами на минимальность для всех случаев; storage-дефект подрывает надежность расчетов на реальных данных.

## 8. Production-ready Gap Analysis

| Область | Статус | Риск | Что сделать | Приоритет |
|---|---|---|---|---:|
| Python package | BROKEN | Нельзя установить пакет | заменить backend на `setuptools.build_meta`, проверить install | P0 |
| Storage | BROKEN | Потеря/искажение users/groups | сохранять participants и groups в одном YAML или разнести файлы | P0 |
| CI/release | BROKEN | GitHub Actions не соберет проект | поправить root path или убрать вложенную папку | P0 |
| PyInstaller | BROKEN | Standalone build невалиден | исправить spec paths, проверить build без включения user data | P0 |
| Tests | PARTIAL | Зеленый suite не ловит P0 баги | добавить storage/install/CLI/packaging tests | P1 |
| CLI | PARTIAL | UX ломается без install, нет validate/backup | добавить validate-data, backup/restore, понятные errors | P1 |
| Launcher | PARTIAL | Недостаточно операций для обычного пользователя | добавить CRUD participants/groups/purchases | P1 |
| Docs | PARTIAL | Инструкции ведут на placeholders | заменить GitHub links, привести имена файлов и факты | P1 |
| GitHub release | MISSING | Нет tags/releases | настроить release strategy | P2 |
| Data safety | MISSING | Риск потери данных | atomic write, backups, schema version | P0/P1 |

## 9. Рекомендуемый P0/P1 план

### P0

1. Исправить `pyproject.toml`: заменить build backend и проверить `pip install -e .[dev]`.
2. Исправить `initialize_data_files()`: не перезаписывать `participants.yaml`; добавить тест, который проверяет наличие и participants, и groups после `init`.
3. Решить структуру GitHub repo: либо перенести содержимое `expense-splitter/` в root, либо обновить все workflow paths.
4. Исправить PyInstaller spec paths и artifact paths в GitHub Actions.
5. Добавить защиту пользовательских данных: atomic write и backup перед изменениями.

### P1

1. Добавить `validate-data`, `backup`, `restore`.
2. Добавить CRUD participants/groups/purchases в CLI и launcher.
3. Исправить документацию: убрать placeholders, привести актуальные команды, указать статус remote/PR/release.
4. Добавить тесты storage, CLI help, install smoke, corrupted YAML, duplicate participants, invalid date, unknown payer/participant.
5. Улучшить округление: явно определить fair policy распределения копеек.

## 10. Итог

Отчет Manus полезен как краткое описание намерений и проделанной работы, но не может использоваться как release-quality отчет: он содержит неподтвержденные или завышенные заявления о тестах, полной готовности и соответствии требованиям. GitHub-репозиторий и PR действительно существуют, однако текущий проект требует существенной стабилизации перед production-ready состоянием.

