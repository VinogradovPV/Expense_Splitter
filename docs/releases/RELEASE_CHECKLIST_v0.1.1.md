# Expense Splitter v0.1.1 Release Checklist

Дата подготовки: 2026-06-30
Статус: release hygiene checklist после RC-проверки.

## Version

- [x] Проверить `pyproject.toml`.
- [x] Зафиксированная версия: `0.1.1`.
- [x] Рекомендуемый tag: `v0.1.1`.
- [x] RC tag `v0.1.1-rc.1` уже использован для tag-triggered workflow dry-run.
- [x] Не создавать `v0.1.0` для текущего HEAD: версия пакета уже `0.1.1`.
- [ ] Принять отдельное решение по существующему `v0.1.1`, который указывает на старый commit `c6b4c8d`.

## Repository baseline

- [x] Branch: `prod-ready/p0-p1`.
- [x] HEAD совпадает с `origin/prod-ready/p0-p1` перед dry-run подготовкой.
- [x] Локальные `data/*.yaml` не tracked и ignored.
- [x] Generated artifacts не staged.
- [x] TG-PREP.0 baseline: HEAD `7e15112` совпадает с `origin/prod-ready/p0-p1`.
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
- [x] Для будущих RC tags `*-rc.*` workflow передает `prerelease: true`.
- [ ] Повторить RC tag workflow после workflow fix на новом RC tag.

## P3.REL.2 result for v0.1.1-rc.1

- [x] Tag `v0.1.1-rc.1` создан и отправлен в origin.
- [x] Build Release run `28443861057` завершился successfully.
- [x] GitHub Release был создан: `https://github.com/VinogradovPV/Expense_Splitter/releases/tag/v0.1.1-rc.1`.
- [x] Release оказался `prerelease=false`; workflow исправлен после проверки, но существующий release не менялся без отдельного подтверждения.
- [x] Artifact download issue classified as local/network connection problem, not project release blocker.
- [x] Do not count smoke on partially downloaded `.exe`; repeat only after complete downloads are available.

## Release notes

- [x] Подготовить `docs/releases/RELEASE_NOTES_v0.1.1.md`.
- [x] Описать GUI.
- [x] Описать settlement periods.
- [x] Описать форматы Markdown/CSV/PNG/HTML/XLSX/PDF.
- [x] Описать data safety.
- [x] Описать standalone Windows artifacts.
- [x] Описать known limitations.

## Do not do without explicit confirmation

- [x] Не создавать новые local tags в TG-PREP.1.
- [x] Не создавать новые remote tags в TG-PREP.1.
- [ ] Не выполнять `git push origin v0.1.1`.
- [ ] Не публиковать GitHub Release.
- [ ] Не загружать artifacts вручную.

## Release-history mismatch

- [x] Remote tag `v0.1.1` существует.
- [x] GitHub Release `v0.1.1` существует: `https://github.com/VinogradovPV/Expense_Splitter/releases/tag/v0.1.1`.
- [x] Tag `v0.1.1` указывает на старый commit `c6b4c8d`, а текущий baseline — `7e15112`.
- [ ] Не удалять и не пересоздавать `v0.1.1` без отдельного решения пользователя.

## Next

- [x] P3.REL.2 — RC tag workflow dry-run.
- [ ] Решить release-history mismatch перед финальной release-процедурой.
- [ ] TG-PREP.2 — создать `cloud/telegram-prep` после release hygiene decision.
