"""
test_pipeline.py - Automated Unit & Integration Tests
Project: Automation of Quality Inspection Report Generation
Client: MJMTECHNOVA ENGINEERING PVT. LTD.
Academic Mentorship: Prof. Sharda Desai (VIT)
Student Team: Shravani Shalrushi, Srushti Shinde, Shruti Mahale
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from pathlib import Path
import unittest
import openpyxl
import pandas as pd

from extractor import DrawingExtractor
from ml_classifier import DrawingAnnotationClassifier

BASE_DIR = Path(__file__).resolve().parent
DRAWINGS_DIR = BASE_DIR / "Drawings"
UNSEEN_DIR = BASE_DIR / "unseen"
OUTPUT_DIR = BASE_DIR / "output"
DATASET_DIR = BASE_DIR / "dataset"


class TestDrawingAutomation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.extractor = DrawingExtractor()
        cls.classifier = DrawingAnnotationClassifier()

    def test_01_all_drawings_exist(self):
        """Verifies that 7 training drawings and 1 unseen drawing exist."""
        train_pdfs = list(DRAWINGS_DIR.glob("*.[pP][dD][fF]"))
        self.assertEqual(len(train_pdfs), 7, f"Expected 7 training drawings, found {len(train_pdfs)}")

        unseen_pdfs = list(UNSEEN_DIR.glob("*.[pP][dD][fF]"))
        self.assertEqual(len(unseen_pdfs), 1, f"Expected 1 unseen drawing, found {len(unseen_pdfs)}")

    def test_02_metadata_extraction(self):
        """Verifies metadata extraction on sample drawings."""
        p_cde = DRAWINGS_DIR / "P24CDE2000220005 (1).PDF"
        meta = self.extractor.extract_metadata(p_cde)
        self.assertEqual(meta["part_number"], "P24CDE200022")
        self.assertEqual(meta["description"], "KNOB FIXING BLOCK-XS")
        self.assertIn("304", meta["material"])
        self.assertEqual(meta["revision"], "01")

        p_unseen = UNSEEN_DIR / "P24J9E1000150019 (1).PDF"
        meta_unseen = self.extractor.extract_metadata(p_unseen)
        self.assertEqual(meta_unseen["part_number"], "P24J9E100015")
        self.assertEqual(meta_unseen["description"], "Z - AXIS COMMON PLATE")
        self.assertEqual(meta_unseen["revision"], "06")

    def test_03_coordinate_table_extraction(self):
        """Verifies hole table extraction for drawings with coordinate tables."""
        p_coord = DRAWINGS_DIR / "P25AYC100229001 (1).PDF"
        coords = self.extractor.extract_coordinate_table(p_coord)
        self.assertGreaterEqual(len(coords), 50, "P25AYC100229 coordinate count mismatch")

        p_hole_table = DRAWINGS_DIR / "P26G2A2000010010 (1).PDF"
        coords_g2a = self.extractor.extract_coordinate_table(p_hole_table)
        self.assertGreaterEqual(len(coords_g2a), 60, "P26G2A coordinate count mismatch")

    def test_04_dataset_integrity(self):
        """Verifies dataset file presence, schema, and noise-free contents."""
        csv_path = DATASET_DIR / "training_data.csv"
        self.assertTrue(csv_path.exists(), "training_data.csv not found")

        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        self.assertGreater(len(df), 400, "Dataset should have >400 verified samples")

        # Verify no contaminated title block border tolerance noise
        noise_samples = df[df["text"].isin(["±1.0", "±0.05", "±0.1", "±0.2", "±0.3", "±0.5"])]
        self.assertEqual(len(noise_samples), 0, "Dataset contains unfiltered border tolerance noise")

        # Verify critical columns exist
        expected_cols = ["text", "normalized_text", "category", "nominal_value", "upper_tol", "lower_tol", "inspection_tool", "source_pdf"]
        for col in expected_cols:
            self.assertIn(col, df.columns, f"Missing column {col} in dataset")

    def test_05_classifier_predictions(self):
        """Verifies AI classifier categorizes unseen patterns correctly."""
        tests = [
            ("M6 - 6H THRU", "THREAD_CALLOUT"),
            ("3x Ø4.5 THRU", "HOLE_CALLOUT"),
            ("16±0.02", "TOLERANCED_DIMENSION"),
            ("250.0 mm", "LINEAR_DIMENSION"),
            ("0.5 x 45°", "CHAMFER"),
            ("R 5 TYP", "RADIUS"),
        ]
        for text, expected in tests:
            res = self.classifier.predict(text)
            self.assertEqual(res["predicted_category"], expected, f"Failed prediction on '{text}': got {res['predicted_category']}, expected {expected}")

    def test_06_excel_inspection_reports(self):
        """Verifies generated Excel inspection reports for all drawings."""
        xlsx_files = list(OUTPUT_DIR.glob("*_inspection_report.xlsx"))
        self.assertEqual(len(xlsx_files), 8, f"Expected 8 reports, found {len(xlsx_files)}")

        for xfile in xlsx_files:
            wb = openpyxl.load_workbook(xfile, data_only=False)
            self.assertIn("Quality Inspection Report", wb.sheetnames)
            ws = wb["Quality Inspection Report"]

            # Check header branding
            self.assertEqual(ws["A1"].value, "MJMTECHNOVA ENGINEERING PVT. LTD.")
            self.assertIn("AUTOMATED QUALITY INSPECTION REPORT", str(ws["A2"].value))

            # Check part metadata exists
            self.assertTrue(bool(ws["C5"].value), f"Part number missing in {xfile.name}")
            self.assertTrue(bool(ws["C6"].value), f"Description missing in {xfile.name}")

            # Check table header
            self.assertEqual(ws["A11"].value, "Sr. No.")
            self.assertEqual(ws["B11"].value, "Characteristic / Parameter")

            # Check data row exists
            self.assertIsNotNone(ws["A12"].value, f"No inspection rows in {xfile.name}")
            self.assertIn("ROUND", str(ws["K12"].value), f"Deviation formula missing in {xfile.name}")
            self.assertIn("IF", str(ws["L12"].value), f"QC result formula missing in {xfile.name}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
