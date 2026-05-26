@echo off
setlocal
cd /d "%~dp0"

if not exist "venv\Scripts\activate" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

echo Starting AI Running Coach...
echo Auto-restart enabled. Press Ctrl+C to stop.

:restart
python main.py --mode=development
if %ERRORLEVEL% neq 0 (
    echo Coach exited with code %ERRORLEVEL%. Restarting in 5 seconds...
    timeout /t 5 /nobreak >nul
    goto restart
)
