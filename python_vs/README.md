# Automation of Quality Inspection Report Generation to Reduce Manual Efforts

**Industrial Project Letter of Intent (LOI)**  
**Client / Industry Partner:** MJMTECHNOVA ENGINEERING PVT. LTD.  
*S. No. 608, At Post Gogalwadi, Tal. Haveli, Dist. Pune – 412 205, Maharashtra, India.*  
*GST No.: 27AATCM4920D1ZC | CIN: U28229PN2025PTC242849 | Web: [www.mjmtechnova.com](http://www.mjmtechnova.com)*  

---

### Academic Mentorship & Project Team
* **VIT Faculty Mentor:** Prof. Sharda Desai
* **Student Engineers Assigned:**
  1. **Shravani Prashant Shalrushi**
  2. **Srushti Pradip Shinde**
  3. **Shruti Vilas Mahale**

---

## 1. Executive Summary & Industrial Background

In traditional manufacturing and precision engineering facilities, **Quality Inspection Reports (First Article Inspection, In-Process QC, and Final Pre-Dispatch Inspection)** require extensive manual effort. Quality assurance personnel must manually inspect 2D engineering drawings, read dimensions, record tolerances, calculate upper/lower specification limits, decide on measuring instruments, and transcribe data into Excel templates.

This manual process leads to:
* **Data-entry errors** and transcription mistakes
* **Calculation errors** for asymmetric/symmetric tolerance limits (USL/LSL)
* **Inconsistent formatting** and lack of traceability
* **Delays** in shop-floor sign-off and dispatch documentation

As part of **MJMTECHNOVA ENGINEERING PVT. LTD.**'s continuous improvement and digitalization initiatives, this project delivers a **fully automated, AI-assisted Quality Inspection Report Generation System** directly from 2D CAD engineering drawings (PDFs).

---

## 2. Why the Original Dataset Was Incorrect & How It Was Fixed

### The Problem in the Initial Implementation:
1. **Title Block Tolerance Contamination:** The general tolerance table from the drawing frame border (`±1.0`, `±0.2`, `±0.05`, `±0.1`, `±0.15`, `±0.3`, `±0.5`, `±0.8`, `±1.2`, `±2.0`, `±3.0`) was repeatedly extracted as part dimensions (>50% of the original dataset was noise).
2. **Missing Real Dimensions:** Standard linear dimensions (e.g., `18`, `26`, `204.5`, `360`, `510`, `145`) were omitted because earlier scripts looked only for numbers ending in `"mm"`. In engineering drawings, linear dimensions follow Drawing Note 1: *"ALL DIMENSIONS ARE IN mm"* and do not repeat the `"mm"` suffix.
3. **Misclassified Manufacturing Notes:** Notes like `"1. DEBURRING OF SHARP EDGES AND HOLES (LESS THAN 0.3MM), AND"` were incorrectly labeled as `DIMENSION`.
4. **Omission of Drawings:** The previous code hardcoded prefixes `P24CDE` and `P25AYC`, completely skipping `P24G2A`, `P24J9A`, `P26G2A`, and `P24J9E`. Materials like `C45`, `S45C`, `ALU.6061-T6`, and `SUS 304` were returning `"Not found"`.
5. **Symbol Corruption:** Corrupted CAD characters (e.g. depth backtick `` ` ``, diameter `Ã˜`/`O`, degree symbols) caused broken entries.

### The Solution:
The updated system extracts **459 verified, high-quality, noise-free engineering characteristics** across all drawings:
* **`LINEAR_DIMENSION` (219 samples):** Auto-mapped to standard general tolerances per **IS 2102-m / ISO 2768-m**.
* **`COORDINATE_FEATURE` (138 samples):** Multi-column Hole Tables & datum coordinate entries extracted with X and Y values.
* **`HOLE_CALLOUT` (26 samples):** Clearance holes, reamed holes (H7), counterbores, and depths.
* **`THREAD_CALLOUT` (24 samples):** Metric internal threads (`M3`, `M4`, `M5`, `M6`, `M10`, fine pitch `M5x0.5 - 6H`).
* **`TOLERANCED_DIMENSION` (22 samples):** Symmetric (`16±0.02`, `1.5±0.01`, `8±0.5`) and asymmetric limit tolerances (`250 +0.03/+0.01`, `25 -0.01/-0.03`).
* **`RADIUS` (17 samples):** Internal and external fillets (`R 0.5`, `R 2 TYP`, `R 3`, `R 5`, `R 10 8X`).
* **`GEOMETRIC_TOLERANCE` (8 samples):** GD&T symbols (True Position `⌖ 0.05 A`, Parallelism `// 0.03`, Runout).
* **`CHAMFER` (5 samples):** Edge chamfers (`0.5 x 45°`, `1 x 45°`, `4-C1`).

---

## 3. Architecture & File Structure

```
d:/python_vs/python_vs/
│
├── Drawings/                         # Primary training & evaluation drawings (7 PDFs)
│   ├── P24CDE2000220005 (1).PDF      # Knob Fixing Block (SUS 304)
│   ├── P24G2A100233007 (2).PDF       # Unlock Support Plate (C45, Ni-plated)
│   ├── P24J9A1000380010 (2).PDF      # Vertical Board (ALU 6061-T6, 2 Pages)
│   ├── P25AYC100161001 (1).PDF       # Jacking Slide Rail Vertical Plate
│   ├── P25AYC100162001.PDF           # Jacking Slide Rail Vertical Plate-1
│   ├── P25AYC100229001 (1).PDF       # Side Plate B2 (with 31-hole Coordinate Table)
│   └── P26G2A2000010010 (1).PDF      # Mounting Plate (C45, 2 Pages, 38-hole Table)
│
├── unseen/                           # Unseen test drawing
│   └── P24J9E1000150019 (1).PDF      # Z-Axis Common Plate (S45C, Rev 06)
│
├── dataset/                          # Clean, verified dataset artifacts
│   ├── training_data.csv             # 459 verified engineering annotations
│   ├── training_data.json            # Structured JSON dataset
│   ├── dataset_summary.txt           # Statistical distribution breakdown
│   ├── drawing_text_classifier.pkl   # Trained scikit-learn NLP classification model
│   └── model_evaluation.txt          # 5-fold cross-validation metrics (99.57% accuracy)
│
├── output/                           # Generated Quality Inspection Excel Reports
│   ├── P24CDE2000220005 (1)_inspection_report.xlsx
│   ├── P24G2A100233007 (2)_inspection_report.xlsx
│   ├── P24J9A1000380010 (2)_inspection_report.xlsx
│   ├── P24J9E1000150019 (1)_inspection_report.xlsx
│   ├── P25AYC100161001 (1)_inspection_report.xlsx
│   ├── P25AYC100162001_inspection_report.xlsx
│   ├── P25AYC100229001 (1)_inspection_report.xlsx
│   ├── P26G2A2000010010 (1)_inspection_report.xlsx
│   ├── hole_coordinates.csv          # 138 coordinate records
│   ├── hole_callouts.csv             # 50 hole/thread records
│   └── drawing_dimensions.csv        # 271 dimension records
│
├── extractor.py                      # Core DrawingExtractor engine
├── prepare_dataset.py                # Verified dataset builder
├── ml_classifier.py                  # Scikit-learn NLP model training & inference
├── generate_report.py                # MJMTECHNOVA branded Excel report generator
├── read_drawing.py                   # Backward-compatible CLI wrapper
├── run_pipeline.py                   # Master end-to-end execution script
└── test_pipeline.py                  # Automated test suite (6 passing tests)
```

---

## 4. Quality Inspection Report Template Details

Each generated Excel report in `output/` is formatted to industrial standards:
1. **Header Banner:**
   * Company Name: **MJMTECHNOVA ENGINEERING PVT. LTD.**
   * Subtitle: **AUTOMATED QUALITY INSPECTION REPORT (FIRST ARTICLE / IN-PROCESS / FINAL INSPECTION)**
   * Works Address, GST No., CIN, and Website
2. **Metadata Card:**
   * Part Number, Part Description, Material Specification, Surface Treatment, Revision No., Net Weight, Inspection Date, Student Project Team, and VIT Faculty Mentor.
3. **Inspection Table Columns:**
   * **Sr. No.**
   * **Characteristic / Parameter** (e.g. *Hole A.1 - X Coordinate*, *Thread M5 - 6H*, *Precision Dimension 16 ± 0.02*)
   * **Category** (`LINEAR_DIMENSION`, `HOLE_CALLOUT`, `THREAD_CALLOUT`, etc.)
   * **Nominal Dimension**
   * **Specified Tolerance** (e.g. `±0.1`, `+0.03/+0.01`, `±0.02`)
   * **LSL (Lower Spec Limit)**
   * **USL (Upper Spec Limit)**
   * **Unit** (`mm`, `Metric (6H)`, `µm`)
   * **Recommended Measuring Tool** (e.g. *Digital Vernier Caliper*, *External Micrometer*, *Thread Plug Gauge 6H*, *CMM / 2D Height Gauge*)
   * **Actual Measurement**
   * **Deviation** (Excel formula: `=IF(ISBLANK(J12), "", ROUND(J12-D12, 4))`)
   * **QC Result** (Excel formula: `=IF(ISBLANK(J12), "PENDING", IF(AND(J12>=F12, J12<=G12), "ACCEPT", "REJECT"))`)
   * **Source Callout / Drawing Text**
   * **Remarks & Status**
4. **Summary & Sign-Off Section:**
   * Total Parameters Inspected
   * Sign-off blocks for VIT Student Engineers, VIT Faculty Mentor, and MJMTECHNOVA Quality Assurance Manager.

---

## 5. Machine Learning AI Classification Performance

* **Model:** Character n-gram TF-IDF Vectorizer + Balanced Logistic Regression
* **Validation:** 5-Fold Stratified Cross-Validation
* **Mean Accuracy:** **99.57% (± 0.53%)**
* **Inference Speed:** < 2 ms per callout string

```
Sample Predictions:
  * 'M5 - 6H ↧ 10'    -> THREAD_CALLOUT        [Confidence: 99.0%]
  * '4X Ø3.4 THRU'     -> HOLE_CALLOUT          [Confidence: 94.7%]
  * '16±0.02'          -> TOLERANCED_DIMENSION  [Confidence: 96.5%]
  * '204.5 mm'         -> LINEAR_DIMENSION      [Confidence: 91.5%]
  * '0.5 x 45°'        -> CHAMFER               [Confidence: 97.9%]
  * 'R 3 TYP'          -> RADIUS                [Confidence: 86.5%]
  * 'A.1 X=132.5mm'    -> COORDINATE_FEATURE    [Confidence: 92.2%]
  * '⌖ 0.05 A'         -> GEOMETRIC_TOLERANCE   [Confidence: 95.2%]
```

---

## 6. How to Run the Project

### Option A: Run the Complete Master Pipeline (Recommended)
Executes all steps end-to-end:
```powershell
python run_pipeline.py
```

### Option B: Run Individual Modules
1. **Feature Extraction:**
   ```powershell
   python read_drawing.py
   ```
2. **Dataset Compilation:**
   ```powershell
   python prepare_dataset.py
   ```
3. **Train AI Classifier:**
   ```powershell
   python ml_classifier.py
   ```
4. **Generate Excel Inspection Reports:**
   ```powershell
   python generate_report.py
   ```

### Option C: Run Automated Tests
```powershell
python test_pipeline.py
```
*(Runs 6 unit/integration tests verifying extraction, dataset integrity, classifier accuracy, and generated Excel reports)*
