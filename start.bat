@echo off
echo ============================================================
echo   TrustAI - Starting Application
echo ============================================================
echo.
echo   PRIVACY: All processing is local. No data leaves your machine.
echo.

REM --- Activate virtual environment ---
call "%~dp0venv\Scripts\activate.bat"

REM --- Build the React frontend ---
echo [1/2] Building frontend...
cd /d "%~dp0frontend"
call npm run build
if errorlevel 1 (
    echo.
    echo ERROR: Frontend build failed. Make sure Node.js is installed
    echo        and you have run 'npm install' in the frontend folder.
    pause
    exit /b 1
)
echo       Frontend built successfully.
echo.

REM --- Start the backend (serves both API + frontend) ---
echo [2/2] Starting server...
echo.
echo   >>> Open in your browser: http://localhost:8501
echo.
cd /d "%~dp0backend"
python main.py
pause
