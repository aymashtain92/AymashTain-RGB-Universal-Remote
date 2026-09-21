@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel%==0 (
    python "%~dp0main.py" %*
) else (
    py "%~dp0main.py" %*
)

endlocal