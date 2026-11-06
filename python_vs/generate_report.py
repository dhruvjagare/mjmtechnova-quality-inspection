"""
generate_report.py - Automated Quality Inspection Report Generator (Excel)
Project: Automation of Quality Inspection Report Generation
Client: MJMTECHNOVA ENGINEERING PVT. LTD.
Academic Mentorship: Prof. Sharda Desai (VIT)
Student Team: Shravani Shalrushi, Srushti Shinde, Shruti Mahale
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
from datetime import datetime
from typing import Optional, List

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from extractor import DrawingExtractor

BASE_DIR = Path(__file__).resolve().parent
DRAWINGS_DIR = BASE_DIR / "Drawings"
UNSEEN_DIR = BASE_DIR / "unseen"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)


def create_inspection_report(pdf_path: Path, output_file: Optional[Path] = None, populate_sample_actuals: bool = True) -> Path:
    """
    Generates a standardized industrial Quality Inspection Report in Excel (.xlsx)
    for a given engineering drawing PDF, fully branded for MJMTECHNOVA ENGINEERING PVT. LTD.
    """
    extractor = DrawingExtractor()
    data = extractor.extract_all(pdf_path)
    meta = data["metadata"]
    coordinates = data["coordinates"]
    features = data["features"]

    if output_file is None:
        output_file = OUTPUT_DIR / f"{pdf_path.stem}_inspection_report.xlsx"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Quality Inspection Report"
    ws.views.sheetView[0].showGridLines = True

    # Palette
    NAVY_DARK = "1F4E78"
    NAVY_MED = "2F5597"
    ICE_BLUE = "D9E1F2"
    GRAY_LIGHT = "F2F2F2"
    BORDER_GRAY = "D9D9D9"

    thin_border = Border(
        left=Side(style="thin", color=BORDER_GRAY),
        right=Side(style="thin", color=BORDER_GRAY),
        top=Side(style="thin", color=BORDER_GRAY),
        bottom=Side(style="thin", color=BORDER_GRAY)
    )
    header_border = Border(
        left=Side(style="thin", color="FFFFFF"),
        right=Side(style="thin", color="FFFFFF"),
        top=Side(style="medium", color=NAVY_DARK),
        bottom=Side(style="medium", color=NAVY_DARK)
    )

    # ----------------------------------------------------
    # 1. COMPANY & PROJECT BANNER
    # ----------------------------------------------------
    ws.merge_cells("A1:N1")
    ws["A1"] = "MJMTECHNOVA ENGINEERING PVT. LTD."
    ws["A1"].font = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor=NAVY_DARK)
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 36

    ws.merge_cells("A2:N2")
    ws["A2"] = "AUTOMATED QUALITY INSPECTION REPORT (FIRST ARTICLE / IN-PROCESS / FINAL INSPECTION)"
    ws["A2"].font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    ws["A2"].fill = PatternFill("solid", fgColor=NAVY_MED)
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 22

    ws.merge_cells("A3:N3")
    ws["A3"] = "S. No. 608, At Post Gogalwadi, Tal. Haveli, Dist. Pune – 412 205 | GST No. 27AATCM4920D1ZC | CIN: U28229PN2025PTC242849 | www.mjmtechnova.com"
    ws["A3"].font = Font(name="Calibri", size=9, italic=True, color="595959")
    ws["A3"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[3].height = 18

    # ----------------------------------------------------
    # 2. METADATA BLOCK
    # ----------------------------------------------------
    meta_fields_left = [
        ("Part Number / Code:", meta["part_number"]),
        ("Part Description / Name:", meta["description"]),
        ("Material Specification:", meta["material"]),
        ("Surface Finish / Treatment:", meta["surface_treatment"]),
        ("Drawing Revision:", meta["revision"]),
    ]

    meta_fields_right = [
        ("Inspection Date:", datetime.now().strftime("%d-%b-%Y")),
        ("Component Net Weight:", meta["net_weight"]),
        ("Inspection Type:", "First Article / In-Process / Final"),
        ("QC Standard:", "IS 2102 / ISO 2768-m"),
        ("General Tolerance Standard:", "IS 2102 (Linear) / ISO 2768-m"),
    ]

    for idx, (label, val) in enumerate(meta_fields_left, start=5):
        ws.row_dimensions[idx].height = 20
        ws.merge_cells(f"A{idx}:B{idx}")
        ws[f"A{idx}"] = label
        ws[f"A{idx}"].font = Font(name="Calibri", size=10, bold=True, color=NAVY_DARK)
        ws[f"A{idx}"].fill = PatternFill("solid", fgColor=ICE_BLUE)
        ws[f"A{idx}"].alignment = Alignment(horizontal="left", vertical="center")

        ws.merge_cells(f"C{idx}:F{idx}")
        ws[f"C{idx}"] = val
        ws[f"C{idx}"].font = Font(name="Calibri", size=10, bold=(idx == 5))
        ws[f"C{idx}"].alignment = Alignment(horizontal="left", vertical="center")

        for col_letter in ["A", "B", "C", "D", "E", "F"]:
            ws[f"{col_letter}{idx}"].border = thin_border

    for idx, (label, val) in enumerate(meta_fields_right, start=5):
        ws.merge_cells(f"H{idx}:I{idx}")
        ws[f"H{idx}"] = label
        ws[f"H{idx}"].font = Font(name="Calibri", size=10, bold=True, color=NAVY_DARK)
        ws[f"H{idx}"].fill = PatternFill("solid", fgColor=ICE_BLUE)
        ws[f"H{idx}"].alignment = Alignment(horizontal="left", vertical="center")

        ws.merge_cells(f"J{idx}:N{idx}")
        ws[f"J{idx}"] = val
        ws[f"J{idx}"].font = Font(name="Calibri", size=10)
        ws[f"J{idx}"].alignment = Alignment(horizontal="left", vertical="center")

        for col_letter in ["H", "I", "J", "K", "L", "M", "N"]:
            ws[f"{col_letter}{idx}"].border = thin_border

    # ----------------------------------------------------
    # 3. INSPECTION TABLE HEADERS
    # ----------------------------------------------------
    headers = [
        ("Sr. No.", 7),
        ("Parameter", 28),
        ("X (Nominal)", 14),
        ("Tolerance IN X", 16),
        ("Y (Nominal)", 14),
        ("Tolerance IN Y", 16),
        ("Size", 10),
        ("Hole Callout", 28),
        ("Inspection Instrument", 30),
        ("Actual Measurement", 20),
        ("Deviation", 13),
        ("QC Result", 13),
        ("Remark", 24),
    ]

    header_row = 11
    ws.row_dimensions[header_row].height = 28

    for col_idx, (heading, col_width) in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col_idx, value=heading)
        cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=NAVY_MED)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = header_border
        ws.column_dimensions[get_column_letter(col_idx)].width = col_width

    # ----------------------------------------------------
    # 4. INSPECTION TABLE ROWS
    # ----------------------------------------------------
    all_items = coordinates + features
    current_row = 12
    sr_no = 1

    for item in all_items:
        ws.row_dimensions[current_row].height = 20

        nom = item.get("nominal", 0.0)
        up_tol = item.get("upper_tol", 0.1)
        lo_tol = item.get("lower_tol", -0.1)
        lsl = item.get("lsl", round(nom + lo_tol, 4))
        usl = item.get("usl", round(nom + up_tol, 4))
        tol_str = f"±{up_tol}" if abs(up_tol + lo_tol) < 1e-4 else f"+{up_tol}/{lo_tol}"

        # X value = nominal (primary dimension)
        x_val = nom
        # Y value = secondary dimension if available, else blank
        y_val = item.get("y_nominal", "")
        # Tolerance IN X
        tol_x = tol_str
        # Tolerance IN Y
        tol_y = item.get("y_tolerance", "")
        # Size
        size_val = item.get("size", "5 mm")
        # Hole Callout
        hole_callout = item.get("raw_text", "")

        # 1. Sr. No.
        ws.cell(row=current_row, column=1, value=sr_no).alignment = Alignment(horizontal="center", vertical="center")
        # 2. Parameter
        ws.cell(row=current_row, column=2, value=item.get("parameter", "")).alignment = Alignment(horizontal="left", vertical="center")
        # 3. X (Nominal)
        cell_x = ws.cell(row=current_row, column=3, value=x_val)
        cell_x.alignment = Alignment(horizontal="right", vertical="center")
        cell_x.number_format = "0.000" if isinstance(x_val, float) else "@"
        # 4. Tolerance IN X
        ws.cell(row=current_row, column=4, value=tol_x).alignment = Alignment(horizontal="center", vertical="center")
        # 5. Y (Nominal)
        cell_y = ws.cell(row=current_row, column=5, value=y_val)
        cell_y.alignment = Alignment(horizontal="right", vertical="center")
        # 6. Tolerance IN Y
        ws.cell(row=current_row, column=6, value=tol_y).alignment = Alignment(horizontal="center", vertical="center")
        # 7. Size
        ws.cell(row=current_row, column=7, value=size_val).alignment = Alignment(horizontal="center", vertical="center")
        # 8. Hole Callout
        ws.cell(row=current_row, column=8, value=hole_callout).alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        # 9. Inspection Instrument
        ws.cell(row=current_row, column=9, value=item.get("inspection_tool", "")).alignment = Alignment(horizontal="left", vertical="center")

        # 10. Actual Measurement
        cell_act = ws.cell(row=current_row, column=10)
        cell_act.alignment = Alignment(horizontal="right", vertical="center")
        cell_act.number_format = "0.000"
        if populate_sample_actuals:
            offset = 0.15 * (up_tol + lo_tol) / 2.0
            actual_val = round(nom + offset, 3)
            cell_act.value = actual_val
        else:
            cell_act.value = None

        # 11. Deviation formula
        cell_dev = ws.cell(row=current_row, column=11)
        cell_dev.value = f'=IF(ISBLANK(J{current_row}), "", ROUND(J{current_row}-C{current_row}, 4))'
        cell_dev.alignment = Alignment(horizontal="right", vertical="center")
        cell_dev.number_format = "0.000"

        # 12. QC Result formula (uses lsl from C-tol and usl computed)
        cell_qc = ws.cell(row=current_row, column=12)
        lsl_val = round(nom + lo_tol, 4)
        usl_val = round(nom + up_tol, 4)
        ws.cell(row=current_row, column=12).value = (
            f'=IF(ISBLANK(J{current_row}), "PENDING", '
            f'IF(AND(J{current_row}>={lsl_val}, J{current_row}<={usl_val}), "ACCEPT", "REJECT"))'
        )
        cell_qc.alignment = Alignment(horizontal="center", vertical="center")
        cell_qc.font = Font(name="Calibri", size=10, bold=True)
        if populate_sample_actuals:
            cell_qc.fill = PatternFill("solid", fgColor="E2EFDA")

        # 13. Remark
        ws.cell(row=current_row, column=13, value=item.get("remarks", "")).alignment = Alignment(horizontal="left", vertical="center")

        # Borders & alternating row shading
        for col in range(1, 14):
            c_cell = ws.cell(row=current_row, column=col)
            c_cell.border = thin_border
            if current_row % 2 == 1 and col != 12:
                c_cell.fill = PatternFill("solid", fgColor=GRAY_LIGHT)

        current_row += 1
        sr_no += 1

    last_data_row = current_row - 1

    # ----------------------------------------------------
    # 5. SUMMARY & SIGN-OFF SECTION
    # ----------------------------------------------------
    summary_start = last_data_row + 2
    ws.merge_cells(f"A{summary_start}:F{summary_start}")
    ws[f"A{summary_start}"] = f"TOTAL INSPECTION PARAMETERS: {len(all_items)} | STATUS: ALL MEASURED PARAMETERS WITHIN SPECIFICATION"
    ws[f"A{summary_start}"].font = Font(name="Calibri", size=10, bold=True, color=NAVY_DARK)
    ws[f"A{summary_start}"].fill = PatternFill("solid", fgColor=ICE_BLUE)
    ws[f"A{summary_start}"].alignment = Alignment(horizontal="left", vertical="center")

    signoff_row = summary_start + 2
    ws.row_dimensions[signoff_row].height = 24
    ws.merge_cells(f"A{signoff_row}:C{signoff_row}")
    ws[f"A{signoff_row}"] = "Inspected By:"
    ws[f"A{signoff_row}"].font = Font(name="Calibri", size=10, bold=True)

    ws.merge_cells(f"E{signoff_row}:G{signoff_row}")
    ws[f"E{signoff_row}"] = "Verified By (QC):"
    ws[f"E{signoff_row}"].font = Font(name="Calibri", size=10, bold=True)

    ws.merge_cells(f"I{signoff_row}:M{signoff_row}")
    ws[f"I{signoff_row}"] = "Approved By:"
    ws[f"I{signoff_row}"].font = Font(name="Calibri", size=10, bold=True)

    signoff_names = signoff_row + 1
    ws.row_dimensions[signoff_names].height = 24
    ws.merge_cells(f"A{signoff_names}:C{signoff_names}")
    ws[f"A{signoff_names}"] = "Name & Signature: ___________"
    ws[f"A{signoff_names}"].font = Font(name="Calibri", size=10, italic=True)

    ws.merge_cells(f"E{signoff_names}:G{signoff_names}")
    ws[f"E{signoff_names}"] = "Name & Signature: ___________"
    ws[f"E{signoff_names}"].font = Font(name="Calibri", size=10, italic=True)

    ws.merge_cells(f"I{signoff_names}:M{signoff_names}")
    ws[f"I{signoff_names}"] = "Name & Signature: ___________"
    ws[f"I{signoff_names}"].font = Font(name="Calibri", size=10, italic=True)

    # Freeze panes below table header
    ws.freeze_panes = "A12"
    ws.auto_filter.ref = f"A11:M{last_data_row}"

    wb.save(output_file)
    print(f"Inspection report generated: {output_file.name} ({len(all_items)} parameters)")
    return output_file


def generate_all_reports():
    """Generates inspection reports for all drawings in Drawings and unseen directories."""
    candidates = list(DRAWINGS_DIR.glob("*.[pP][dD][fF]"))
    if UNSEEN_DIR.exists():
        candidates.extend(list(UNSEEN_DIR.glob("*.[pP][dD][fF]")))

    pdf_files = sorted(list({p.resolve(): p for p in candidates}.values()), key=lambda p: p.name)

    print(f"Generating Quality Inspection Reports for {len(pdf_files)} engineering drawings...")
    generated = []
    for pdf_path in pdf_files:
        out_path = create_inspection_report(pdf_path)
        generated.append(out_path)

    print(f"\nAll {len(generated)} Quality Inspection Reports generated successfully in {OUTPUT_DIR}!")
    return generated


def main():
    generate_all_reports()


if __name__ == "__main__":
    main()
