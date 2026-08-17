from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, Sequence

from expense_splitter.report_tables import rows_for_visual_table, visual_table_note

CSV_ENCODING = "utf-8-sig"
FONT_NAME = "ExpenseSplitterSans"
PDF_MAIN_PURCHASE_ROWS_LIMIT = 15
FONT_CANDIDATES = (
    Path(r"C:\Windows\Fonts\arial.ttf"),
    Path(r"C:\Windows\Fonts\segoeui.ttf"),
    Path(r"C:\Windows\Fonts\tahoma.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    Path("/Library/Fonts/Arial Unicode.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
)


class PdfFontError(ValueError):
    """Raised when no local Cyrillic-capable font is available."""


@dataclass(frozen=True)
class PdfDesignTokens:
    margin_x_cm: float = 1.4
    margin_y_cm: float = 1.1
    title_size: float = 19
    section_size: float = 13
    kpi_label_size: float = 8
    kpi_value_size: float = 15
    table_size: float = 8.7
    appendix_size: float = 7.6
    note_size: float = 7.8
    ink: str = "#172033"
    muted: str = "#607086"
    accent: str = "#285F8F"
    line: str = "#D9E2EC"
    warning: str = "#8A5A13"


@dataclass(frozen=True)
class PdfTableSpec:
    filename: str
    title: str
    display_mode: Literal["compact", "financial", "full", "appendix", "callout"] = (
        "compact"
    )
    section: Literal["overview", "participants", "details", "appendix"] = "details"
    preferred_width: float = 0.55


@dataclass(frozen=True)
class PdfChartSpec:
    key: str
    title: str
    image_path: Path
    size_mode: Literal["full", "half", "compact"] = "half"
    section: str = "charts"
    generated: bool = True


@dataclass(frozen=True)
class PdfReportManifest:
    tables: tuple[PdfTableSpec, ...]
    charts: tuple[PdfChartSpec, ...]


def discover_cyrillic_font() -> Path | None:
    return next((candidate for candidate in FONT_CANDIDATES if candidate.is_file()), None)


def ensure_pdf_font() -> str:
    pdfmetrics, TTFont = _load_reportlab_font_tools()
    if FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return FONT_NAME
    font_path = discover_cyrillic_font()
    if font_path is None:
        raise PdfFontError(
            "PDF font not found. Install Arial, Segoe UI, Tahoma, DejaVu Sans, or Liberation Sans "
            "and rerun the report."
        )
    pdfmetrics.registerFont(TTFont(FONT_NAME, str(font_path)))
    return FONT_NAME


def _load_reportlab_font_tools() -> tuple[Any, Any]:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    return pdfmetrics, TTFont


def _load_reportlab_layout_tools() -> dict[str, Any]:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Image,
        KeepTogether,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    return {
        "A4": A4,
        "Image": Image,
        "KeepTogether": KeepTogether,
        "PageBreak": PageBreak,
        "Paragraph": Paragraph,
        "ParagraphStyle": ParagraphStyle,
        "SimpleDocTemplate": SimpleDocTemplate,
        "Spacer": Spacer,
        "TA_CENTER": TA_CENTER,
        "TA_RIGHT": TA_RIGHT,
        "Table": Table,
        "TableStyle": TableStyle,
        "cm": cm,
        "colors": colors,
        "getSampleStyleSheet": getSampleStyleSheet,
        "landscape": landscape,
    }


def write_pdf_report(
    path: Path,
    *,
    title: str,
    metadata_rows: Sequence[Sequence[object]],
    tables_dir: Path,
    table_specs: Sequence[PdfTableSpec],
    charts_dir: Path | None = None,
    chart_paths: Sequence[Path] | None = None,
    report_kind: Literal["analytics", "current", "settlement"] = "current",
) -> Path:
    tools = _load_reportlab_layout_tools()
    font_name = ensure_pdf_font()
    tokens = PdfDesignTokens()
    doc = tools["SimpleDocTemplate"](
        str(path),
        pagesize=tools["landscape"](tools["A4"]),
        leftMargin=tokens.margin_x_cm * tools["cm"],
        rightMargin=tokens.margin_x_cm * tools["cm"],
        topMargin=tokens.margin_y_cm * tools["cm"],
        bottomMargin=tokens.margin_y_cm * tools["cm"],
    )
    styles = _styles(font_name, tools, tokens)
    manifest = _build_manifest(table_specs, chart_paths, charts_dir, report_kind)
    table_data = _load_manifest_tables(manifest, tables_dir)
    context_rows, kpi_rows = _split_summary_rows(metadata_rows)
    story: list[object] = [
        tools["Paragraph"](title, styles["Title"]),
        tools["Spacer"](1, 0.08 * tools["cm"]),
    ]
    if context_rows:
        story.extend(
            [
                tools["Paragraph"](_context_text(context_rows), styles["Context"]),
                tools["Spacer"](1, 0.16 * tools["cm"]),
            ]
        )
    story.extend(
        [
            _kpi_grid(kpi_rows, styles, doc.width, tools, tokens),
            tools["Spacer"](1, 0.28 * tools["cm"]),
        ]
    )

    rendered_section = False
    for section in ("overview", "participants", "details"):
        specs = [spec for spec in manifest.tables if spec.section == section]
        if not specs:
            continue
        if rendered_section:
            story.append(tools["PageBreak"]())
        story.extend(_table_grid(specs, table_data, styles, doc.width, tools, tokens))
        rendered_section = True

    if manifest.charts:
        if rendered_section:
            story.append(tools["PageBreak"]())
        story.extend(_chart_grid(manifest.charts, styles, doc.width, doc.height, tools))

    appendix_specs = [spec for spec in manifest.tables if spec.section == "appendix"]
    if appendix_specs:
        story.extend(
            [
                tools["PageBreak"](),
                tools["Paragraph"]("Приложение: все покупки", styles["Title"]),
                tools["Spacer"](1, 0.18 * tools["cm"]),
            ]
        )
        for spec in appendix_specs:
            story.append(
                _build_table(
                    table_data.get(spec.filename, []),
                    styles,
                    doc.width,
                    mode="appendix",
                    tools=tools,
                    tokens=tokens,
                )
            )

    path.parent.mkdir(parents=True, exist_ok=True)
    doc.build(
        story,
        onFirstPage=lambda canvas, current_doc: _page_footer(canvas, current_doc, tools, tokens),
        onLaterPages=lambda canvas, current_doc: _page_footer(canvas, current_doc, tools, tokens),
    )
    return path


def _build_manifest(
    table_specs: Sequence[PdfTableSpec],
    chart_paths: Sequence[Path] | None,
    charts_dir: Path | None,
    report_kind: str,
) -> PdfReportManifest:
    paths = list(chart_paths) if chart_paths is not None else (
        list(charts_dir.glob("*.png")) if charts_dir and charts_dir.exists() else []
    )
    order = {
        "current": [
            "balances.png",
            "operations_by_day.png",
            "participant_share.png",
            "spending_by_category.png",
            "spending_by_payer.png",
            "top_purchases.png",
        ],
        "analytics": [
            "spending_by_category.png",
            "spending_by_payer.png",
            "participant_share.png",
            "balances.png",
            "period_trend.png",
            "top_purchases.png",
        ],
        "settlement": [
            "balances.png",
            "participant_share.png",
            "spending_by_category.png",
            "spending_by_payer.png",
            "top_purchases.png",
        ],
    }.get(report_kind, [])
    rank = {name: index for index, name in enumerate(order)}
    paths.sort(key=lambda item: (rank.get(item.name, len(rank)), item.name))
    charts = tuple(
        PdfChartSpec(
            key=item.stem,
            title=_chart_title(item.name),
            image_path=item,
            size_mode="full" if item.name == "period_trend.png" else "half",
        )
        for item in paths
        if item.is_file()
    )
    return PdfReportManifest(tuple(table_specs), charts)


def _load_manifest_tables(
    manifest: PdfReportManifest, tables_dir: Path
) -> dict[str, list[list[str]]]:
    result: dict[str, list[list[str]]] = {}
    for spec in manifest.tables:
        csv_path = tables_dir / spec.filename
        rows = (
            rows_for_visual_table(spec.filename, _read_csv(csv_path))
            if csv_path.is_file()
            else []
        )
        if spec.filename == "purchases.csv" and spec.section != "appendix":
            rows = _compact_purchase_rows(rows)
        result[spec.filename] = rows
    return result


def _split_summary_rows(
    rows: Sequence[Sequence[object]],
) -> tuple[list[Sequence[object]], list[Sequence[object]]]:
    kpi_prefixes = (
        "общая сумма",
        "общая сумма периода",
        "количество покупок",
        "средняя покупка",
        "средний чек",
        "количество участников",
        "итоговые переводы",
    )
    context, kpis = [], []
    for row in rows:
        label = str(row[0]).casefold() if row else ""
        (kpis if label.startswith(kpi_prefixes) else context).append(row)
    return context, kpis


def _context_text(rows: Sequence[Sequence[object]]) -> str:
    return "   •   ".join(
        f"{_serialize(row[0])}: {_friendly_value(row[1])}" for row in rows if len(row) > 1
    )


def _friendly_value(value: object) -> str:
    text = _serialize(value).replace("T", " ")
    if "+" in text and len(text) > 19:
        text = text.split("+")[0]
    return text[:16] if len(text) >= 19 and text[10:11] == " " else text


def _kpi_grid(rows, styles, width, tools, tokens):
    if not rows:
        rows = [["Данные", "Нет данных"]]
    cards = []
    for row in rows:
        label = str(row[0]).replace("Количество ", "").capitalize()
        value = _format_kpi_value(row[1] if len(row) > 1 else "")
        cards.append(
            tools["Table"](
                [
                    [tools["Paragraph"](value, styles["KpiValue"])],
                    [tools["Paragraph"](label, styles["KpiLabel"])],
                ],
                style=tools["TableStyle"](
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), tools["colors"].HexColor("#F4F7FA")),
                        ("BOX", (0, 0), (-1, -1), 0.6, tools["colors"].HexColor(tokens.line)),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, 0), 6),
                        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                    ]
                ),
            )
        )
    count = min(len(cards), 6)
    grid = tools["Table"]([cards], colWidths=[width / count] * count)
    grid.setStyle(
        tools["TableStyle"](
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return tools["KeepTogether"]([grid])


def _format_kpi_value(value: object) -> str:
    if isinstance(value, (Decimal, float)):
        return f"{value:,.2f}".replace(",", " ")
    return _serialize(value)


def _table_grid(specs, table_data, styles, width, tools, tokens) -> list[object]:
    cards = [
        _table_card(spec, table_data.get(spec.filename, []), styles, width * 0.48, tools, tokens)
        for spec in specs
    ]
    result: list[object] = []
    for index in range(0, len(cards), 2):
        pair = cards[index : index + 2]
        if len(pair) == 1:
            pair.append("")
        grid = tools["Table"]([pair], colWidths=[width * 0.49, width * 0.49])
        grid.setStyle(
            tools["TableStyle"](
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        result.append(grid)
    return result


def _table_card(spec, rows, styles, width, tools, tokens):
    if spec.display_mode == "callout" or (spec.filename == "warnings.csv" and len(rows) <= 1):
        if spec.filename == "warnings.csv" and len(rows) > 1:
            message = "<br/>".join(_serialize(row[-1]) for row in rows[1:] if row)
        else:
            message = rows[0][0] if rows else "Таблица не создана."
        body = tools["Paragraph"](_serialize(message), styles["Callout"])
    else:
        body = _build_table(rows, styles, width, mode=spec.display_mode, tools=tools, tokens=tokens)
    content = [[tools["Paragraph"](spec.title, styles["Heading2"])] , [body]]
    note = visual_table_note(spec.filename)
    if note:
        content.append([tools["Paragraph"](note, styles["Note"])])
    card = tools["Table"](content, colWidths=[width])
    card.setStyle(
        tools["TableStyle"](
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return card


def _chart_grid(charts, styles, width, height, tools) -> list[object]:
    result: list[object] = [tools["Paragraph"]("Графики", styles["Heading2"])]
    for page_start in range(0, len(charts), 4):
        if page_start:
            result.extend(
                [tools["PageBreak"](), tools["Paragraph"]("Графики", styles["Heading2"])]
            )
        page_charts = charts[page_start : page_start + 4]
        if len(page_charts) == 1:
            result.append(
                _chart_card(page_charts[0], styles, width, height * 0.72, tools)
            )
            continue
        rows, spans, pending = [], [], []
        for chart in page_charts:
            if chart.size_mode == "full":
                if pending:
                    rows.append([pending[0], ""])
                    pending = []
                row_index = len(rows)
                rows.append(
                    [_chart_card(chart, styles, width * 0.96, height * 0.46, tools), ""]
                )
                spans.append(("SPAN", (0, row_index), (1, row_index)))
                continue
            pending.append(_chart_card(chart, styles, width * 0.48, height * 0.34, tools))
            if len(pending) == 2:
                rows.append(pending)
                pending = []
        if pending:
            rows.append([pending[0], ""])
        grid = tools["Table"](rows, colWidths=[width * 0.49, width * 0.49])
        grid.setStyle(
            tools["TableStyle"](
                [
                    *spans,
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        result.append(grid)
    return result


def _chart_card(chart, styles, max_width, max_height, tools):
    card = tools["Table"](
        [
            [tools["Paragraph"](chart.title, styles["Heading3"])],
            [_image(chart.image_path, max_width, max_height, tools)],
        ],
        colWidths=[max_width],
    )
    card.setStyle(
        tools["TableStyle"](
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return card


def _styles(font_name: str, tools: dict[str, Any], tokens: PdfDesignTokens | None = None):
    tokens = tokens or PdfDesignTokens()
    styles = tools["getSampleStyleSheet"]()
    for style in styles.byName.values():
        style.fontName = font_name
    styles["Title"].fontSize = tokens.title_size
    styles["Title"].leading = 22
    styles["Title"].textColor = tools["colors"].HexColor(tokens.ink)
    styles["Heading2"].fontSize = tokens.section_size
    styles["Heading2"].leading = 16
    styles["Heading2"].spaceAfter = 5
    styles["Heading3"].fontSize = 10
    styles["Heading3"].leading = 12
    styles["Heading3"].spaceAfter = 3
    styles["BodyText"].fontSize = tokens.note_size
    styles["BodyText"].leading = 10
    additions = (
        ("Cell", tokens.table_size, 10.5, 0, tokens.ink),
        ("CellRight", tokens.table_size, 10.5, tools["TA_RIGHT"], tokens.ink),
        ("AppendixCell", tokens.appendix_size, 9.1, 0, tokens.ink),
        ("KpiLabel", tokens.kpi_label_size, 9.5, tools["TA_CENTER"], tokens.muted),
        ("KpiValue", tokens.kpi_value_size, 17, tools["TA_CENTER"], tokens.accent),
        ("Context", tokens.note_size, 10, 0, tokens.muted),
        ("Note", tokens.note_size, 9.5, 0, tokens.muted),
        ("Callout", 8.5, 10.5, 0, tokens.warning),
    )
    for name, size, leading, alignment, color in additions:
        styles.add(
            tools["ParagraphStyle"](
                name=name,
                parent=styles["BodyText"],
                fontName=font_name,
                fontSize=size,
                leading=leading,
                alignment=alignment,
                textColor=tools["colors"].HexColor(color),
            )
        )
    return styles


def _build_table(rows, styles, width, *, mode="compact", tools=None, tokens=None):
    tools = tools or _load_reportlab_layout_tools()
    tokens = tokens or PdfDesignTokens()
    if not rows:
        rows = [["Нет данных."]]
    column_count = max(len(row) for row in rows)
    normalized = [list(row) + [""] * (column_count - len(row)) for row in rows]
    col_widths = _column_widths(normalized, width)
    body = [
        [
            tools["Paragraph"](
                _serialize(cell),
                styles[
                    "CellRight"
                    if _is_numeric(cell)
                    else ("AppendixCell" if mode == "appendix" else "Cell")
                ],
            )
            for cell in row
        ]
        for row in normalized
    ]
    table = tools["Table"](body, colWidths=col_widths, repeatRows=1 if len(rows) > 1 else 0)
    table.setStyle(
        tools["TableStyle"](
            [
                ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
                ("BACKGROUND", (0, 0), (-1, 0), tools["colors"].HexColor("#EAF1F7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), tools["colors"].HexColor(tokens.ink)),
                ("LINEBELOW", (0, 0), (-1, 0), 0.7, tools["colors"].HexColor(tokens.accent)),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [tools["colors"].white, tools["colors"].HexColor("#F8FAFC")],
                ),
                ("GRID", (0, 0), (-1, -1), 0.2, tools["colors"].HexColor(tokens.line)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _compact_purchase_rows(rows: Sequence[Sequence[str]]) -> list[list[str]]:
    if not rows:
        return []
    headers = [str(value) for value in rows[0]]
    wanted = {
        "Дата",
        "Покупка",
        "Наименование покупки",
        "Сумма",
        "Плательщик",
        "Категория",
        "Участники",
    }
    indexes = [index for index, header in enumerate(headers) if header in wanted]
    result = [
        [headers[index] if headers[index] != "Участники" else "Участников" for index in indexes]
    ]
    for row in rows[1 : PDF_MAIN_PURCHASE_ROWS_LIMIT + 1]:
        compact = []
        for index in indexes:
            value = row[index] if index < len(row) else ""
            if headers[index] == "Участники":
                count = len([item for item in str(value).split(",") if item.strip()])
                value = f"{count} участн."
            compact.append(value)
        result.append(compact)
    return result


def _column_widths(rows: Sequence[Sequence[object]], width: float) -> list[float]:
    count = max(len(row) for row in rows)
    raw = [
        max(len(_serialize(row[index])) for row in rows if index < len(row))
        for index in range(count)
    ]
    weights = [max(6, min(length, 32)) for length in raw]
    total = sum(weights) or 1
    return [width * weight / total for weight in weights]


def _image(path: Path, max_width: float, max_height: float, tools: dict[str, Any]) -> Any:
    image = tools["Image"](str(path))
    ratio = min(max_width / image.drawWidth, max_height / image.drawHeight, 1)
    image.drawWidth *= ratio
    image.drawHeight *= ratio
    return image


def _read_csv(path: Path) -> list[list[str]]:
    with path.open(encoding=CSV_ENCODING, newline="") as stream:
        return list(csv.reader(stream))


def _chart_title(filename: str) -> str:
    from expense_splitter.report_tables import chart_display_title

    return chart_display_title(filename)


def _serialize(value: object) -> str:
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    return "" if value is None else str(value)


def _is_numeric(value: object) -> bool:
    if isinstance(value, (Decimal, int, float)):
        return True
    try:
        Decimal(str(value).replace(" ", "").replace("%", ""))
    except Exception:
        return False
    return True


def _page_footer(
    canvas, doc, tools: dict[str, Any], tokens: PdfDesignTokens | None = None
) -> None:
    tokens = tokens or PdfDesignTokens()
    canvas.saveState()
    canvas.setFont(FONT_NAME, 7)
    canvas.setFillColor(tools["colors"].HexColor(tokens.muted))
    canvas.drawRightString(
        doc.pagesize[0] - doc.rightMargin,
        0.45 * tools["cm"],
        f"Страница {doc.page}",
    )
    canvas.restoreState()
