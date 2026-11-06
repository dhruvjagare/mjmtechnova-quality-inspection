"""
start.py — Launches FastAPI backend + React frontend together.
Run:  python start.py
"""
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

BASE   = Path(__file__).resolve().parent
PY_DIR = BASE / "python_vs"
FE_DIR = BASE / "frontend"

print("=" * 55)
print("  MJMTECHNOVA Quality Inspection Dashboard  ")
print("=" * 55)
print()

# 1. Start FastAPI backend
print("[1/2] Starting FastAPI backend on http://localhost:8000 ...")
backend = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
    cwd=str(PY_DIR),
)

time.sleep(3)
print("      ✅ Backend started")

# 2. Start React dev server
print("[2/2] Starting React frontend on http://localhost:5173 ...")
frontend = subprocess.Popen(
    ["npm", "run", "dev"],
    cwd=str(FE_DIR),
    shell=True,
)

time.sleep(4)
print("      ✅ Frontend started")
print()
print("─" * 55)
print("  🌐 Open in browser: http://localhost:5173")
print("  📡 API docs:        http://localhost:8000/docs")
print("─" * 55)
print()
print("Press Ctrl+C to stop both servers.")

webbrowser.open("http://localhost:5173")

try:
    backend.wait()
    frontend.wait()
except KeyboardInterrupt:
    print("\nShutting down...")
    backend.terminate()
    frontend.terminate()
