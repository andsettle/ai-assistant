@echo off
title AI Assistant - Launcher
echo ========================================
echo   AI Assistant - Starting System
echo ========================================
echo.
echo Starting Backend...
start "AI Backend" cmd /k "%~dp0start-backend.bat"

echo.
echo Starting Frontend...
start "AI Frontend" cmd /k "%~dp0start-frontend.bat"

echo.
echo ========================================
echo   System is launching!
echo ========================================
echo.
echo The AI Assistant will open shortly.
echo You can close this window.
echo.
timeout /t 3 /nobreak > nul
exit
