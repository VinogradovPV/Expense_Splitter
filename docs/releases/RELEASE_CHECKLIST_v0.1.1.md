# Expense Splitter v0.1.1 Release Checklist

Дата подготовки: 2026-06-30
Статус: dry-run checklist, release не опубликован.

## Version

- [x] Проверить `pyproject.toml`.
- [x] Зафиксированная версия: `0.1.1`.
- [x] Рекомендуемый tag: `v0.1.1`.
- [ ] Если нужен release candidate: использовать `v0.1.1-rc.1`.
- [ ] Не создавать `v0.1.0` для текущего HEAD: версия пакета уже `0.1.1`.

## Repository baseline

- [x] Branch: `prod-ready/p0-p1`.
- [x] HEAD совпадает с `origin/prod-ready/p0-p1` перед dry-run подготовкой.
- [x] Локальные `data/*.yaml` не tracked и ignored.
- [x] Generated artifacts не staged.
- [ ] Перед tag повторить `git status --short`.
- [ ] Перед tag повторить `git rev-parse HEAD` и `git rev-parse origin/prod-ready/p0-p1`.

## Quality gate before tag

- [ ] `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"`
- [ ] `.\.venv\Scripts\python.exe -m pytest tests -v`
- [ ] `.\.venv\Scripts\python.exe -m compileall -q src tests`
- [ ] `.\.venv\Scripts\python.exe -m ruff check src tests`
- [ ] `.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py`
- [ ] `git diff --check`

## Release workflow safety

- [x] `build-release.yml` имеет `workflow_dispatch`.
- [x] `build-release.yml` запускается на tags `v*.*.*`.
- [x] Build jobs выполняют checkout и сборку в GitHub runner.
- [x] Artifact upload использует runner-local `dist/*`.
- [x] Локальный `dist/` текущей машины не участвует в workflow.
- [x] GitHub Release job ограничен tag refs: `startsWith(github.ref, 'refs/tags/v')`.
- [ ] Перед RC tag проверить, что workflow behavior приемлем для prerelease policy.

## Release notes

- [x] Подготовить `docs/releases/RELEASE_NOTES_v0.1.1.md`.
- [x] Описать GUI.
- [x] Описать settlement periods.
- [x] Описать форматы Markdown/CSV/PNG/HTML/XLSX/PDF.
- [x] Описать data safety.
- [x] Описать standalone Windows artifacts.
- [x] Описать known limitations.

## Do not do without explicit confirmation

- [ ] Не создавать local tag.
- [ ] Не создавать remote tag.
- [ ] Не выполнять `git push origin v0.1.1`.
- [ ] Не публиковать GitHub Release.
- [ ] Не загружать artifacts вручную.

## Next

- [ ] P3.REL.2 — RC tag workflow dry-run.
- [ ] P3.REL.3 — Final v0.1.1 release после явного подтверждения пользователя.
