@echo off
title AI Assistant - Quick Test
echo ========================================
echo   AI Assistant - System Test
echo ========================================
echo.
echo Testing backend...
cd /d "%~dp0backend"
python test_client.py

echo.
echo ========================================
echo   Test Complete!
echo ========================================
echo.
pause
