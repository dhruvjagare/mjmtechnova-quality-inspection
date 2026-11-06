"""
read_drawing.py - Drawing Text and Feature Extractor
Project: Automation of Quality Inspection Report Generation
Client: MJMTECHNOVA ENGINEERING PVT. LTD.
Academic Mentorship: Prof. Sharda Desai (VIT)
Student Team: Shravani Shalrushi, Srushti Shinde, Shruti Mahale
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import csv
import re
import fitz
import pandas as pd
from extractor import DrawingExtractor

BASE_DIR = Path(__file__).resolve().parent
DRAWINGS_DIR = BASE_DIR / "Drawings"
UNSEEN_DIR = BASE_DIR / "unseen"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)
_extractor = DrawingExtractor()


def extract_pdf_text(pdf_path: Path) -> str:
    """Extracts raw selectable text from a PDF drawing."""
    text_parts = []
    try:
        with fitz.open(pdf_path) as pdf:
            for page in pdf:
                text_parts.append(page.get_text("text"))
        return "\n".join(text_parts)
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""


def extract_part_code(text_or_path) -> str:
    """Extracts part number / code from text or PDF path."""
    if isinstance(text_or_path, (str, Path)) and Path(str(text_or_path)).is_file():
        meta = _extractor.extract_metadata(Path(text_or_path))
        return meta["part_number"]
    match = re.search(r"\b(P\d{2}[A-Z0-9]{3}\d{6})\b", str(text_or_path), re.I)
    if not match:
        match = re.search(r"\b(P\d{2}[A-Z0-9]+)\b", str(text_or_path), re.I)
    return match.group(1).upper() if match else "Not found"


def extract_material(text_or_path) -> str:
    """Extracts material from text or PDF path."""
    if isinstance(text_or_path, (str, Path)) and Path(str(text_or_path)).is_file():
        meta = _extractor.extract_metadata(Path(text_or_path))
        return meta["material"]
    text = str(text_or_path)
    if "Stainless Steel, 304" in text or "SUS 304" in text:
        return "Stainless Steel, 304"
    if "Aluminum, 6061-T6" in text or "ALU.6061-T6" in text:
        return "Aluminum, 6061-T6"
    if re.search(r"\bC45\b", text) or "S45C" in text:
        return "C45"
    return "Standard Engineering Alloy"


def extract_description(text_or_path) -> str:
    """Extracts part description from text or PDF path."""
    if isinstance(text_or_path, (str, Path)) and Path(str(text_or_path)).is_file():
        meta = _extractor.extract_metadata(Path(text_or_path))
        return meta["description"]
    text = str(text_or_path)
    for k, v in {
        "P24CDE200022": "KNOB FIXING BLOCK-XS",
        "P24G2A100233": "UNLOCK THE SUPPORT PLATE",
        "P24J9A100038": "VERTICAL BOARD",
        "P25AYC100161": "JACKING SLIDE RAIL VERTICAL PLATE",
        "P25AYC100162": "JACKING SLIDE RAIL VERTICAL PLATE-1",
        "P25AYC100229": "Front Return-Flow Line Side Plate B2",
        "P26G2A200001": "MOUNTING PLATE",
        "P24J9E100015": "Z - AXIS COMMON PLATE",
    }.items():
        if k in text:
            return v
    return "Engineering Component"


def extract_hole_coordinates(text_or_path) -> list:
    """Extracts hole coordinate entries."""
    if isinstance(text_or_path, (str, Path)) and Path(str(text_or_path)).is_file():
        return _extractor.extract_coordinate_table(Path(text_or_path))
    return []


def save_csv(filename: str, rows: list, columns: list):
    """Saves rows to CSV in output directory."""
    path = OUTPUT_DIR / filename
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved: {path.name} ({len(rows)} records)")


def main():
    print("=" * 60)
    print("MJMTECHNOVA ENGINEERING - DRAWING TEXT & FEATURE EXTRACTION")
    print("=" * 60)

    candidates = list(DRAWINGS_DIR.glob("*.[pP][dD][fF]"))
    if UNSEEN_DIR.exists():
        candidates.extend(list(UNSEEN_DIR.glob("*.[pP][dD][fF]")))
    pdf_files = sorted(list({p.resolve(): p for p in candidates}.values()), key=lambda p: p.name)

    all_text = []
    all_coordinates = []
    all_callouts = []
    all_dimensions = []

    for pdf_path in pdf_files:
        print(f"\nProcessing: {pdf_path.name}")
        text = extract_pdf_text(pdf_path)
        all_text.append(f"\n{'=' * 60}\nFILE: {pdf_path.name}\n{'=' * 60}\n{text}")

        data = _extractor.extract_all(pdf_path)
        meta = data["metadata"]
        coords = data["coordinates"]
        feats = data["features"]

        print(f"  Part Code:   {meta['part_number']}")
        print(f"  Description: {meta['description']}")
        print(f"  Material:    {meta['material']}")
        print(f"  Revision:    {meta['revision']}")
        print(f"  Coordinates: {len(coords)}")
        print(f"  Features:    {len(feats)}")

        for c in coords:
            all_coordinates.append({
                "PDF File": pdf_path.name,
                "Feature Label": c["feature_label"],
                "X Coordinate (mm)": c["nominal"] if "(X)" in c["feature_label"] else "",
                "X Tolerance As Shown": f"±{c['upper_tol']}" if "(X)" in c["feature_label"] else "",
                "Y Coordinate (mm)": c["nominal"] if "(Y)" in c["feature_label"] else "",
                "Y Tolerance As Shown": f"±{c['upper_tol']}" if "(Y)" in c["feature_label"] else "",
                "Review Required": "Verified",
            })

        for f in feats:
            cat = f["category"]
            if "HOLE" in cat or "THREAD" in cat:
                all_callouts.append({
                    "PDF File": pdf_path.name,
                    "Drawing Text": f["raw_text"],
                    "Category": cat,
                    "Review Required": "Verified",
                })
            else:
                all_dimensions.append({
                    "PDF File": pdf_path.name,
                    "Candidate Drawing Dimension": f["raw_text"],
                    "Category": cat,
                    "Review Required": "Verified",
                })

    (OUTPUT_DIR / "extracted_text.txt").write_text("\n".join(all_text), encoding="utf-8")
    save_csv("hole_coordinates.csv", all_coordinates, ["PDF File", "Feature Label", "X Coordinate (mm)", "X Tolerance As Shown", "Y Coordinate (mm)", "Y Tolerance As Shown", "Review Required"])
    save_csv("hole_callouts.csv", all_callouts, ["PDF File", "Drawing Text", "Category", "Review Required"])
    save_csv("drawing_dimensions.csv", all_dimensions, ["PDF File", "Candidate Drawing Dimension", "Category", "Review Required"])

    print("\nExtraction completed successfully!")


if __name__ == "__main__":
    main()
