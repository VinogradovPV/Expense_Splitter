from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

from expense_splitter.report_tables import chart_display_title, rows_for_visual_table

CSV_ENCODING = "utf-8-sig"
FONT_NAME = "ExpenseSplitterSans"
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
class PdfTableSpec:
    filename: str
    title: str


def discover_cyrillic_font() -> Path | None:
    for candidate in FONT_CANDIDATES:
        if candidate.is_file():
            return candidate
    return None


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
    from reportlab.lib.enums import TA_RIGHT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Image,
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
        "PageBreak": PageBreak,
        "Paragraph": Paragraph,
        "ParagraphStyle": ParagraphStyle,
        "SimpleDocTemplate": SimpleDocTemplate,
        "Spacer": Spacer,
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
) -> Path:
    tools = _load_reportlab_layout_tools()
    font_name = ensure_pdf_font()
    page_size = tools["landscape"](tools["A4"])
    doc = tools["SimpleDocTemplate"](
        str(path),
        pagesize=page_size,
        leftMargin=1.1 * tools["cm"],
        rightMargin=1.1 * tools["cm"],
        topMargin=1.0 * tools["cm"],
        bottomMargin=1.0 * tools["cm"],
    )
    styles = _styles(font_name, tools)
    story: list[object] = [
        tools["Paragraph"](title, styles["Title"]),
        tools["Spacer"](1, 0.25 * tools["cm"]),
    ]
    story.append(_build_table(metadata_rows, styles, doc.width, compact=False))
    story.append(tools["Spacer"](1, 0.35 * tools["cm"]))

    for spec in table_specs:
        csv_path = tables_dir / spec.filename
        story.append(tools["Paragraph"](spec.title, styles["Heading2"]))
        if csv_path.is_file():
            rows = rows_for_visual_table(spec.filename, _read_csv(csv_path))
            story.append(_build_table(rows, styles, doc.width, compact=True, tools=tools))
        else:
            story.append(tools["Paragraph"]("Таблица не создана.", styles["BodyText"]))
        story.append(tools["Spacer"](1, 0.35 * tools["cm"]))

    chart_paths = sorted(charts_dir.glob("*.png")) if charts_dir and charts_dir.exists() else []
    if chart_paths:
        story.append(tools["PageBreak"]())
        story.append(tools["Paragraph"]("Графики", styles["Heading2"]))
        for chart_path in chart_paths:
            story.append(tools["Paragraph"](chart_display_title(chart_path), styles["Heading3"]))
            story.append(_image(chart_path, doc.width, doc.height * 0.72, tools))
            story.append(tools["Spacer"](1, 0.25 * tools["cm"]))

    path.parent.mkdir(parents=True, exist_ok=True)
    doc.build(
        story,
        onFirstPage=lambda canvas, doc: _page_footer(canvas, doc, tools),
        onLaterPages=lambda canvas, doc: _page_footer(canvas, doc, tools),
    )
    return path


def _styles(font_name: str, tools: dict[str, Any]):
    styles = tools["getSampleStyleSheet"]()
    for style in styles.byName.values():
        style.fontName = font_name
    styles["Title"].fontSize = 17
    styles["Title"].leading = 21
    styles["Heading2"].fontSize = 12
    styles["Heading2"].leading = 15
    styles["Heading3"].fontSize = 9
    styles["Heading3"].leading = 11
    styles["BodyText"].fontSize = 7
    styles["BodyText"].leading = 8.5
    styles.add(
        tools["ParagraphStyle"](
            name="Cell",
            parent=styles["BodyText"],
            fontName=font_name,
            fontSize=6.2,
            leading=7.4,
        )
    )
    styles.add(
        tools["ParagraphStyle"](
            name="CellRight",
            parent=styles["Cell"],
            alignment=tools["TA_RIGHT"],
        )
    )
    return styles


def _build_table(
    rows: Sequence[Sequence[object]],
    styles,
    width: float,
    *,
    compact: bool,
    tools: dict[str, Any] | None = None,
) -> Any:
    tools = tools or _load_reportlab_layout_tools()
    if not rows:
        rows = [["Нет данных."]]
    column_count = max(len(row) for row in rows)
    normalized = [list(row) + [""] * (column_count - len(row)) for row in rows]
    col_widths = _column_widths(normalized, width)
    body = [
        [
            tools["Paragraph"](
                _serialize(cell),
                styles["CellRight" if _is_numeric(cell) else "Cell"],
            )
            for cell in row
        ]
        for row in normalized
    ]
    table = tools["Table"](
        body,
        colWidths=col_widths,
        repeatRows=1 if compact and len(rows) > 1 else 0,
    )
    table.setStyle(
        tools["TableStyle"](
            [
                ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
                ("BACKGROUND", (0, 0), (-1, 0), tools["colors"].HexColor("#EAF1F7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), tools["colors"].HexColor("#172033")),
                ("GRID", (0, 0), (-1, -1), 0.25, tools["colors"].HexColor("#D9E2EC")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _column_widths(rows: Sequence[Sequence[object]], width: float) -> list[float]:
    count = max(len(row) for row in rows)
    raw = [
        max(len(_serialize(row[index])) for row in rows if index < len(row))
        for index in range(count)
    ]
    weights = [max(6, min(length, 28)) for length in raw]
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


def _serialize(value: object) -> str:
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def _is_numeric(value: object) -> bool:
    if isinstance(value, (Decimal, int, float)):
        return True
    try:
        Decimal(str(value))
    except Exception:
        return False
    return True


def _page_footer(canvas, doc, tools: dict[str, Any]) -> None:
    canvas.saveState()
    canvas.setFont(FONT_NAME, 7)
    canvas.setFillColor(tools["colors"].HexColor("#607086"))
    canvas.drawRightString(
        doc.pagesize[0] - doc.rightMargin,
        0.45 * tools["cm"],
        f"Page {doc.page}",
    )
    canvas.restoreState()
