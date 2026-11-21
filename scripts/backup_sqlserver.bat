@echo off
setlocal
set BACKUP_DIR=C:\SmartAttendance\backups
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set STAMP=%%i
sqlcmd -S localhost -E -Q "BACKUP DATABASE SmartAttendanceDB TO DISK=N'%BACKUP_DIR%\SmartAttendanceDB_%STAMP%.bak' WITH CHECKSUM, INIT"
if errorlevel 1 (
 echo Backup failed. Check SQL Server permissions and sqlcmd installation.
 exit /b 1
)
echo Backup completed: %BACKUP_DIR%\SmartAttendanceDB_%STAMP%.bak
