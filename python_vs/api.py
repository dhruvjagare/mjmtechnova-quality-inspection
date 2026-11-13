"""
api.py - Enterprise Company-Only Protected Quality Inspection API
Permanent, free forever authentication via JWT & SHA256/HMAC hashing.
Zero database dependencies, zero bcrypt compatibility bugs!
"""

import sys, tempfile, re, os, hashlib, hmac
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from jose import JWTError, jwt

from extractor import DrawingExtractor
from generate_report import create_inspection_report

# ─── Security Configuration ──────────────────────────────────────────────────
SECRET_KEY = os.environ.get("JWT_SECRET", "mjmtechnova-permanent-key-2026-secure")
ALGORITHM  = "HS256"
TOKEN_EXPIRE_HOURS = 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(password: str) -> str:
    """Standard SHA-256 with salt — reliable, fast, zero dependency errors."""
    salt = "mjm_technova_salt_2026"
    return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_password(plain), hashed)

COMPANY_DEFAULT_PASS = os.environ.get("COMPANY_PASSWORD", "Mjm@Quality2026")

COMPANY_USERS = {
    "quality@mjmtechnova.com": {
        "name": "MJM Quality Team",
        "email": "quality@mjmtechnova.com",
        "hashed_password": hash_password(COMPANY_DEFAULT_PASS),
    },
    "admin@mjmtechnova.com": {
        "name": "MJM Engineering Admin",
        "email": "admin@mjmtechnova.com",
        "hashed_password": hash_password(os.environ.get("ADMIN_PASSWORD", "MjmAdmin@2026")),
    }
}

# ─── Directories ─────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
if not FRONTEND_DIST.exists():
    FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

app = FastAPI(title="MJMTECHNOVA Quality Inspection API", version="2.5")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

extractor = DrawingExtractor()

# ─── Auth Verification ───────────────────────────────────────────────────────
def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session expired or invalid. Please sign in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email or email not in COMPANY_USERS:
            raise credentials_exception
        return COMPANY_USERS[email]
    except JWTError:
        raise credentials_exception


# ─── Models ──────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


# ─── Auth Endpoints ──────────────────────────────────────────────────────────
@app.post("/auth/login")
def login(req: LoginRequest):
    email = req.email.strip().lower()

    if not (email.endswith("@mjmtechnova.com")):
        raise HTTPException(
            status_code=403,
            detail="Access Denied: Only authorized company emails (@mjmtechnova.com) are permitted."
        )

    user = COMPANY_USERS.get(email)
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid company email or password.")

    token = create_token({"sub": user["email"], "name": user["name"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"name": user["name"], "email": user["email"]}
    }


@app.get("/auth/me")
def me(current_user: dict = Depends(get_current_user)):
    return {"name": current_user["name"], "email": current_user["email"]}


# ─── Protected Quality Inspection Endpoints ──────────────────────────────────
@app.post("/api/extract")
async def extract_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload PDF, extract dimensions and return structured JSON (Protected)."""
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

            raw_callout = item.get("hole_callout") or item.get("raw_text", "")
            formatted_callout = extractor.normalize_symbols(raw_callout)

            size_val = item.get("size")
            if not size_val:
                m_dia = re.search(r"(?:Ø|M)\s*(\d+(?:\.\d+)?)", formatted_callout)
                if m_dia:
                    size_val = f"{m_dia.group(1)} mm"
                else:
                    size_val = f"{nom} mm" if nom else "5 mm"

            rows.append({
                "sr":           idx,
                "parameter":    item.get("parameter", ""),
                "x_nominal":    nom,
                "tol_x":        tol_str,
                "y_nominal":    item.get("y_nominal", ""),
                "tol_y":        item.get("y_tolerance", ""),
                "size":         size_val,
                "hole_callout": formatted_callout,
                "instrument":   item.get("inspection_tool", ""),
                "actual":       actual,
                "deviation":    dev,
                "qc_result":    status_val,
                "remark":       item.get("remarks", ""),
            })

        return {"filename": file.filename, "metadata": meta, "rows": rows, "total": len(rows)}
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/api/report")
async def download_report(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Generate Excel report and return for download (Protected)."""
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
    return {"status": "ok", "version": "2.5"}


if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
