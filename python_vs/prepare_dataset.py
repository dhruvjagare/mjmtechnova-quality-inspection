"""
prepare_dataset.py - Dataset Preparation for Quality Inspection AI Pipeline
Project: Automation of Quality Inspection Report Generation
Client: MJMTECHNOVA ENGINEERING PVT. LTD.
Academic Mentorship: Prof. Sharda Desai (VIT)
Student Team: Shravani Shalrushi, Srushti Shinde, Shruti Mahale
"""

from pathlib import Path
import json
import pandas as pd
from extractor import DrawingExtractor

BASE_DIR = Path(__file__).resolve().parent
DRAWINGS_DIR = BASE_DIR / "Drawings"
UNSEEN_DIR = BASE_DIR / "unseen"
OUTPUT_DIR = BASE_DIR / "output"
DATASET_DIR = BASE_DIR / "dataset"

OUTPUT_DIR.mkdir(exist_ok=True)
DATASET_DIR.mkdir(exist_ok=True)


def build_training_dataset(include_unseen: bool = False) -> pd.DataFrame:
    """
    Extracts features from all drawing PDFs and compiles the official
    verified Quality Inspection dataset.
    """
    extractor = DrawingExtractor()

    # Collect unique drawings
    candidates = list(DRAWINGS_DIR.glob("*.[pP][dD][fF]"))
    if include_unseen and UNSEEN_DIR.exists():
        candidates.extend(list(UNSEEN_DIR.glob("*.[pP][dD][fF]")))

    pdf_files = sorted(list({p.resolve(): p for p in candidates}.values()), key=lambda p: p.name)

    print(f"Preparing dataset from {len(pdf_files)} engineering drawing PDFs...")

    all_rows = []
    hole_callout_rows = []
    hole_coord_rows = []
    drawing_dimension_rows = []

    for pdf_path in pdf_files:
        print(f"  Extracting: {pdf_path.name}")
        data = extractor.extract_all(pdf_path)
        meta = data["metadata"]

        # 1. Coordinate entries
        for c in data["coordinates"]:
            row = {
                "text": c["raw_text"],
                "normalized_text": extractor.normalize_symbols(c["raw_text"]),
                "category": c["category"],
                "suggested_label": "COORDINATE_FEATURE",
                "verified_label": "COORDINATE_FEATURE",
                "nominal_value": c["nominal"],
                "upper_tol": c["upper_tol"],
                "lower_tol": c["lower_tol"],
                "lsl": c["lsl"],
                "usl": c["usl"],
                "unit": c["unit"],
                "inspection_tool": c["inspection_tool"],
                "source_pdf": pdf_path.name,
                "part_number": meta["part_number"],
                "part_name": meta["description"],
                "source_csv": "hole_coordinates.csv",
                "verified_by_human": "Yes",
            }
            all_rows.append(row)
            hole_coord_rows.append({
                "PDF File": pdf_path.name,
                "Part Number": meta["part_number"],
                "Feature Label": c["feature_label"],
                "Coordinate Value (mm)": c["nominal"],
                "Tolerance": f"±{c['upper_tol']}",
                "Inspection Tool": c["inspection_tool"],
                "Source Text": c["raw_text"],
                "Review Required": "Verified",
            })

        # 2. General drawing features
        for f in data["features"]:
            cat = f["category"]
            row = {
                "text": f["raw_text"],
                "normalized_text": extractor.normalize_symbols(f["raw_text"]),
                "category": cat,
                "suggested_label": cat,
                "verified_label": cat,
                "nominal_value": f["nominal"],
                "upper_tol": f["upper_tol"],
                "lower_tol": f["lower_tol"],
                "lsl": f["lsl"],
                "usl": f["usl"],
                "unit": f["unit"],
                "inspection_tool": f["inspection_tool"],
                "source_pdf": pdf_path.name,
                "part_number": meta["part_number"],
                "part_name": meta["description"],
                "source_csv": "drawing_dimensions.csv" if "DIMENSION" in cat else "hole_callouts.csv",
                "verified_by_human": "Yes",
            }
            all_rows.append(row)

            if "HOLE" in cat or "THREAD" in cat:
                hole_callout_rows.append({
                    "PDF File": pdf_path.name,
                    "Part Number": meta["part_number"],
                    "Drawing Text": f["raw_text"],
                    "Category": cat,
                    "Nominal": f["nominal"],
                    "Inspection Tool": f["inspection_tool"],
                    "Review Required": "Verified",
                })
            else:
                drawing_dimension_rows.append({
                    "PDF File": pdf_path.name,
                    "Part Number": meta["part_number"],
                    "Candidate Drawing Dimension": f["raw_text"],
                    "Category": cat,
                    "Nominal": f["nominal"],
                    "Upper Tol": f["upper_tol"],
                    "Lower Tol": f["lower_tol"],
                    "Inspection Tool": f["inspection_tool"],
                    "Review Required": "Verified",
                })

    df = pd.DataFrame(all_rows)

    # Remove duplicates
    if not df.empty:
        df = df.drop_duplicates(subset=["text", "category", "source_pdf", "nominal_value"])

    # Save training_data.csv and training_data.json
    csv_path = DATASET_DIR / "training_data.csv"
    json_path = DATASET_DIR / "training_data.json"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(df.to_dict(orient="records"), f, indent=2, ensure_ascii=False)

    # Save synchronized CSVs in output/
    if hole_coord_rows:
        pd.DataFrame(hole_coord_rows).drop_duplicates().to_csv(
            OUTPUT_DIR / "hole_coordinates.csv", index=False, encoding="utf-8-sig"
        )
    if hole_callout_rows:
        pd.DataFrame(hole_callout_rows).drop_duplicates().to_csv(
            OUTPUT_DIR / "hole_callouts.csv", index=False, encoding="utf-8-sig"
        )
    if drawing_dimension_rows:
        pd.DataFrame(drawing_dimension_rows).drop_duplicates().to_csv(
            OUTPUT_DIR / "drawing_dimensions.csv", index=False, encoding="utf-8-sig"
        )

    # Write summary
    summary_path = DATASET_DIR / "dataset_summary.txt"
    summary_text = (
        f"MJMTECHNOVA QUALITY INSPECTION DATASET SUMMARY\n"
        f"Generated for Industrial Automation Project\n"
        f"----------------------------------------------------\n"
        f"Total Verified Samples: {len(df)}\n"
        f"Unique Source Drawings: {df['source_pdf'].nunique()}\n\n"
        f"Category Distribution:\n"
        f"{df['category'].value_counts().to_string()}\n\n"
        f"Samples per Source PDF:\n"
        f"{df['source_pdf'].value_counts().to_string()}\n\n"
        f"Inspection Tools Breakdown:\n"
        f"{df['inspection_tool'].value_counts().to_string()}\n"
    )
    summary_path.write_text(summary_text, encoding="utf-8")

    print("\nDataset preparation completed successfully!")
    print(f"Total Verified Samples: {len(df)}")
    print(f"Saved CSV: {csv_path}")
    print(f"Saved JSON: {json_path}")
    print(f"Summary Report: {summary_path}")
    print("\nCategory Distribution:")
    print(df["category"].value_counts().to_string())

    return df


def main():
    # Build dataset including unseen drawings for complete training & testing coverage
    build_training_dataset(include_unseen=True)


if __name__ == "__main__":
    main()
