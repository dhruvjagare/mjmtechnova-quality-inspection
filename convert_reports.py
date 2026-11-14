"""
convert_reports.py - Generates professionally styled DOCX and PDF documents
for the Comprehensive Technical Report and the Code & Model Report.
"""
import re
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted, PageBreak, KeepTogether
)
from reportlab.pdfgen import canvas

BASE_DIR = Path("d:/python_vs")

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def markdown_to_docx(md_path: Path, docx_path: Path, title: str):
    doc = Document()
    
    # Configure 1-inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Styles
    navy = RGBColor(31, 78, 120)       # #1F4E78
    dark_gray = RGBColor(50, 50, 50)
    code_bg = "F4F6F9"

    lines = md_path.read_text(encoding="utf-8").splitlines()
    in_code_block = False
    code_buffer = []
    in_table = False
    table_rows = []

    for line in lines:
        stripped = line.strip()

        # Handle Code Blocks
        if stripped.startswith("```"):
            if in_code_block:
                in_code_block = False
                # Add table for code block
                tbl = doc.add_table(rows=1, cols=1)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                cell = tbl.cell(0, 0)
                set_cell_background(cell, code_bg)
                set_cell_margins(cell, 120, 120, 180, 180)
                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                run = p.add_run("\n".join(code_buffer))
                run.font.name = "Consolas"
                run.font.size = Pt(8.5)
                run.font.color.rgb = RGBColor(30, 30, 30)
                doc.add_paragraph().paragraph_format.space_after = Pt(4)
                code_buffer = []
            else:
                in_code_block = True
                code_buffer = []
            continue

        if in_code_block:
            code_buffer.append(line)
            continue

        # Handle Tables
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            # Skip delimiter rows
            if all(re.match(r"^:?-+:?$", c) for c in cells):
                continue
            if not in_table:
                in_table = True
                table_rows = [cells]
            else:
                table_rows.append(cells)
            continue
        elif in_table:
            # End of table, render it
            in_table = False
            if table_rows:
                num_cols = max(len(r) for r in table_rows)
                tbl = doc.add_table(rows=len(table_rows), cols=num_cols)
                tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                for r_idx, row_data in enumerate(table_rows):
                    is_header = (r_idx == 0)
                    for c_idx, val in enumerate(row_data):
                        cell = tbl.cell(r_idx, c_idx)
                        p = cell.paragraphs[0]
                        p.paragraph_format.space_before = Pt(2)
                        p.paragraph_format.space_after = Pt(2)
                        # Clean markdown bold/code from cell text
                        clean_val = re.sub(r"\*\*([^*]+)\*\*", r"\1", val)
                        clean_val = re.sub(r"`([^`]+)`", r"\1", clean_val)
                        run = p.add_run(clean_val)
                        if is_header:
                            set_cell_background(cell, "1F4E78")
                            run.font.bold = True
                            run.font.color.rgb = RGBColor(255, 255, 255)
                            run.font.size = Pt(9)
                        else:
                            if r_idx % 2 == 1:
                                set_cell_background(cell, "F9FAFC")
                            else:
                                set_cell_background(cell, "FFFFFF")
                            run.font.size = Pt(8.5)
                            run.font.color.rgb = dark_gray
                doc.add_paragraph().paragraph_format.space_after = Pt(6)
            table_rows = []

        # Empty lines
        if not stripped:
            continue

        # Headings
        if stripped.startswith("# "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(stripped[2:].replace("📘", "").replace("🧠", "").strip())
            run.font.name = "Calibri"
            run.font.size = Pt(20)
            run.font.bold = True
            run.font.color.rgb = navy
        elif stripped.startswith("## "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(3)
            run = p.add_run(stripped[3:].strip())
            run.font.name = "Calibri"
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = navy
        elif stripped.startswith("### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(stripped[4:].strip())
            run.font.name = "Calibri"
            run.font.size = Pt(11.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(40, 90, 140)
        elif stripped.startswith("#### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(stripped[5:].strip())
            run.font.name = "Calibri"
            run.font.size = Pt(10.5)
            run.font.bold = True
            run.font.color.rgb = dark_gray
        elif stripped.startswith("- ") or stripped.startswith("* "):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            clean_text = stripped[2:].strip()
            # Simple bold handler
            parts = re.split(r"(\*\*[^*]+\*\*)", clean_text)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    r = p.add_run(part[2:-2])
                    r.font.bold = True
                else:
                    p.add_run(part)
        elif re.match(r"^\d+\.\s+", stripped):
            match = re.match(r"^(\d+\.\s+)(.*)", stripped)
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            parts = re.split(r"(\*\*[^*]+\*\*)", match.group(2))
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    r = p.add_run(part[2:-2])
                    r.font.bold = True
                else:
                    p.add_run(part)
        elif stripped.startswith("> "):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(stripped[2:])
            r.font.italic = True
            r.font.color.rgb = RGBColor(100, 100, 100)
        elif stripped.startswith("---"):
            continue
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(4)
            parts = re.split(r"(\*\*[^*]+\*\*)", stripped)
            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    r = p.add_run(part[2:-2])
                    r.font.bold = True
                else:
                    p.add_run(part)

    doc.save(docx_path)
    print(f"Generated DOCX: {docx_path}")

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#666666"))
        # Top banner
        self.drawString(54, 750, "MJMTECHNOVA ENGINEERING PVT. LTD. | Technical Project Documentation")
        self.setStrokeColor(colors.HexColor("#D0D7DE"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)
        # Footer
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "Confidential - Quality Inspection Automation System")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)
        self.restoreState()

def markdown_to_pdf(md_path: Path, pdf_path: Path):
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=64,
        bottomMargin=54
    )
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1F4E78"),
        spaceAfter=10
    )
    h1_style = ParagraphStyle(
        'DocH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1F4E78"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#285A8C"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#222222"),
        spaceAfter=4
    )
    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=2
    )
    code_style = ParagraphStyle(
        'DocCode',
        fontName='Courier',
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#1E1E1E")
    )

    story = []
    lines = md_path.read_text(encoding="utf-8").splitlines()
    in_code_block = False
    code_buffer = []
    in_table = False
    table_rows = []

    def clean_inline_html(text):
        # Escape XML entities first
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # Replace escaped formatting
        text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', text)
        return text

    for line in lines:
        stripped = line.strip()

        # Handle Code blocks
        if stripped.startswith("```"):
            if in_code_block:
                in_code_block = False
                code_text = "\n".join(code_buffer)
                p = Preformatted(code_text, code_style)
                # Put in table box
                t = Table([[p]], colWidths=[504])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F6F8FA")),
                    ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#D0D7DE")),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('LEFTPADDING', (0,0), (-1,-1), 6),
                    ('RIGHTPADDING', (0,0), (-1,-1), 6),
                ]))
                story.append(t)
                story.append(Spacer(1, 4))
                code_buffer = []
            else:
                in_code_block = True
                code_buffer = []
            continue

        if in_code_block:
            code_buffer.append(line)
            continue

        # Handle Tables
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if all(re.match(r"^:?-+:?$", c) for c in cells):
                continue
            if not in_table:
                in_table = True
                table_rows = [cells]
            else:
                table_rows.append(cells)
            continue
        elif in_table:
            in_table = False
            if table_rows:
                num_cols = max(len(r) for r in table_rows)
                col_width = 504 / num_cols
                formatted_table_data = []
                for r_idx, row in enumerate(table_rows):
                    row_data = []
                    is_h = (r_idx == 0)
                    for c_idx in range(num_cols):
                        val = row[c_idx] if c_idx < len(row) else ""
                        c_text = clean_inline_html(val)
                        if is_h:
                            p = Paragraph(f"<b><font color='white'>{c_text}</font></b>", ParagraphStyle('TH', parent=body_style, fontSize=7.5, leading=9.5))
                        else:
                            p = Paragraph(c_text, ParagraphStyle('TD', parent=body_style, fontSize=7, leading=8.5))
                        row_data.append(p)
                    formatted_table_data.append(row_data)

                t = Table(formatted_table_data, colWidths=[col_width]*num_cols)
                t_style = [
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1F4E78")),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D0D7DE")),
                    ('TOPPADDING', (0,0), (-1,-1), 3),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                    ('LEFTPADDING', (0,0), (-1,-1), 4),
                    ('RIGHTPADDING', (0,0), (-1,-1), 4),
                ]
                for r_idx in range(1, len(formatted_table_data)):
                    if r_idx % 2 == 1:
                        t_style.append(('BACKGROUND', (0, r_idx), (-1, r_idx), colors.HexColor("#F9FAFC")))
                t.setStyle(TableStyle(t_style))
                story.append(t)
                story.append(Spacer(1, 4))
            table_rows = []

        if not stripped:
            continue

        if stripped.startswith("# "):
            title_text = clean_inline_html(stripped[2:].replace("📘", "").replace("🧠", "").strip())
            story.append(Paragraph(title_text, title_style))
        elif stripped.startswith("## "):
            h_text = clean_inline_html(stripped[3:].strip())
            story.append(Paragraph(h_text, h1_style))
        elif stripped.startswith("### ") or stripped.startswith("#### "):
            h_text = clean_inline_html(re.sub(r"^#+\s*", "", stripped).strip())
            story.append(Paragraph(h_text, h2_style))
        elif stripped.startswith("- ") or stripped.startswith("* "):
            bullet_text = clean_inline_html("• " + stripped[2:].strip())
            story.append(Paragraph(bullet_text, bullet_style))
        elif re.match(r"^\d+\.\s+", stripped):
            num_text = clean_inline_html(stripped)
            story.append(Paragraph(num_text, bullet_style))
        elif stripped.startswith("---"):
            story.append(Spacer(1, 4))
        else:
            p_text = clean_inline_html(stripped)
            story.append(Paragraph(p_text, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated PDF: {pdf_path}")

def main():
    rep1_md = BASE_DIR / "TECHNICAL_PROJECT_REPORT.md"
    rep1_docx = BASE_DIR / "TECHNICAL_PROJECT_REPORT.docx"
    rep1_pdf = BASE_DIR / "TECHNICAL_PROJECT_REPORT.pdf"

    rep3_md = BASE_DIR / "CODE_AND_MODEL_REPORT.md"
    rep3_docx = BASE_DIR / "CODE_AND_MODEL_REPORT.docx"
    rep3_pdf = BASE_DIR / "CODE_AND_MODEL_REPORT.pdf"

    print("Generating DOCX & PDF for Report 1 (Technical Project Report)...")
    markdown_to_docx(rep1_md, rep1_docx, "Technical Project Report")
    markdown_to_pdf(rep1_md, rep1_pdf)

    print("\nGenerating DOCX & PDF for Report 3 (Code & Model Report)...")
    markdown_to_docx(rep3_md, rep3_docx, "Code & AI Model Technical Report")
    markdown_to_pdf(rep3_md, rep3_pdf)

    print("\nAll conversions successfully completed!")

if __name__ == "__main__":
    main()
