# Expense Splitter — P3 release and post-release hardening step-by-step v1

## 0. Контекст и цель P3

Проект `expense_splitter` прошел P2 release quality gate и находится в состоянии production-ready candidate. Следующий этап P3 должен не добавлять крупный новый функционал, а довести проект до проверяемого релиза: подтвердить, что все последние P2-доработки действительно опубликованы, закрыть мелкие release-blockers, проверить tag-triggered GitHub Release workflow, подготовить release notes и провести smoke-test standalone-артефактов.

P3 не должен превращаться в очередной этап “давайте еще улучшим всё”. Любая новая фича после P2.REL.1 оформляется отдельным этапом после релиза.

## 1. Обязательные правила P3

1. Все `git`, `gh`, `pip`, `pytest`, `compileall`, `ruff`, PyInstaller и PowerShell-команды выполнять outside sandbox.
2. Не использовать destructive-команды:
   - `git reset --hard`;
   - `git clean -fd`;
   - force push;
   - массовое удаление данных.
3. Не коммитить generated artifacts:
   - `.tmp/`;
   - `reports/`;
   - `build/`;
   - `dist/`;
   - `.pytest_cache/`;
   - `.ruff_cache/`;
   - `__pycache__/`;
   - `*.egg-info/`;
   - `*.bak`;
   - локальные пользовательские `data/*.yaml`, если они ignored.
4. Не коммитить font files, standalone exe и отчеты.
5. Все Markdown, Python, YAML, HTML и текстовые файлы сохранять в UTF-8.
6. Не использовать `read_text()` / `write_text()` без явного `encoding=` для текстовых файлов.
7. Не менять расчетную бизнес-логику без отдельного явного blocker.
8. Не менять пользовательские YAML без backup и isolated temp data для smoke.
9. Документы и финальный ответ Codex писать на русском.
10. В `docs/reports/prod_ready_progress_report.md` фиксировать каждый P3-этап кратко: цель, изменения, проверки, commit, push, GitHub Actions, ограничения.

PowerShell UTF-8 prelude перед проверками:

```powershell
chcp 65001
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
```

## 2. Анализ состояния после P2.REL.1

P2.REL.1 зафиксировал, что:

- editable install `.[dev]` проходит;
- полный pytest зеленый;
- `compileall`, Ruff, UTF-8/mojibake checker и `git diff --check` проходят;
- PyInstaller Windows build создает standalone CLI, launcher и GUI executables;
- analytics smoke создает HTML/XLSX/PDF для month/quarter/year;
- generated artifacts остаются ignored;
- P0 blockers не выявлены.

Ограничения, которые нужно закрыть на P3:

1. Tag-triggered `build-release.yml` еще не проверен на реальном release tag.
2. Публикация GitHub Release требует отдельного тестового тега и проверки artifacts.
3. Warning `Typer 0.26.7 не объявляет extra all` не блокирует установку, но его лучше убрать перед релизом.
4. `_MEI*` в `%TEMP%` после принудительно остановленных one-file процессов нужно описать и, если возможно, смягчить в troubleshooting/build docs.
5. Нужно убедиться, что последние локальные P2-доработки после P2.REL.1 действительно закоммичены, запушены и прошли CI.

## 3. P3.0 — Baseline reconciliation before release

### Цель

Проверить, что рабочая ветка, GitHub, отчет P2.REL.1 и фактический код синхронизированы. Без этого нельзя создавать tag, потому что релиз из “кажется, всё запушено” — это не релиз, а лотерея с YAML.

### Команды

```powershell
cd C:\Users\Rockaudit\LLM_CHAT\expense_splitter

git status --short
git branch --show-current
git remote -v
git log --oneline -20
git fetch origin --prune
git status --short
git rev-parse HEAD
git rev-parse origin/prod-ready/p0-p1
gh run list --limit 10
```

### Проверить

1. Текущая ветка: `prod-ready/p0-p1`.
2. `HEAD` совпадает с `origin/prod-ready/p0-p1`.
3. `git status --short` не содержит неожиданных modified/untracked source files.
4. Последние P2-этапы есть в истории:
   - settlement period UX / empty-period cleanup;
   - unified PDF reports and purchase sorting;
   - русификация пользовательских терминов;
   - release quality gate.
5. Последний GitHub Actions run по ветке зеленый.
6. `reports/`, `dist/`, `build/`, `.tmp/`, caches и backups не staged.

### Если найден blocker

- Не продолжать к P3.1.
- Зафиксировать blocker в `docs/reports/prod_ready_progress_report.md`.
- Исправить только blocker, без нового функционала.

### Критерии завершения

- Локальный HEAD и remote branch синхронизированы.
- Последний CI зеленый.
- Generated artifacts не staged.
- В progress report добавлен раздел `P3.0 — Baseline reconciliation before release`.

### Commit

Если менялся только progress report:

```powershell
git add docs/reports/prod_ready_progress_report.md
git commit -m "docs: record P3 release baseline"
git push origin prod-ready/p0-p1
```

## 4. P3.MAINT.1 — Release-blocker cleanup

### Цель

Закрыть мелкие, но неприятные release warnings перед tag. Главное — не трогать фичи и расчеты.

### Задачи

1. Убрать warning про несуществующий extra `typer[all]`:
   - проверить `pyproject.toml`;
   - если там `typer[all]`, заменить на корректный dependency `typer>=...` и явно указать нужные runtime dependencies, если они реально нужны;
   - проверить, что CLI/GUI и Rich/Typer продолжают работать.
2. Проверить `build-release.yml`:
   - есть ли `workflow_dispatch`;
   - есть ли trigger на `v*.*.*`;
   - корректны ли artifact names;
   - не публикует ли workflow полноценный release без явного tag/release policy.
3. Проверить `PACKAGING.md` и `Troubleshooting.md` на `_MEI*`:
   - добавить короткое объяснение, что `_MEI*` — временные PyInstaller one-file directories;
   - рекомендовать закрывать GUI штатно, а не убивать процесс;
   - не добавлять cleanup, который удаляет чужие temp-файлы.
4. Проверить version consistency:
   - `pyproject.toml` version;
   - README/release docs;
   - planned tag.

### Проверки

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
.\.venv\Scripts\python.exe -m ruff check src tests
git diff --check
```

### Критерии завершения

- Editable install проходит без warning про `typer[all]`, если warning действительно шел из проекта.
- Workflow syntax и release triggers понятны.
- Документация описывает `_MEI*` без паники и шаманства.
- Тесты зеленые.

### Commit

```powershell
git status --short
git add pyproject.toml .github/workflows docs README.md tests src
git commit -m "chore: clean up release readiness warnings"
git push origin prod-ready/p0-p1
gh run list --limit 10
```

## 5. P3.REL.1 — Release tag dry-run plan

### Цель

Подготовить релизный план и release notes, не публикуя tag без явного подтверждения пользователя.

### Задачи

1. Определить версию релиза:
   - если `pyproject.toml` содержит `0.1.0`, предложить tag `v0.1.0`;
   - если нужен RC, предложить `v0.1.0-rc.1`.
2. Подготовить release notes:
   - краткое описание продукта;
   - основные возможности GUI;
   - settlement periods;
   - reports: Markdown/CSV/PNG/HTML/XLSX/PDF;
   - data safety;
   - standalone Windows artifacts;
   - known limitations.
3. Создать или обновить:
   - `docs/releases/RELEASE_NOTES_v0.1.0.md`;
   - `docs/releases/RELEASE_CHECKLIST_v0.1.0.md`.
4. Проверить, что release workflow не будет случайно публиковать мусор из `dist/` текущей машины.

### Не делать без подтверждения пользователя

- Не создавать remote tag.
- Не выполнять `git push origin v...`.
- Не публиковать GitHub Release.
- Не загружать artifacts вручную.

### Проверки

Docs-only проверки:

```powershell
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
git diff --check
```

Safety checks:

```powershell
git status --short
gh workflow list
gh run list --limit 10
```

### Commit

```powershell
git add docs/releases docs/reports/prod_ready_progress_report.md README.md docs
git commit -m "docs: prepare v0.1.0 release notes and checklist"
git push origin prod-ready/p0-p1
```

## 6. P3.REL.2 — Tag-triggered Build Release verification

### Цель

Проверить, что GitHub workflow `build-release.yml` действительно собирает release artifacts при tag-triggered запуске.

### Предусловие

Получить явное подтверждение пользователя на создание и push test tag.

### Рекомендуемый безопасный вариант

1. Сначала использовать prerelease tag:

```powershell
git tag -a v0.1.0-rc.1 -m "Expense Splitter v0.1.0-rc.1"
git push origin v0.1.0-rc.1
```

2. Дождаться workflow:

```powershell
gh run list --workflow build-release.yml --limit 5
gh run watch <run-id>
gh run view <run-id> --log
```

3. Проверить artifacts:

```powershell
gh run download <run-id> --dir .tmp\release_artifacts_v0_1_0_rc1
```

4. Проверить, что artifacts содержат ожидаемые standalone executables/archives и не содержат source trash.

5. Если workflow создал GitHub Release:
   - проверить, что он draft/prerelease, если это RC;
   - проверить release notes;
   - проверить assets.

### Проверки artifacts

Из скачанных artifacts проверить минимум:

```powershell
.\expense-splitter.exe --help
.\expense-splitter-launcher.exe --help
.\expense-splitter-gui.exe --help
```

Если artifacts упакованы в zip, сначала распаковать в `.tmp`.

### Если workflow упал

- Не создавать новый tag вслепую.
- Прочитать лог:

```powershell
gh run view <run-id> --log
```

- Исправить только release workflow/build blocker.
- Создать новый RC tag только после исправления.

### Commit

Если пришлось менять workflow/docs:

```powershell
git add .github/workflows docs README.md
git commit -m "fix: stabilize tag-triggered release workflow"
git push origin prod-ready/p0-p1
```

## 7. P3.QA.1 — Clean-machine installation smoke

### Цель

Проверить пользовательский сценарий не из рабочего репозитория, а из скачанного release artifact или чистой копии. Рабочий проект, как известно, всегда “работает у разработчика”, что является самой бесполезной гарантией в природе.

### Сценарии

1. Clean artifact smoke:
   - распаковать release artifact в новую папку вне репозитория;
   - запустить CLI help;
   - запустить GUI help;
   - запустить GUI вручную.
2. First-run data smoke:
   - создать временную папку data;
   - инициализировать данные;
   - добавить покупку;
   - построить текущий отчет;
   - закрыть период;
   - построить отчет периода;
   - проверить PDF/XLSX/HTML.
3. Manual GUI smoke:
   - добавить покупку;
   - отредактировать покупку;
   - выбрать участников/категории;
   - создать PDF current-report;
   - закрыть период с autosuggest;
   - удалить пустой тестовый период;
   - проверить справочники.

### Критерии завершения

- Пользователь может запустить приложение без IDE.
- Нет traceback.
- Нет mojibake.
- Отчеты создаются.
- User data не теряется.

## 8. P3.REL.3 — Final v0.1.0 release

### Предусловие

- RC tag workflow прошел.
- Artifacts скачаны и проверены.
- Clean-machine smoke пройден.
- Пользователь дал явное подтверждение на финальный tag/release.

### Действия

```powershell
git checkout prod-ready/p0-p1
git pull origin prod-ready/p0-p1
git tag -a v0.1.0 -m "Expense Splitter v0.1.0"
git push origin v0.1.0
```

Дождаться workflow:

```powershell
gh run list --workflow build-release.yml --limit 5
gh run watch <run-id>
```

Проверить GitHub Release:

```powershell
gh release view v0.1.0
```

Если release draft:

```powershell
gh release edit v0.1.0 --draft=false
```

Выполнять публикацию только после явного разрешения пользователя.

## 9. P3.POST.1 — Post-release cleanup and next backlog

### Цель

Зафиксировать релиз и подготовить следующую ветку без смешивания релизной стабилизации с новыми фичами.

### Задачи

1. Обновить progress report:
   - release tag;
   - workflow run;
   - artifacts;
   - release URL;
   - known limitations.
2. Обновить roadmap:
   - validate-data / backup / restore, если еще не закрыто полноценно;
   - fair rounding policy, если осталась из аудита;
   - Linux/macOS standalone verification;
   - optional installer MSI/NSIS;
   - UX polish после реальных пользователей.
3. Создать milestone/issue list на GitHub, если это уместно.

### Commit

```powershell
git add docs README.md
git commit -m "docs: record v0.1.0 release results"
git push origin prod-ready/p0-p1
```

## 10. Финальный формат ответа Codex после каждого P3-этапа

```text
1. Этап.
2. Статус: completed / partial / blocked.
3. Что проверено.
4. Что изменено.
5. Измененные файлы.
6. Проверки и результаты.
7. Commit hash.
8. Push status.
9. GitHub Actions / Release workflow status.
10. Artifacts status, если применимо.
11. Generated artifacts not staged.
12. User data not modified, если применимо.
13. Git/GitHub commands outside sandbox only.
14. Known limitations.
15. Следующий рекомендуемый этап.
```

## 11. Рекомендуемый порядок выполнения

1. `P3.0 — Baseline reconciliation before release`.
2. `P3.MAINT.1 — Release-blocker cleanup`.
3. `P3.REL.1 — Release tag dry-run plan`.
4. `P3.REL.2 — Tag-triggered Build Release verification`.
5. `P3.QA.1 — Clean-machine installation smoke`.
6. `P3.REL.3 — Final v0.1.0 release`.
7. `P3.POST.1 — Post-release cleanup and next backlog`.

