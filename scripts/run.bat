@echo off
cd /d "%~dp0\.."
if not exist ".venv\Scripts\activate.bat" (
  echo Run scripts\install.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
