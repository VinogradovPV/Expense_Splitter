# Expense Splitter v0.1.1 Release Notes

Дата подготовки: 2026-06-30
Статус: dry-run, tag не создан.

## Кратко

Expense Splitter — локальное приложение для учета совместных расходов, расчета долей
участников и подготовки взаиморасчетов. Проект работает как CLI и как desktop GUI на Tkinter,
хранит данные локально в YAML и генерирует пользовательские отчеты без обращения к внешним
сервисам.

Рекомендуемый release tag для текущего состояния: `v0.1.1`.

`pyproject.toml` содержит версию `0.1.1`, поэтому tag `v0.1.0` не рекомендуется для этого
коммита. Если нужен release candidate перед финальным релизом, безопасный вариант:
`v0.1.1-rc.1`.

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

- Release tag workflow еще не проверен реальным RC tag в рамках P3.REL.2.
- Финальный release tag и GitHub Release требуют отдельного явного подтверждения пользователя.
- PDF требует локальный кириллический шрифт в среде сборки или запуска.
- Данные хранятся локально в YAML; многопользовательская синхронизация не реализована.
- Для Windows standalone требуется отдельный smoke test скачанного release artifact.

## Dry-run decision

Tag не создан. GitHub Release не опубликован. Artifacts вручную не загружались.

Следующий рекомендуемый шаг: `P3.REL.2 — RC tag workflow dry-run`.
