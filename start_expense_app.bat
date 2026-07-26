@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_expense_app.ps1"
exit /b %ERRORLEVEL%
