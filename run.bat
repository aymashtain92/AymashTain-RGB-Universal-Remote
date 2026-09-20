@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -3 -m venv .venv || python -m venv .venv || goto :nopython
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :nodeps
)

".venv\Scripts\python.exe" main.py %*
if errorlevel 1 pause
exit /b 0

:nopython
echo Python 3.10+ was not found. Install it from https://python.org and tick "Add to PATH".
pause
exit /b 1

:nodeps
echo Dependency installation failed. See the messages above.
pause
exit /b 1
