@echo off
if "%1"=="hidden" goto hidden
start "" /min cmd /c "%~f0" hidden
exit

:hidden
title AI Assistant - Backend
set "ROOT=%~dp0"
set "PID_DIR=%ROOT%data\pids"
if not exist "%PID_DIR%" mkdir "%PID_DIR%"
cd /d "%ROOT%backend"

powershell -NoProfile -Command "$p = Start-Process -FilePath 'python' -ArgumentList 'main.py' -WorkingDirectory '%ROOT%backend' -PassThru -WindowStyle Minimized; Set-Content -Path '%PID_DIR%\backend.pid' -Value $p.Id"
