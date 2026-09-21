@echo off
REM One-click hand-off builder for AymashTain LED RGB Remote.
REM Double-click this file. A numbered zip appears in .\handoff\.

setlocal
cd /d "%~dp0"

REM Prefer `python` on PATH. Fall back to the Windows launcher if needed.
set "PYEXE="
where python >nul 2>nul && set "PYEXE=python"
if not defined PYEXE (
    where py >nul 2>nul && set "PYEXE=py"
)

if not defined PYEXE (
    echo.
    echo Python was not found on PATH.
    echo Install Python 3.14 from python.org and tick "Add python.exe to PATH".
    echo.
    pause
    exit /b 1
)

"%PYEXE%" make_handoff.py
if errorlevel 1 (
    echo.
    echo Something went wrong. Scroll up for the message.
    echo.
    pause
    exit /b 1
)

echo Opening the handoff folder...
start "" "%~dp0handoff"

pause