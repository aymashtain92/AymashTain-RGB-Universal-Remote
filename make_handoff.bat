@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================================
echo   AymashTain Hand-off Bundle Builder
echo ============================================================
echo.

set "PYEXE="
where python >nul 2>nul && set "PYEXE=python"
if not defined PYEXE (
    where py >nul 2>nul && set "PYEXE=py"
)
if not defined PYEXE (
    echo ERROR: Python not found in PATH.
    echo Install Python 3.14 and try again.
    echo.
    pause
    exit /b 1
)

echo Using: !PYEXE!
echo.

!PYEXE! make_handoff.py %*
set "RC=!errorlevel!"

if not "!RC!"=="0" (
    echo.
    echo Something went wrong. Exit code: !RC!
    echo.
    pause
    exit /b !RC!
)

echo.
echo Done. Opening handoff folder...
if exist "handoff" start "" "handoff"
echo.
pause
endlocal