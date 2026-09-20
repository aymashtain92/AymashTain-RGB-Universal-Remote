@echo off
cd /d "%~dp0"
echo Starting AymashTain LED Remote with console logs...
py .\main.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with an error.
    pause
)