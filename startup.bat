@echo off

echo ========================================
echo   Sanskar Intelligence Service Startup
echo ========================================
echo.

if not exist "venv" (
    echo [1/3] Creating virtual environment...
    python -m venv venv
) else (
    echo [1/3] Virtual environment exists, skipping creation
)

echo [2/3] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/3] Installing dependencies...
pip install -q -r requirements.txt

echo.
echo ========================================
echo   Starting API server on port 8000
echo   Health check: http://localhost:8000/health
echo ========================================
echo.
python api.py

pause
