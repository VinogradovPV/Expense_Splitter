from __future__ import annotations

import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html import escape
from pathlib import Path
from typing import Sequence

from expense_splitter.analytics import AnalyticsDataset
from expense_splitter.report_tables import (
    chart_display_title,
    rows_for_visual_table,
    visual_table_note,
)

TABLES = (
    ("summary.csv", "Сводка"),
    ("purchases.csv", "Покупки"),
    ("by_category.csv", "Расходы по категориям"),
    ("by_payer.csv", "Расходы по плательщикам"),
    ("by_participant.csv", "Объем расходов на человека"),
    ("balances.csv", "Балансы"),
    ("settlements.csv", "Переводы"),
    ("top_purchases.csv", "Крупнейшие покупки"),
    ("warnings.csv", "Предупреждения"),
)

CHARTS = (
    ("spending_by_category.png", "Расходы по категориям"),
    ("spending_by_payer.png", "Расходы по плательщикам"),
    ("participant_share.png", chart_display_title("participant_share.png")),
    ("balances.png", "Итоговые балансы"),
    ("period_trend.png", "Динамика расходов"),
    ("top_purchases.png", "Крупнейшие покупки"),
)

CSS = """
:root { --ink:#18212f; --muted:#64748b; --line:#dce3ec; --paper:#f5f7fb;
  --card:#fff; --accent:#285f8f; --warn:#8a5a13; }
* { box-sizing:border-box; } body { margin:0; color:var(--ink); background:var(--paper);
  font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif; }
main { max-width:1180px; margin:auto; padding:32px 22px 64px; }
h1,h2,h3 { line-height:1.2; } h1 { margin-bottom:6px; } h2 { margin-top:38px; }
.meta,.muted { color:var(--muted); } .cards { display:grid;
  grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:14px; margin:24px 0; }
.card,.panel { background:var(--card); border:1px solid var(--line); border-radius:12px;
  box-shadow:0 2px 10px rgba(24,33,47,.05); }
.card { padding:18px; } .card strong { display:block; font-size:25px; margin-top:6px; }
.panel { padding:20px; margin:16px 0; overflow:auto; }
.warning { border-left:5px solid #d99a32; background:#fff9ed; color:var(--warn); }
table { width:100%; border-collapse:collapse; min-width:620px; }
th,td { padding:9px 11px; border-bottom:1px solid var(--line); text-align:left; }
td.num { text-align:right; font-variant-numeric:tabular-nums; }
th { background:#eef3f8; position:sticky; top:0; } td { white-space:normal; }
.chart { width:100%; height:auto; display:block; margin-top:12px; }
.missing { padding:18px; border:1px dashed var(--line); color:var(--muted); }
a { color:var(--accent); } .links { display:flex; flex-wrap:wrap; gap:12px; }
@media (max-width:680px) { main { padding:20px 12px; } table { min-width:560px; } }
"""


def write_html_report(
    dataset: AnalyticsDataset,
    path: Path,
    warnings: Sequence[dict[str, object]],
) -> Path:
    summary = dataset.summary
    generated_at = datetime.now(timezone.utc).astimezone().strftime("%d.%m.%Y %H:%M %Z")
    warning_messages = [escape(str(row.get("message", ""))) for row in warnings]
    warnings_html = (
        "<ul>" + "".join(f"<li>{message}</li>" for message in warning_messages) + "</ul>"
        if warning_messages
        else "<p>Предупреждений нет.</p>"
    )
    cards = (
        ("Общая сумма", _value(summary["total_amount"])),
        ("Количество покупок", _value(summary["purchase_count"])),
        ("Средний чек", _value(summary["average_purchase"])),
        ("Участников", _value(summary["participant_count"])),
    )
    card_html = "".join(
        '<div class="card">'
        f'<span class="muted">{escape(label)}</span>'
        f"<strong>{escape(value)}</strong></div>"
        for label, value in cards
    )
    table_html = "".join(_table_section(path.parent, filename, title) for filename, title in TABLES)
    chart_html = "".join(_chart_section(path.parent, filename, title) for filename, title in CHARTS)
    csv_links = "".join(
        f'<a href="tables/{escape(filename)}">{escape(title)} CSV</a>' for filename, title in TABLES
    )
    document = f"""<!doctype html>
<html lang="ru"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Expense Splitter — аналитика {escape(dataset.period_spec.period_id)}</title>
<style>{CSS}</style></head>
<body><main data-contract-section="report">
<header><h1>Expense Splitter — аналитика расходов</h1>
<p class="meta">Период: {dataset.period_spec.start_date:%d.%m.%Y} —
{dataset.period_spec.end_date:%d.%m.%Y}<br>
Сформировано: {escape(generated_at)}</p></header>
<section data-contract-section="executive-summary"><h2>Краткий итог</h2>
<p>Отчёт объединяет расходы, распределение между участниками, балансы и необходимые
переводы за выбранный период.</p>
<div class="cards">{card_html}</div></section>
<section><h2>Предупреждения и ограничения</h2>
<div class="panel warning">{warnings_html}</div></section>
<section><h2>Графики</h2><p>Визуальные срезы помогают быстро оценить структуру
и динамику расходов.</p>{chart_html}</section>
<section><h2>Таблицы</h2><p>Точные значения приведены ниже и доступны отдельными
CSV-файлами.</p>{table_html}</section>
<section><h2>Файлы отчёта</h2><div class="panel links">
<a href="analytics_report.md">Markdown-отчёт</a>{csv_links}</div></section>
</main></body></html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document, encoding="utf-8")
    return path


def _table_section(report_dir: Path, filename: str, title: str) -> str:
    path = report_dir / "tables" / filename
    if not path.exists():
        return (
            f'<article class="panel"><h3>{escape(title)}</h3><p>Таблица не создана.</p></article>'
        )
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = rows_for_visual_table(filename, list(csv.reader(stream)))
    if not rows:
        body = '<p class="muted">Нет данных.</p>'
    else:
        header = "".join(f"<th>{escape(cell)}</th>" for cell in rows[0])
        data = "".join(
            "<tr>" + "".join(_html_cell(cell) for cell in row) + "</tr>"
            for row in rows[1:]
        )
        body = f"<table><thead><tr>{header}</tr></thead><tbody>{data}</tbody></table>"
    note = visual_table_note(filename)
    if note:
        body += f'<p class="muted">{escape(note)}</p>'
    return f'<article class="panel"><h3>{escape(title)}</h3>{body}</article>'


def _html_cell(value: str) -> str:
    css_class = ' class="num"' if _is_numeric_text(value) else ""
    return f"<td{css_class}>{escape(value)}</td>"


def _is_numeric_text(value: str) -> bool:
    try:
        Decimal(value)
    except (InvalidOperation, ValueError):
        return False
    return True


def _chart_section(report_dir: Path, filename: str, title: str) -> str:
    path = report_dir / "charts" / filename
    if path.exists():
        return (
            f'<article class="panel"><h3>{escape(title)}</h3>'
            '<p class="muted">Локальный PNG-график; значения относятся к выбранному периоду.</p>'
            f'<img class="chart" src="charts/{escape(filename)}" alt="{escape(title)}"></article>'
        )
    return (
        f'<article class="panel"><h3>{escape(title)}</h3>'
        '<p class="missing">График не создан: нет данных за выбранный период.</p></article>'
    )


def _value(value: object) -> str:
    return f"{value:.2f}" if hasattr(value, "quantize") else str(value)
