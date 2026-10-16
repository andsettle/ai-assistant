@echo off
if "%1"=="hidden" goto hidden
start "" /min cmd /c "%~f0" hidden
exit

:hidden
title AI Assistant - Frontend
timeout /t 3 /nobreak > nul
set "ROOT=%~dp0"
set "PID_DIR=%ROOT%data\pids"
if not exist "%PID_DIR%" mkdir "%PID_DIR%"
cd /d "%ROOT%frontend"

rem Use cmd to resolve npm.cmd even if .ps1 association is broken
powershell -NoProfile -Command "$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c','npm','run','tauri','dev' -WorkingDirectory '%ROOT%frontend' -PassThru -WindowStyle Minimized; Set-Content -Path '%PID_DIR%\frontend.pid' -Value $p.Id"
