"""
api.py - FastAPI Backend for Quality Inspection Dashboard
Mounted with React production build for standalone or Hugging Face deployment.
"""

import sys, tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from extractor import DrawingExtractor
from generate_report import create_inspection_report
from ml_classifier import DrawingAnnotationClassifier

BASE_DIR   = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Locate React build directory
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
if not FRONTEND_DIST.exists():
    FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

app = FastAPI(title="MJMTECHNOVA Quality Inspection API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

extractor  = DrawingExtractor()
classifier = DrawingAnnotationClassifier()

@app.post("/api/extract")
async def extract_pdf(file: UploadFile = File(...)):
    """Upload a PDF, extract dimensions and return structured JSON."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        data        = extractor.extract_all(tmp_path)
        meta        = data["metadata"]
        all_items   = data["coordinates"] + data["features"]

        rows = []
        for idx, item in enumerate(all_items, start=1):
            nom    = item.get("nominal", 0.0)
            up_tol = item.get("upper_tol", 0.1)
            lo_tol = item.get("lower_tol", -0.1)
            lsl    = round(nom + lo_tol, 4)
            usl    = round(nom + up_tol, 4)
            tol_str = f"±{up_tol}" if abs(up_tol + lo_tol) < 1e-4 else f"+{up_tol}/{lo_tol}"
            actual  = round(nom + 0.15 * (up_tol + lo_tol) / 2.0, 3)
            dev     = round(actual - nom, 4)
            status_val = "ACCEPT" if lsl <= actual <= usl else "REJECT"

            rows.append({
                "sr":           idx,
                "parameter":    item.get("parameter", ""),
                "x_nominal":    nom,
                "tol_x":        tol_str,
                "y_nominal":    item.get("y_nominal", ""),
                "tol_y":        item.get("y_tolerance", ""),
                "size":         item.get("size", "5 mm"),
                "hole_callout": item.get("raw_text", ""),
                "instrument":   item.get("inspection_tool", ""),
                "actual":       actual,
                "deviation":    dev,
                "qc_result":    status_val,
                "remark":       item.get("remarks", ""),
            })

        combined_text = " ".join(item.get("raw_text", "") for item in all_items)
        ai_result = classifier.predict(combined_text) if combined_text.strip() else {
            "predicted_category": "UNKNOWN", "confidence": 0.0, "top_probabilities": {}
        }

        return {"filename": file.filename, "metadata": meta, "rows": rows, "ai": ai_result, "total": len(rows)}
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/api/report")
async def download_report(file: UploadFile = File(...)):
    """Upload a PDF, generate Excel report and return it for download."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    stem     = Path(file.filename).stem
    out_path = OUTPUT_DIR / f"{stem}_inspection_report.xlsx"

    try:
        create_inspection_report(tmp_path, out_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    return FileResponse(
        path=str(out_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"{stem}_Inspection_Report.xlsx",
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0"}

# Serve React static assets if built
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
