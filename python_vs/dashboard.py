"""
dashboard.py - Pure Python Launcher for Quality Inspection Dashboard
Project: Automation of Quality Inspection Report Generation to Reduce Manual Efforts
Client: MJMTECHNOVA ENGINEERING PVT. LTD.
Academic Mentorship: Prof. Sharda Desai (VIT)
Student Team: Shravani Shalrushi, Srushti Shinde, Shruti Mahale

Usage:
    python dashboard.py
"""

import sys
from pathlib import Path
from streamlit.web import cli as stcli

BASE_DIR = Path(__file__).resolve().parent
APP_SCRIPT = BASE_DIR / "app.py"


def main():
    print("=" * 70)
    print("MJMTECHNOVA ENGINEERING PVT. LTD. - QUALITY DASHBOARD")
    print("Launching Web Dashboard directly via Python...")
    print("Dashboard will open in your web browser at http://localhost:8501")
    print("=" * 70)

    sys.argv = [
        "streamlit",
        "run",
        str(APP_SCRIPT),
        "--server.port=8501",
        "--server.headless=false",
        "--browser.serverAddress=localhost",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
