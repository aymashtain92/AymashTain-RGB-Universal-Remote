@echo off
setlocal

cd /d "%~dp0"

REM Prefer pythonw for a silent GUI launch
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "%~dp0main.py"
    exit /b 0
)

where py >nul 2>nul
if %errorlevel%==0 (
    start "" pyw "%~dp0main.py" 2>nul
    if %errorlevel%==0 exit /b 0
    start "" py "%~dp0main.py"
    exit /b 0
)

where python >nul 2>nul
if %errorlevel%==0 (
    start "" python "%~dp0main.py"
    exit /b 0
)

echo Python is not installed or not on PATH.
echo Run install_and_repair.ps1 to set everything up.
pause