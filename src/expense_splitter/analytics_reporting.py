from __future__ import annotations

import csv
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Sequence

from expense_splitter.analytics import AnalyticsDataset
from expense_splitter.analytics_charts import generate_analytics_charts
from expense_splitter.analytics_html import write_html_report
from expense_splitter.analytics_xlsx import write_xlsx_report
from expense_splitter.report_pdf import PdfTableSpec, write_pdf_report
from expense_splitter.report_sorting import sorted_purchases_with_payer_totals
from expense_splitter.report_tables import chart_display_title
from expense_splitter.visual.palette import PALETTE_NAME, PALETTE_VERSION

SUPPORTED_FORMATS = {"markdown", "csv", "png", "html", "xlsx", "pdf", "all"}
CSV_ENCODING = "utf-8-sig"
ANALYTICS_PDF_TABLES = (
    PdfTableSpec("summary.csv", "Сводка"),
    PdfTableSpec("by_category.csv", "Расходы по категориям"),
    PdfTableSpec("by_payer.csv", "Расходы по плательщикам"),
    PdfTableSpec("by_participant.csv", "Объем расходов на человека"),
    PdfTableSpec("balances.csv", "Балансы"),
    PdfTableSpec("settlements.csv", "Переводы"),
    PdfTableSpec("purchases.csv", "Покупки"),
    PdfTableSpec("warnings.csv", "Предупреждения"),
)


def generate_analytics_report(
    dataset: AnalyticsDataset,
    output_root: Path = Path("reports/analytics"),
    output_format: str = "all",
) -> Path:
    """Generate requested analytics artifacts and return the period report directory."""
    format_key = output_format.lower()
    if format_key not in SUPPORTED_FORMATS:
        raise ValueError("Format must be one of: markdown, csv, png, html, xlsx, pdf, all.")

    report_dir = output_root / str(dataset.period_spec.year) / dataset.period_spec.period_id
    report_dir.mkdir(parents=True, exist_ok=True)
    warnings = [dict(row) for row in dataset.warnings]
    generated: list[Path] = []

    bundle_format = format_key in {"html", "all"}
    if format_key == "html":
        for stale_dir in (report_dir / "tables", report_dir / "charts"):
            stale_dir.mkdir(parents=True, exist_ok=True)

    if format_key in {"png", "html", "xlsx", "pdf", "all"}:
        chart_paths, chart_warnings = generate_analytics_charts(dataset, report_dir / "charts")
        generated.extend(chart_paths)
        warnings.extend(chart_warnings)

    if format_key in {"csv", "html", "xlsx", "pdf", "all"}:
        generated.extend(write_csv_tables(dataset, report_dir / "tables", warnings))
    elif format_key == "png" and warnings:
        generated.append(write_warnings_csv(report_dir / "tables" / "warnings.csv", warnings))

    if format_key in {"markdown", "html", "all"}:
        generated.append(
            write_markdown_report(dataset, report_dir / "analytics_report.md", warnings)
        )

    if bundle_format:
        generated.append(
            write_html_report(
                dataset,
                report_dir / "analytics_dashboard.html",
                warnings,
            )
        )

    if format_key in {"xlsx", "all"}:
        generated.append(
            write_xlsx_report(
                dataset,
                report_dir / f"expense_analytics_{dataset.period_spec.period_id}.xlsx",
                report_dir / "tables",
                report_dir / "charts",
            )
        )

    if format_key in {"pdf", "all"}:
        generated.append(
            write_pdf_report(
                report_dir / f"expense_analytics_{dataset.period_spec.period_id}.pdf",
                title="Аналитический отчет",
                metadata_rows=_summary_rows(dataset),
                tables_dir=report_dir / "tables",
                table_specs=ANALYTICS_PDF_TABLES,
                charts_dir=report_dir / "charts",
            )
        )

    if bundle_format:
        metadata_path = report_dir / "metadata.json"
        generated.append(metadata_path)
        write_metadata(dataset, metadata_path, generated, warnings, report_dir)

    return report_dir


def write_csv_tables(
    dataset: AnalyticsDataset,
    tables_dir: Path,
    warnings: Sequence[dict[str, object]] | None = None,
) -> list[Path]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    warning_rows = list(dataset.warnings if warnings is None else warnings)
    specs = (
        ("summary.csv", ["Показатель", "Значение"], _summary_rows(dataset)),
        (
            "purchases.csv",
            [
                "ID",
                "Дата",
                "Наименование покупки",
                "Сумма",
                "Плательщик",
                "Участники",
                "Категория",
                "Комментарий",
            ],
            _purchase_rows(dataset),
        ),
        (
            "by_category.csv",
            ["Категория", "Количество покупок", "Сумма"],
            (
                [row["category"], row["purchase_count"], row["total_amount"]]
                for row in dataset.by_category
            ),
        ),
        (
            "by_payer.csv",
            ["Плательщик", "Количество покупок", "Оплачено", "Доля оплат, %"],
            (
                [
                    row["payer"],
                    row["purchase_count"],
                    row["total_paid"],
                    row["payer_share_percent"],
                ]
                for row in dataset.by_payer
            ),
        ),
        (
            "by_participant.csv",
            ["Участник", "Количество покупок", "Доля расходов"],
            (
                [row["participant"], row["purchase_count"], row["total_share"]]
                for row in dataset.by_participant
            ),
        ),
        (
            "balances.csv",
            ["Участник", "Оплачено", "Доля", "Баланс"],
            ([row.participant, row.paid, row.share, row.net] for row in dataset.balances),
        ),
        (
            "settlements.csv",
            ["От кого", "Кому", "Сумма"],
            ([row.from_participant, row.to_participant, row.amount] for row in dataset.settlements),
        ),
        (
            "top_purchases.csv",
            [
                "Место",
                "ID",
                "Дата",
                "Наименование покупки",
                "Сумма",
                "Плательщик",
                "Категория",
                "Участники",
            ],
            _top_purchase_rows(dataset),
        ),
        (
            "warnings.csv",
            ["Тип предупреждения", "ID покупки", "Наименование покупки", "Сообщение"],
            _warning_rows(warning_rows),
        ),
    )
    paths: list[Path] = []
    for filename, headers, rows in specs:
        path = tables_dir / filename
        _write_csv(path, headers, rows)
        paths.append(path)
    return paths


def write_warnings_csv(path: Path, warnings: Sequence[dict[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(
        path,
        ["Тип предупреждения", "ID покупки", "Наименование покупки", "Сообщение"],
        _warning_rows(warnings),
    )
    return path


def write_markdown_report(
    dataset: AnalyticsDataset,
    path: Path,
    warnings: Sequence[dict[str, object]] | None = None,
) -> Path:
    summary = dataset.summary
    lines = [
        f"# Аналитика расходов: {dataset.period_spec.period_id}",
        "",
        (
            f"Период: {dataset.period_spec.start_date.isoformat()} — "
            f"{dataset.period_spec.end_date.isoformat()}"
        ),
        "",
        "## Сводка",
        "",
        "| Показатель | Значение |",
        "|---|---:|",
        f"| Общая сумма | {_serialize(summary['total_amount'])} |",
        f"| Количество покупок | {summary['purchase_count']} |",
        f"| Средняя покупка | {_serialize(summary['average_purchase'])} |",
        f"| Количество участников | {summary['participant_count']} |",
        "",
    ]
    _append_markdown_table(
        lines,
        "Покупки",
        [
            "Дата",
            "Покупка",
            "Сумма",
            "Плательщик",
            "Участники",
            "Категория",
            "Комментарий",
        ],
        (
            [row[1], row[2], row[3], row[4], row[5], row[6], row[7]]
            for row in _purchase_rows(dataset)
        ),
    )
    _append_markdown_table(
        lines,
        "Расходы по категориям",
        ["Категория", "Покупок", "Сумма"],
        (
            [row["category"], row["purchase_count"], row["total_amount"]]
            for row in dataset.by_category
        ),
    )
    _append_markdown_table(
        lines,
        "Расходы по плательщикам",
        ["Плательщик", "Покупок", "Оплачено", "Доля оплат, %"],
        (
            [row["payer"], row["purchase_count"], row["total_paid"], row["payer_share_percent"]]
            for row in dataset.by_payer
        ),
    )
    _append_markdown_table(
        lines,
        "Объем расходов на человека",
        ["Участник", "Покупок", "Доля"],
        (
            [row["participant"], row["purchase_count"], row["total_share"]]
            for row in dataset.by_participant
        ),
    )
    _append_markdown_table(
        lines,
        "Балансы",
        ["Участник", "Оплачено", "Доля", "Баланс"],
        ([row.participant, row.paid, row.share, row.net] for row in dataset.balances),
    )
    _append_markdown_table(
        lines,
        "Переводы",
        ["От кого", "Кому", "Сумма"],
        ([row.from_participant, row.to_participant, row.amount] for row in dataset.settlements),
    )
    _append_markdown_table(
        lines,
        "Крупнейшие покупки",
        ["Место", "Покупка", "Сумма", "Плательщик"],
        (
            [row["rank"], row["purchase_name"], row["amount"], row["payer"]]
            for row in dataset.top_purchases
        ),
    )

    warning_rows = list(dataset.warnings if warnings is None else warnings)
    if warning_rows:
        lines.extend(["## Предупреждения", ""])
        lines.extend(f"- {_escape_markdown(row.get('message', ''))}" for row in warning_rows)
        lines.append("")

    chart_dir = path.parent / "charts"
    chart_paths = sorted(chart_dir.glob("*.png")) if chart_dir.exists() else []
    if chart_paths:
        lines.extend(["## Графики", ""])
        for chart_path in chart_paths:
            title = chart_display_title(chart_path)
            lines.extend([f"![{title}](charts/{chart_path.name})", ""])

    lines.extend(["## Файлы", "", "- CSV-таблицы: `tables/`", "- PNG-графики: `charts/`", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_metadata(
    dataset: AnalyticsDataset,
    path: Path,
    generated_files: Sequence[Path],
    warnings: Sequence[dict[str, object]],
    report_dir: Path,
) -> Path:
    metadata = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": {
            "type": dataset.period_spec.period,
            "id": dataset.period_spec.period_id,
            "year": dataset.period_spec.year,
            "month": dataset.period_spec.month,
            "quarter": dataset.period_spec.quarter,
            "start_date": dataset.period_spec.start_date.isoformat(),
            "end_date": dataset.period_spec.end_date.isoformat(),
        },
        "summary": {key: _json_value(value) for key, value in dataset.summary.items()},
        "palette": {"name": PALETTE_NAME, "version": PALETTE_VERSION},
        "warning_count": len(warnings),
        "files": sorted(
            str(file.relative_to(report_dir)).replace("\\", "/") for file in generated_files
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _summary_rows(dataset: AnalyticsDataset) -> list[list[object]]:
    summary = dataset.summary
    return [
        ["Тип периода", summary["period"]],
        ["ID периода", summary["period_id"]],
        ["Дата начала", summary["start_date"]],
        ["Дата окончания", summary["end_date"]],
        ["Общая сумма", summary["total_amount"]],
        ["Количество покупок", summary["purchase_count"]],
        ["Средняя покупка", summary["average_purchase"]],
        ["Количество участников", summary["participant_count"]],
    ]


def _purchase_rows(dataset: AnalyticsDataset) -> Iterable[list[object]]:
    for row in sorted_purchases_with_payer_totals(dataset.purchases):
        purchase = row.purchase
        yield [
            purchase.id,
            purchase.date,
            purchase.purchase_name,
            purchase.amount,
            purchase.payer,
            purchase.participants,
            purchase.category,
            purchase.comment,
            row.payer_total,
            row.payer_rank,
        ]


def _top_purchase_rows(dataset: AnalyticsDataset) -> Iterable[list[object]]:
    for row in dataset.top_purchases:
        yield [
            row["rank"],
            row["id"],
            row["date"],
            row["purchase_name"],
            row["amount"],
            row["payer"],
            row["category"],
            row["participants"],
        ]


def _warning_rows(warnings: Sequence[dict[str, object]]) -> Iterable[list[object]]:
    for row in warnings:
        yield [
            row.get("warning_type", ""),
            row.get("purchase_id", ""),
            row.get("purchase_name", ""),
            row.get("message", ""),
        ]


def _write_csv(path: Path, headers: Sequence[str], rows: Iterable[Sequence[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    materialized_rows = [list(row) for row in rows]
    output_headers = _headers_for_rows(path, headers, materialized_rows)
    with path.open("w", encoding=CSV_ENCODING, newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(output_headers)
        writer.writerows([_serialize(value) for value in row] for row in materialized_rows)


def _headers_for_rows(
    path: Path,
    headers: Sequence[str],
    rows: Sequence[Sequence[object]],
) -> list[str]:
    result = list(headers)
    max_columns = max((len(row) for row in rows), default=len(result))
    if path.name == "purchases.csv" and max_columns == len(result) + 2:
        result.extend(["payer_total", "payer_rank"])
    while len(result) < max_columns:
        result.append(f"extra_{len(result) + 1}")
    return result


def _serialize(value: object) -> str:
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def _json_value(value: object) -> object:
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, date):
        return value.isoformat()
    return value


def _append_markdown_table(
    lines: list[str], title: str, headers: Sequence[str], rows: Iterable[Sequence[object]]
) -> None:
    serialized_rows = [[_escape_markdown(value) for value in row] for row in rows]
    output_headers = _headers_for_markdown(headers, serialized_rows)
    lines.extend([f"## {title}", ""])
    if not serialized_rows:
        lines.extend(["Нет данных.", ""])
        return
    lines.append("| " + " | ".join(output_headers) + " |")
    lines.append("|" + "|".join("---" for _ in output_headers) + "|")
    lines.extend("| " + " | ".join(row) + " |" for row in serialized_rows)
    lines.append("")


def _headers_for_markdown(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    result = list(headers)
    max_columns = max((len(row) for row in rows), default=len(result))
    if max_columns == len(result) + 2:
        result.extend(["payer_total", "payer_rank"])
    while len(result) < max_columns:
        result.append(f"extra_{len(result) + 1}")
    return result


def _escape_markdown(value: object) -> str:
    return _serialize(value).replace("|", "\\|").replace("\n", " ")
