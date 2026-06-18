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
