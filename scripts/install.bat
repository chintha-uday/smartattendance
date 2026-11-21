@echo off
setlocal
cd /d "%~dp0\.."
echo ==========================================
echo SMART ATTENDANCE - WINDOWS INSTALLER
echo ==========================================
where py >nul 2>nul
if errorlevel 1 (
  echo Python 3.12+ is required. Install Python and enable Add to PATH.
  pause
  exit /b 1
)
if not exist ".venv" py -3 -m venv .venv
if errorlevel 1 goto :error
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 goto :error
pip install -r requirements.txt
if errorlevel 1 goto :error
if not exist ".env" copy ".env.example" ".env"
echo.
echo Installation packages are ready.
echo 1. Edit .env and configure DB_URL for SQL Server.
echo 2. Ensure SQL Server and ODBC Driver 18 are installed.
echo 3. Run: python -m app.setup_admin
echo 4. Run scripts\run.bat
echo.
pause
exit /b 0
:error
echo Installation failed. Review the error above.
pause
exit /b 1
