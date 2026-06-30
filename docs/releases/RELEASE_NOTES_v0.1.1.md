# Expense Splitter v0.1.1 Release Notes

Дата подготовки: 2026-06-30
Статус: release hygiene после RC-проверки; документ описывает текущий baseline и известные
release-history расхождения.

## Кратко

Expense Splitter — локальное приложение для учета совместных расходов, расчета долей
участников и подготовки взаиморасчетов. Проект работает как CLI и как desktop GUI на Tkinter,
хранит данные локально в YAML и генерирует пользовательские отчеты без обращения к внешним
сервисам.

Рекомендуемый release tag для текущего состояния: `v0.1.1`, но tag/release с таким именем уже
существует в GitHub и указывает на более старый commit `c6b4c8d`, а не на текущий baseline
`7e15112`.

`pyproject.toml` содержит версию `0.1.1`, поэтому tag `v0.1.0` не рекомендуется для этого
коммита. RC tag `v0.1.1-rc.1` уже использовался для проверки tag-triggered workflow.

## Основные возможности GUI

- Добавление, редактирование и удаление открытых покупок с проверками безопасности.
- Русские пользовательские подписи для статусов, scope, форматов отчетов и листов XLSX.
- Управление участниками, группами и категориями через вкладку справочников.
- Создание analytics, current-report и settlement-period отчетов из GUI.
- Открытие HTML, XLSX, PDF и папок отчетов из интерфейса.
- Защита settled/period purchases от небезопасного редактирования и удаления.

## Settlement periods

- Preview закрытия периода без изменения данных.
- Close периода с историческим snapshot: `purchase_ids`, `total_amount`, `settlements`,
  даты и статус.
- Reopen периода без удаления истории.
- Suggest следующего периода закрытия.
- Rename и безопасное удаление только пустых technical periods.
- Исторический отчет по конкретному settlement period.

## Отчеты

Поддерживаемые форматы:

- Markdown;
- CSV;
- PNG charts;
- offline HTML;
- XLSX через openpyxl;
- native PDF через ReportLab.

Доступные семейства отчетов:

- analytics за month/quarter/year;
- current-report по `open` или `all`;
- settlement-period report по историческому snapshot периода.

Визуальные отчеты скрывают служебные поля покупок (`ID`, `payer_total`, `payer_rank`) и
используют пользовательские русские названия таблиц и диаграмм. CSV сохраняет машинно-читаемые
поля там, где они нужны для аудита и сортировки.

## Data safety

- Generated artifacts исключены из Git: `reports/`, `.tmp/`, `build/`, `dist/`, caches,
  `*.egg-info`, `*.bak`.
- Локальные пользовательские `data/*.yaml` исключены из Git и не публикуются в release commit.
- Smoke tests и CLI проверки должны использовать isolated temp data dir.
- Отчеты не закрывают периоды и не меняют YAML, кроме явных команд управления данными.
- Snapshot settlements не пересчитываются при historical settlement-period report.

## Standalone Windows artifacts

P2.REL.1 подтвердил локальную standalone-сборку:

- `dist/expense-splitter.exe`;
- `dist/expense-splitter-launcher.exe`;
- `dist/expense-splitter-gui.exe`.

Release workflow должен собирать artifacts заново в GitHub Actions runner. Локальная папка
`dist/` не должна добавляться в Git и не должна загружаться вручную.

## Known limitations

- RC tag workflow проверен на `v0.1.1-rc.1`, но существующий GitHub Release для RC был создан как
  обычный release (`prerelease=false`). Workflow исправлен для будущих RC tags; существующий RC
  release не изменялся без отдельного подтверждения.
- GitHub tag/release `v0.1.1` уже существует и указывает на старый commit `c6b4c8d`, не на текущий
  baseline `7e15112`. Не удалять и не пересоздавать его без отдельного решения пользователя.
- Финальный release tag и GitHub Release требуют отдельного явного подтверждения пользователя.
- PDF требует локальный кириллический шрифт в среде сборки или запуска.
- Данные хранятся локально в YAML; многопользовательская синхронизация не реализована.
- Для Windows standalone требуется отдельный smoke test полностью скачанного release artifact.

## Dry-run decision

В рамках P3.REL.1 tag не создавался, GitHub Release не публиковался и artifacts вручную не
загружались. Позже в рамках P3.REL.2 был создан `v0.1.1-rc.1`, а существующий `v0.1.1` был
обнаружен как release-history mismatch.

Следующий рекомендуемый шаг перед cloud-веткой: `TG-PREP.2 — создать cloud-prep ветку`, только
после явного решения по release-history mismatch.

## P3.REL.2 RC verification note

Для tag `v0.1.1-rc.1` workflow `Build Release` успешно собрал Linux и Windows artifacts и создал
GitHub Release. Проверка выявила, что RC release был опубликован как обычный release
(`prerelease=false`). Workflow исправлен так, чтобы будущие tags вида `*-rc.*` публиковались как
prerelease.

Скачивание artifacts на локальную машину было нестабильным: `gh run download` и fallback download
release assets прерывались сетевыми ошибками. Пользователь классифицировал это как проблему
соединения, а не release-blocker проекта. Smoke на частично скачанных `.exe` не засчитывается;
clean local executable smoke рекомендуется повторить, когда artifacts удастся скачать полностью.
