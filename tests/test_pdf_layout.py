from pathlib import Path

import expense_splitter.report_pdf as report_pdf
from expense_splitter.report_pdf import PdfTableSpec
from expense_splitter.report_tables import BALANCE_EXPLANATION


class FakeDoc:
    def __init__(self, path, **kwargs):
        self.path = Path(path)
        self.width = 720
        self.height = 480
        self.pagesize = kwargs["pagesize"]
        self.rightMargin = 36
        self.leftMargin = 36
        self.topMargin = 36
        self.bottomMargin = 36
        self.story = None

    def build(self, story, **kwargs):
        self.story = story
        self.path.write_bytes(b"%PDF fake")


def test_pdf_story_keeps_table_title_with_table_and_avoids_chart_pagebreak(
    tmp_path,
    monkeypatch,
):
    captured = {}

    def fake_doc(path, **kwargs):
        doc = FakeDoc(path, **kwargs)
        captured["doc"] = doc
        return doc

    tools = {
        "A4": (842, 595),
        "Image": lambda path: path,
        "KeepTogether": lambda content: ("keep", content),
        "PageBreak": lambda: "PAGEBREAK",
        "Paragraph": lambda text, style: ("paragraph", text, style),
        "ParagraphStyle": lambda **kwargs: kwargs,
        "SimpleDocTemplate": fake_doc,
        "Spacer": lambda width, height: ("spacer", width, height),
        "TA_RIGHT": 2,
        "Table": lambda *args, **kwargs: ("table", args, kwargs),
        "TableStyle": lambda commands: ("style", commands),
        "cm": 28.35,
        "colors": object(),
        "getSampleStyleSheet": lambda: {},
        "landscape": lambda size: size,
    }
    monkeypatch.setattr(report_pdf, "_load_reportlab_layout_tools", lambda: tools)
    monkeypatch.setattr(report_pdf, "ensure_pdf_font", lambda: report_pdf.FONT_NAME)
    monkeypatch.setattr(
        report_pdf,
        "_styles",
        lambda font_name, tools: {"Title": "title", "Heading2": "h2", "BodyText": "body"},
    )
    monkeypatch.setattr(
        report_pdf,
        "_build_table",
        lambda rows, styles, width, **kwargs: ("table", rows),
    )
    monkeypatch.setattr(report_pdf, "_image", lambda path, width, height, tools: ("image", path))

    tables_dir = tmp_path / "tables"
    charts_dir = tmp_path / "charts"
    tables_dir.mkdir()
    charts_dir.mkdir()
    (tables_dir / "balances.csv").write_text(
        "Участник,Оплачено,Доля,Баланс\nAlice,100.00,50.00,50.00\n",
        encoding="utf-8-sig",
    )
    (charts_dir / "balances.png").write_bytes(b"fake")

    report_pdf.write_pdf_report(
        tmp_path / "report.pdf",
        title="Smoke",
        metadata_rows=[["Показатель", "Значение"]],
        tables_dir=tables_dir,
        table_specs=[PdfTableSpec("balances.csv", "Балансы")],
        charts_dir=charts_dir,
    )

    story = captured["doc"].story
    keep_blocks = [item for item in story if isinstance(item, tuple) and item[0] == "keep"]
    assert keep_blocks
    table_block = keep_blocks[0][1]
    assert ("paragraph", "Балансы", "h2") in table_block
    assert any(item == ("paragraph", BALANCE_EXPLANATION, "body") for item in table_block)
    assert "PAGEBREAK" not in story
