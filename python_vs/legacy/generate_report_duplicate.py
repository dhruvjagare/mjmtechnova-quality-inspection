
from pathlib import Path
import csv

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from read_drawing import (
    extract_pdf_text,
    extract_part_code,
    extract_material,
    extract_description,
    extract_hole_coordinates,
)

DRAWING_FOLDER = Path("drawings")
OUTPUT_FOLDER = Path("output")
OUTPUT_FOLDER.mkdir(exist_ok=True)


def generate_report(pdf_path):
    # Read the PDF drawing
    text = extract_pdf_text(pdf_path)

    if not text.strip():
        print(f"Could not read text from {pdf_path.name}")
        return

    # Extract drawing information
    part_code = extract_part_code(text)
    material = extract_material(text)
    description = extract_description(text)
    holes = extract_hole_coordinates(text)

    # Create the Excel workbook
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Inspection Report"

    # Title
    sheet.merge_cells("A1:F1")
    sheet["A1"] = "ENGINEERING DRAWING INSPECTION REPORT"
    sheet["A1"].font = Font(
        bold=True, size=14, color="FFFFFF"
    )
    sheet["A1"].fill = PatternFill(
        "solid", fgColor="1F4E78"
    )
    sheet["A1"].alignment = Alignment(horizontal="center")

    # Part details
    sheet["A3"] = "Part Number"
    sheet["B3"] = part_code
    sheet["D3"] = "Part Name"
    sheet["E3"] = description

    sheet["A4"] = "Material"
    sheet["B4"] = material
    sheet["D4"] = "Drawing Revision"
    sheet["E4"] = ""

    # Inspection table headings
    headers = [
        "Sr. No.",
        "Parameter",
        "Nominal Dimension",
        "Tolerance",
        "Actual Measurement",
        "QC Result",
    ]

    header_row = 6

    for column, heading in enumerate(headers, start=1):
        cell = sheet.cell(
            row=header_row, column=column, value=heading
        )
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(
            "solid", fgColor="4472C4"
        )
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )

    # Add X and Y coordinates for every detected hole.
    # Actual measurements, tolerances, and QC results
    # are left blank unless verified information is available.
    row = 7
    serial_number = 1

    for hole in holes:
        label = hole["hole"]

        # X-coordinate row
        sheet.cell(row=row, column=1, value=serial_number)
        sheet.cell(
            row=row, column=2, value=f"{label} - X coordinate"
        )
        sheet.cell(
            row=row,
            column=3,
            value=f'{hole["x_mm"]:g} mm',
        )
        row += 1
        serial_number += 1

        # Y-coordinate row
        sheet.cell(row=row, column=1, value=serial_number)
        sheet.cell(
            row=row, column=2, value=f"{label} - Y coordinate"
        )
        sheet.cell(
            row=row,
            column=3,
            value=f'{hole["y_mm"]:g} mm',
        )
        row += 1
        serial_number += 1

    # Style the inspection table
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    for cells in sheet.iter_rows(
        min_row=3,
        max_row=max(row - 1, 6),
        min_col=1,
        max_col=6,
    ):
        for cell in cells:
            cell.border = thin_border
            cell.alignment = Alignment(
                vertical="center",
                wrap_text=True,
            )

    # Set column widths
    widths = [10, 30, 22, 18, 22, 16]

    for column, width in enumerate(widths, start=1):
        sheet.column_dimensions[
            get_column_letter(column)
        ].width = width

    sheet.freeze_panes = "A7"
    sheet.auto_filter.ref = f"A6:F{max(row - 1, 6)}"

    # Save the report
    output_file = OUTPUT_FOLDER / (
        pdf_path.stem + "_inspection_report.xlsx"
    )
    workbook.save(output_file)

    print(f"\nDrawing: {pdf_path.name}")
    print(f"Part number: {part_code}")
    print(f"Material: {material}")
    print(f"Description: {description}")
    print(f"Hole labels extracted: {len(holes)}")
    print(f"Inspection rows generated: {2 * len(holes)}")
    print(f"Excel report saved: {output_file}")


def main():
    if not DRAWING_FOLDER.exists():
        print("The drawings folder was not found.")
        return

    pdf_files = sorted(
        path for path in DRAWING_FOLDER.iterdir()
        if path.is_file()
        and path.suffix.lower() == ".pdf"
    )

    if not pdf_files:
        print("No PDF drawings found.")
        return

    for pdf_path in pdf_files:
        generate_report(pdf_path)


if __name__ == "__main__":
    main()
