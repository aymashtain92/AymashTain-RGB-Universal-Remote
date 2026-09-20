@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" call run.bat --version
".venv\Scripts\python.exe" -m pip install pyinstaller
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean ^
    --name "AymashTain LED Remote" ^
    --windowed ^
    --collect-all bleak ^
    --collect-submodules sounddevice ^
    main.py

echo.
echo Built: dist\AymashTain LED Remote\AymashTain LED Remote.exe
pause
