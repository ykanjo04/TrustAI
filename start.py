"""
TrustAI - Single-command launcher.

Builds the React frontend and starts the FastAPI server using the project venv.
Open http://localhost:8501 after launch.

PRIVACY: All processing is local. No data leaves your machine.
"""

import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend"
BACKEND_DIR = ROOT / "backend"
VENV_PYTHON = ROOT / "venv" / "Scripts" / "python.exe"


def main():
    print("=" * 60)
    print("  TrustAI - Building & Starting")
    print("=" * 60)
    print()

    # Determine which Python to use (prefer venv)
    python_exe = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    if VENV_PYTHON.exists():
        print("  Using virtual environment: venv/")
    else:
        print("  WARNING: venv not found, using system Python.")
        print("  Run 'python -m venv venv' then install deps to create one.")
    print()

    # Step 1: Build frontend
    print("  [1/2] Building frontend...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=str(FRONTEND_DIR),
        shell=True,
    )
    if result.returncode != 0:
        print("\n  ERROR: Frontend build failed.")
        print("  Make sure Node.js is installed and run 'npm install' first.")
        sys.exit(1)
    print("        Frontend built successfully.\n")

    # Step 2: Start backend (serves API + frontend on port 8501)
    print("  [2/2] Starting server...\n")
    print("  >>> Open in your browser: http://localhost:8501\n")

    os.chdir(str(BACKEND_DIR))
    subprocess.run([python_exe, "main.py"], cwd=str(BACKEND_DIR))


if __name__ == "__main__":
    main()
