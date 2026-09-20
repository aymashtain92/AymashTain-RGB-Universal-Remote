@echo off
:: Batch file to update GitHub repo with latest changes
:: Double-click to run!

:: Change to your project directory
cd /d "D:\Coding projects\aymashtain-led-remote-Source"

:: Check if we're in a Git repo
if not exist .git (
    echo ERROR: Not a Git repository! Make sure you're in the correct folder.
    pause
    exit /b
)

:: Add all changes
echo Adding all changes...
git add .

:: Commit with a timestamp
echo Committing changes...
git commit -m "Auto-update: %date% %time%"

:: Push to GitHub
echo Pushing to GitHub...
git push

:: Done!
echo.
echo ✅ Successfully updated GitHub!
pause