@echo off
setlocal
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0debug_run.ps1"
set RC=%errorlevel%

echo.
echo ============================================================
echo   Debug run finished. Exit code: %RC%
echo.
echo   Report saved in the project root:
echo     debug_powershell_run_*.txt
echo.
echo   Idea file for next session:
echo     NEXT_SESSION_DEBUG_BUTTON_IDEA.txt
echo ============================================================
echo.
pause
exit /b %RC%