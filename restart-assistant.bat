@echo off
title AI Assistant - Emergency Restart
echo ========================================
echo   AI Assistant - Emergency Restart
echo ========================================
echo.
echo Stopping assistant processes...

set "ROOT=%~dp0"
set "PID_DIR=%ROOT%data\pids"

call :killpid "%PID_DIR%\backend.pid"
call :killpid "%PID_DIR%\frontend.pid"

rem Fallback: close only assistant windows by title
taskkill /F /FI "WINDOWTITLE eq AI Assistant - Backend" /T 2>nul
taskkill /F /FI "WINDOWTITLE eq AI Assistant - Frontend" /T 2>nul

echo.
echo Waiting 2 seconds...
timeout /t 2 /nobreak > nul

echo.
echo Restarting system...
start "AI Assistant Launcher" "%~dp0start-assistant.bat"

echo.
echo System restarted!
timeout /t 2 /nobreak > nul
exit

:killpid
if exist "%~1" (
  for /f %%p in (%~1) do (
    if not "%%p"=="" taskkill /PID %%p /T /F 2>nul
  )
  del "%~1" 2>nul
)
exit /b 0
