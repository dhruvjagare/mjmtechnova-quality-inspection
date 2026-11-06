"""
run_pipeline.py - Root Workspace Runner
Redirects to the project implementation inside python_vs/
"""

import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR / "python_vs"

if __name__ == "__main__":
    script = PROJECT_DIR / "run_pipeline.py"
    res = subprocess.run([sys.executable, str(script)], cwd=str(PROJECT_DIR))
    sys.exit(res.returncode)
