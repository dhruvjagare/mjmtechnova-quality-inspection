
from pathlib import Path
import re
import csv
import pymupdf

# --------------------------------------------------
# 1. Project folders
# --------------------------------------------------

DRAWING_FOLDER = Path("drawings")
OUTPUT_FOLDER = Path("output")

OUTPUT_FOLDER.mkdir(exist_ok=True)


# --------------------------------------------------
# 2. Extract text from a PDF
# --------------------------------------------------

def extract_pdf_text(pdf_path):
    """Extract selectable text from a PDF drawing."""

    try:
        with pymupdf.open(pdf_path) as document:
            return "\n".join(
                page.get_text() for page in document
            )

    except Exception as error:
        print(f"Error reading {pdf_path.name}: {error}")
        return ""


# --------------------------------------------------
# 3. Extract part number
# --------------------------------------------------

def extract_part_code(text):
    normalized_text = re.sub(r"\s+", " ", text)

    pattern = r"\bP\d+[A-Z]+\d+\b"
    matches = re.findall(pattern, normalized_text, re.IGNORECASE)

    for code in matches:
        code = code.upper()

        if code.startswith(("P24CDE", "P25AYC")):
            return code

    return "Not found"


# --------------------------------------------------
# 4. Extract material
# --------------------------------------------------

def extract_material(text):
    patterns = [
        r"Stainless\s+Steel\s*,?\s*\d+",
        r"Alumin(?:um|ium)\s*,?\s*6061-T6",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(0).strip()

    return "Not found"


# --------------------------------------------------
# 5. Extract description
# --------------------------------------------------

def extract_description(text):
    normalized_text = re.sub(r"\s+", " ", text).strip()

    descriptions = [
        r"Front Return-Flow Line Side Plate B2",
        r"JACKING SLIDE RAIL VERTICAL PLATE-1",
        r"JACKING SLIDE RAIL VERTICAL PLATE",
        r"203002112D953_03-13 KNOB FIXING BLOCK-XS",
    ]

    for pattern in descriptions:
        match = re.search(
            pattern, normalized_text, re.IGNORECASE
        )

        if match:
            return match.group(0)

    return "Not found"


# --------------------------------------------------
# 6. Extract hole coordinates
# --------------------------------------------------

def extract_hole_coordinates(text):
    """
    Extract hole labels and X/Y coordinates when the
    PDF text presents them as separate, readable lines.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    holes = []

    hole_pattern = re.compile(
        r"^[ABC]\.\d+$",
        re.IGNORECASE
    )

    coordinate_pattern = re.compile(
        r"^(-?\d+(?:\.\d+)?)\s*mm$",
        re.IGNORECASE
    )

    for index, line in enumerate(lines):

        if not hole_pattern.fullmatch(line):
            continue

        # Collect text until the next hole label
        block = []

        for next_line in lines[index + 1:]:
            if hole_pattern.fullmatch(next_line):
                break

            block.append(next_line)

        # Find coordinate values explicitly marked in mm
        coordinates = []

        for item in block:
            match = coordinate_pattern.fullmatch(item)

            if match:
                coordinates.append(float(match.group(1)))

        # Save a row only when both coordinates are found
        if len(coordinates) >= 2:
            holes.append({
                "hole": line,
                "x_mm": coordinates[0],
                "y_mm": coordinates[1],
            })

    return holes


# --------------------------------------------------
# 7. Process one drawing
# --------------------------------------------------

def process_drawing(pdf_path, all_text, all_holes):

    print("\n" + "=" * 50)
    print(f"Drawing: {pdf_path.name}")

    text = extract_pdf_text(pdf_path)

    if not text.strip():
        print("No readable text extracted.")
        return

    part_code = extract_part_code(text)
    material = extract_material(text)
    description = extract_description(text)

    print(f"Part number: {part_code}")
    print(f"Material: {material}")
    print(f"Description: {description}")

    # Save full extracted text
    all_text.append(
        f"\n{'=' * 50}\n"
        f"Drawing: {pdf_path.name}\n\n"
        f"{text}\n"
    )

    # Extract hole coordinates
    holes = extract_hole_coordinates(text)

    print(f"Hole-coordinate rows found: {len(holes)}")

    for hole in holes:
        print(
            f"{hole['hole']}: "
            f"X = {hole['x_mm']} mm, "
            f"Y = {hole['y_mm']} mm"
        )

        all_holes.append({
            "drawing": pdf_path.name,
            "part_number": part_code,
            "hole": hole["hole"],
            "x_mm": hole["x_mm"],
            "y_mm": hole["y_mm"],
        })


# --------------------------------------------------
# 8. Main program
# --------------------------------------------------

def main():

    if not DRAWING_FOLDER.exists():
        print("The drawings folder was not found.")
        return

    pdf_files = sorted(
        file for file in DRAWING_FOLDER.iterdir()
        if file.is_file()
        and file.suffix.lower() == ".pdf"
    )

    if not pdf_files:
        print("No PDF drawings found.")
        return

    all_text = []
    all_holes = []

    for pdf_path in pdf_files:
        process_drawing(pdf_path, all_text, all_holes)

    # Save extracted text
    text_file = OUTPUT_FOLDER / "extracted_text.txt"

    text_file.write_text(
        "\n".join(all_text),
        encoding="utf-8"
    )

    # Save hole-coordinate data as CSV
    csv_file = OUTPUT_FOLDER / "hole_coordinates.csv"

    columns = [
        "drawing",
        "part_number",
        "hole",
        "x_mm",
        "y_mm",
    ]

    with csv_file.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=columns
        )

        writer.writeheader()
        writer.writerows(all_holes)

    print("\n" + "=" * 50)
    print(f"Extracted text saved to: {text_file}")
    print(f"Hole coordinates saved to: {csv_file}")
    print("Processing completed!")


# --------------------------------------------------
# 9. Start program
# --------------------------------------------------

if __name__ == "__main__":
    main()
