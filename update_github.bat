@echo off
cd /d "D:\Coding projects\aymashtain-led-remote-Source"

if not exist .git (
    echo ERROR: Not a Git repository!
    pause
    exit /b
)

echo =====================================
echo  Updating GitHub - AymashTain
echo =====================================
echo.

echo [1/4] Regenerating AI_CONTEXT.md...
python ai_sync.py

echo.
echo [2/4] Staging changes...
git add .

echo.
echo [3/4] Committing...
git commit -m "Update: %date% %time%"
if errorlevel 1 (
    echo No changes to commit, skipping.
)

echo.
echo [4/4] Pushing to GitHub...
git push

echo.
echo =====================================
echo  DONE
echo =====================================
pause