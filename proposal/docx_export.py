"""Export a proposal dict as an editable Word document."""
from __future__ import annotations

from io import BytesIO

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

from .generator import money, price_text, pricing_totals
from .render import total_weeks, week_label

ACCENT = RGBColor(0x0B, 0x6B, 0x63)


def _bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        doc.add_paragraph(item, style="List Bullet")


def _table(doc: Document, header: list[str], rows: list[list[str]], right_cols: tuple[int, ...] = ()) -> None:
    table = doc.add_table(rows=1, cols=len(header))
    table.style = "Light List Accent 1"
    for cell, text in zip(table.rows[0].cells, header):
        cell.text = text
    for row in rows:
        cells = table.add_row().cells
        for i, (cell, text) in enumerate(zip(cells, row)):
            cell.text = text
            if i in right_cols:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT


def build_docx(p: dict) -> bytes:
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(11)

    title = doc.add_heading(p["title"], level=0)
    for run in title.runs:
        run.font.color.rgb = ACCENT
    doc.add_paragraph(f"Prepared for {p['client']}").runs[0].bold = True
    doc.add_paragraph(f"Prepared by {p['prepared_by']}  |  {p['prepared_on']}  |  Valid until {p['valid_until']}")

    doc.add_heading("Executive summary", level=1)
    doc.add_paragraph(p["summary"])
    if p["goals"]:
        doc.add_heading("Project goals", level=2)
        _bullets(doc, p["goals"])

    doc.add_heading("Scope of work", level=1)
    doc.add_heading("Included", level=2)
    _bullets(doc, p["scope_in"])
    doc.add_heading("Not included", level=2)
    _bullets(doc, p["scope_out"])
    if p["assumptions"]:
        doc.add_heading("Assumptions", level=2)
        _bullets(doc, p["assumptions"])

    weeks = total_weeks(p)
    doc.add_heading("Timeline and milestones", level=1)
    doc.add_paragraph(f"{weeks} week{'s' if weeks != 1 else ''} in total.")
    _table(doc, ["When", "Phase", "What happens"],
           [[week_label(m), m["phase"], m["description"]] for m in p["milestones"]])

    doc.add_heading("Investment", level=1)
    if pricing_totals(p)[1] > 0:
        cur = p["currency"]
        _table(doc, ["Phase", "Estimate"],
               [[i["item"], money(i["low"], cur) if round(i["low"]) == round(i["high"])
                 else f"{money(i['low'], cur)} – {money(i['high'], cur)}"] for i in p["price_items"]]
               + [["Total", price_text(p)]], right_cols=(1,))
        if p["payment_terms"]:
            doc.add_heading("Payment terms", level=2)
            _bullets(doc, p["payment_terms"])
    else:
        doc.add_paragraph("Pricing will be confirmed once the scope is agreed.")

    doc.add_heading("Next steps", level=1)
    if p["notes"]:
        doc.add_heading("Special considerations", level=2)
        _bullets(doc, p["notes"])
    for step in p["next_steps"]:
        doc.add_paragraph(step, style="List Number")

    doc.add_paragraph()
    doc.add_paragraph(f"Accepted for {p['client']}: ______________________   Date: ____________")
    doc.add_paragraph(f"For {p['prepared_by']}: ______________________   Date: ____________")

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
