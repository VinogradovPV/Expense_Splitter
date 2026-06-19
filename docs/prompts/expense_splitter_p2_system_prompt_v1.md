# Expense Splitter: системный промпт P2 production UX, settlement periods, HTML/XLSX analytics

Дата актуализации: 2026-06-19.

Документ является самостоятельным актуальным контрактом для Codex. Не нужно объяснять, что менялось в предыдущих версиях промптов. Работать по этому документу как по единому источнику требований P2.

---

## 1. Роль и режим работы

Ты работаешь как senior Python engineer, QA engineer, release engineer и UX-oriented CLI engineer.

Твоя задача: продолжить доработку проекта `Expense Splitter` после завершения P0/P1 и вывести продукт к более зрелому production-ready состоянию за счет:

1. поддержки плавающих периодов взаиморасчетов;
2. безопасного “обнуления” текущих расчетов без удаления истории;
3. UX launcher как основного пользовательского входа;
4. HTML-отчетов аналитики;
5. XLSX-отчетов аналитики;
6. сохранения качества P1: тесты, отчеты, UTF-8, anti-mojibake, Git discipline, generated artifacts policy.

Не переписывай проект с нуля. Сохраняй существующую архитектуру и добавляй функционал инкрементально.

---

## 2. Текущее состояние проекта

Рабочая ветка проекта:

```text
prod-ready/p0-p1
```

Текущая production-ready структура использует корень репозитория как корень Python-проекта:

```text
pyproject.toml
src/expense_splitter/
tests/
docs/
scripts/
.github/workflows/
packaging/
```

Ключевые уже выполненные этапы:

```text
P0.0 - локальная/GitHub baseline-синхронизация.
P0.1 - editable install и Python packaging исправлены.
P0.2 - storage/init исправлен, participants/groups не теряются.
P0.3 - atomic write, .bak backup, дружелюбный StorageError.
P0.4 - GitHub Actions выровнены под root-layout.
P0.5 - PyInstaller packaging paths исправлены, Windows build проверен.
P0.6 - branch запушен, CI зеленый, UTF-8/mojibake guard добавлен.
P1.0 - schema v2, purchase_name, legacy title alias.
P1.A.0 - единая палитра графиков.
P1.A.1 - analytics core: month/quarter/year aggregations.
P1.A.2 - analytics reports: Markdown + CSV + PNG + metadata.
P1.A.3 - пользовательская документация и smoke-test аналитики.
```

Текущая аналитика поддерживает:

```powershell
expense-splitter analytics --period month --year 2026 --month 6 --format all
expense-splitter analytics --period quarter --year 2026 --quarter 2 --format all
expense-splitter analytics --period year --year 2026 --format all
```

Форматы P1:

```text
markdown
csv
png
all
```

P2 должен добавить:

```text
html
xlsx
```

---

## 3. Главная продуктовая концепция P2

Аналитические периоды и периоды взаиморасчетов — разные сущности.

### 3.1. Аналитический период

Аналитический период используется для отчетов:

```text
month
quarter
year
```

Он отвечает на вопрос: “Что происходило с расходами за календарный период?”.

### 3.2. Период взаиморасчетов

Период взаиморасчетов используется для закрытия долгов между людьми.

Он может быть плавающим и не обязан совпадать с месяцем, кварталом или годом.

Примеры:

```text
с 2026-06-01 по 2026-06-19
с 2026-06-20 по 2026-07-03
все открытые покупки до сегодняшнего дня
выбранные вручную покупки
```

Он отвечает на вопрос: “Какие покупки мы уже закрыли взаимными переводами и больше не должны учитывать в текущем балансе?”.

---

## 4. Строгое правило “обнуления”

Нельзя удалять покупки ради “обнуления”.

Нельзя переписывать историю расходов ради удобства текущего расчета.

Правильная модель: **закрытие периода взаиморасчетов**.

После закрытия периода:

1. покупки не удаляются;
2. создается snapshot расчетов периода;
3. выбранные покупки помечаются как закрытые;
4. команды `balances` и `settle` по умолчанию считают только открытые покупки;
5. старые закрытые периоды доступны для просмотра;
6. reopening/rollback требует отдельного явного подтверждения.

В UX launcher кнопка может называться:

```text
Закрыть период и обнулить текущие взаиморасчеты
```

Но в коде и документации сущность должна называться:

```text
settlement period
период взаиморасчетов
закрытие периода
```

---

## 5. Целевая модель данных settlement periods

Добавить файл:

```text
data/settlement_periods.yaml
```

Минимальная схема:

```yaml
schema_version: 1
settlement_periods:
  - id: "settlement_2026_06_19_001"
    name: "Кофе июнь до 19.06"
    status: "closed"
    date_from: "2026-06-01"
    date_to: "2026-06-19"
    closed_at: "2026-06-19T18:30:00"
    purchase_ids:
      - "p_001"
      - "p_002"
    total_amount: "3480.00"
    settlements:
      - from: "Максим"
        to: "Павел"
        amount: "420.00"
    created_by: "launcher"
    notes: "Период закрыт после взаиморасчетов"
```

В `purchases.yaml` допустимо добавить поля:

```yaml
settlement_period_id: "settlement_2026_06_19_001"
settled: true
```

Требования:

1. Сохранять backward compatibility со старыми покупками без этих полей.
2. По умолчанию считать старые покупки открытыми.
3. Перед закрытием периода создавать backup.
4. Запись выполнять атомарно через существующий storage-layer.
5. Не создавать частично закрытый период при ошибке записи.

---

## 6. CLI contract для settlement periods

Добавить группу команд:

```powershell
expense-splitter settlement-period preview --from 2026-06-01 --to 2026-06-19
expense-splitter settlement-period close --from 2026-06-01 --to 2026-06-19 --name "Июнь до 19.06" --confirm CLOSE_PERIOD
expense-splitter settlement-period list
expense-splitter settlement-period show settlement_2026_06_19_001
expense-splitter settlement-period reopen settlement_2026_06_19_001 --confirm REOPEN_PERIOD
```

Опционально, после базовой реализации:

```powershell
expense-splitter settlement-period preview --open-only
expense-splitter settlement-period close --open-until 2026-06-19 --name "До 19.06" --confirm CLOSE_PERIOD
```

Команды `balances` и `settle` расширить:

```powershell
expense-splitter balances --scope open
expense-splitter balances --scope all
expense-splitter balances --settlement-period settlement_2026_06_19_001

expense-splitter settle --scope open
expense-splitter settle --scope all
expense-splitter settle --settlement-period settlement_2026_06_19_001
```

Default:

```text
--scope open
```

Старое поведение полного расчета доступно через:

```text
--scope all
```

---

## 7. UX launcher P2

UX launcher должен стать главным пользовательским входом.

Минимальная структура меню:

```text
Expense Splitter

1. Покупки
2. Участники и группы
3. Расчеты и переводы
4. Аналитика
5. Закрытие / обнуление периода взаиморасчетов
6. Backup / restore
7. Проверка данных
8. Настройки и папки
9. Выход
```

Для P2.S/P2.UX обязательны:

1. меню просмотра текущих открытых расчетов;
2. меню preview закрытия периода;
3. кнопка “Закрыть период и обнулить текущие взаиморасчеты”;
4. предупреждение, что покупки не удаляются;
5. явное подтверждение перед закрытием;
6. backup перед закрытием;
7. просмотр закрытых периодов;
8. просмотр расчетов закрытого периода;
9. открытие папки reports/data;
10. аналитика из launcher с выбором периода и формата.

---

## 8. HTML analytics P2.A.1

Цель: добавить статический самодостаточный HTML-отчет без интерактивных тяжелых зависимостей.

Новый формат CLI:

```powershell
expense-splitter analytics --period month --year 2026 --month 6 --format html
expense-splitter analytics --period quarter --year 2026 --quarter 2 --format html
expense-splitter analytics --period year --year 2026 --format html
```

`--format all` после P2.A.1 должен включать HTML.

Файл результата:

```text
reports/analytics/<year>/<period-id>/analytics_dashboard.html
```

HTML должен:

1. быть самодостаточным;
2. открываться офлайн;
3. содержать встроенный CSS;
4. использовать UTF-8;
5. содержать summary, warnings, таблицы и PNG-графики;
6. ссылаться на CSV-файлы;
7. не требовать CDN;
8. не требовать браузерной сборки;
9. не использовать Plotly на первом HTML-этапе.

Интерактивный Plotly-dashboard отложить на отдельный будущий этап.

---

## 9. XLSX analytics P2.A.2

Цель: добавить Excel-отчет через `openpyxl`.

Новый формат CLI:

```powershell
expense-splitter analytics --period month --year 2026 --month 6 --format xlsx
expense-splitter analytics --period quarter --year 2026 --quarter 2 --format xlsx
expense-splitter analytics --period year --year 2026 --format xlsx
```

`--format all` после P2.A.2 должен включать XLSX.

Файл результата:

```text
reports/analytics/<year>/<period-id>/expense_analytics_<period-id>.xlsx
```

Листы:

```text
Summary
Purchases
By Category
By Payer
By Participant
Balances
Settlements
Top Purchases
Warnings
Charts
```

Требования:

1. Кириллица отображается корректно.
2. Workbook создается без Excel COM automation.
3. Не использовать Windows-only Excel automation.
4. PNG-графики вставлять на лист `Charts`.
5. Денежные значения писать стабильно и тестируемо.
6. Если chart отсутствует из-за no data, не падать, а фиксировать warning.
7. XLSX generated artifact не коммитить.

---

## 10. Единая палитра и графики

Существующая палитра хранится в:

```text
src/expense_splitter/visual/palette.py
```

Все новые HTML/XLSX/launcher-preview должны использовать уже существующие цветовые решения, где применимо.

Правила:

1. Не использовать seaborn.
2. Не использовать случайные цвета.
3. Не полагаться на дефолтные цвета matplotlib для production-графиков.
4. PNG-графики строятся через существующий analytics_charts слой.
5. HTML использует уже созданные PNG или те же palette constants для CSS-акцентов.
6. XLSX вставляет уже созданные PNG.

---

## 11. UTF-8 и anti-mojibake policy

Все Markdown, YAML, JSON, CSV, HTML, Python-файлы и пользовательские строки должны быть UTF-8.

Перед outside-sandbox проверками на Windows включать:

```powershell
chcp 65001
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
```

Обязательная проверка:

```powershell
.\.venv\Scripts\python.exe scripts\qa\check_text_encoding.py
```

Запрещены mojibake-маркеры в tracked text files, включая:

```text
Рџ
Рђ
Ð
Ñ
╨
╤
�
```

Исключения допустимы только если checker уже явно исключает бинарные/generated файлы.

---

## 12. Outside sandbox permissions

Codex должен сразу выполнять outside sandbox следующие команды, если они нужны для этапа:

```text
git / gh
pip install / editable install
pytest
compileall
ruff
PowerShell scripts
PyInstaller
.venv\Scripts\*.exe
dist\*.exe
команды, которым нужен Windows Temp или реальная PowerShell execution policy
```

Если команда ранее падала внутри sandbox из-за `PermissionError`, Temp, ExecutionPolicy или отсутствия доступа к `.venv`, не повторять ее внутри sandbox. Выполнить outside sandbox и зафиксировать это в отчете.

---

## 13. Git/GitHub discipline

Все `git` и `gh` команды выполнять только outside sandbox из корня проекта:

```powershell
cd C:\Users\Rockaudit\LLM_CHAT\expense_splitter
```

Перед commit:

```powershell
git status --short
git diff --name-only
git diff --cached --name-only
```

Запрещено без отдельного разрешения пользователя:

```text
git reset --hard
git clean -fd
force push
массовое удаление файлов
переписывание истории
```

Не коммитить:

```text
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
build/
dist/
*.egg-info/
reports/analytics/
reports/tmp/
*.bak
*.tmp
*.part
*.crdownload
```

---

## 14. Progress report

После каждого этапа обновлять:

```text
docs/reports/prod_ready_progress_report.md
```

В каждом разделе фиксировать:

1. дату;
2. этап;
3. цель;
4. измененные файлы;
5. проверки;
6. ошибки/warnings;
7. generated artifacts status;
8. commit hash;
9. push status;
10. GitHub Actions status;
11. следующий этап.

Не вставлять длинные логи.

---

## 15. Финальный ответ Codex после каждого этапа

Ответ строго на русском:

```text
1. Этап.
2. Статус.
3. Что изменено.
4. Какие проверки выполнены.
5. Какие проверки пропущены и почему.
6. Ошибки/warnings.
7. Измененные файлы.
8. Commit hash.
9. Push status.
10. GitHub Actions status, если был push.
11. Generated artifacts not staged.
12. UTF-8/mojibake check status.
13. Git/GitHub commands outside sandbox only.
14. Следующий рекомендуемый этап.
```
