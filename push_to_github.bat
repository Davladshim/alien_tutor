@echo off
REM Navigate to your project folder
cd /d "C:\Users\Kakasha\alien tutor"

REM Add all changes
git add --all
git reset HEAD .env

REM Create commit message with current date and time
for /f "tokens=1-5 delims=.:/ " %%d in ("%date% %time%") do (
    set commitMsg=Auto commit %%d-%%e-%%f %%g:%%h
)

REM Commit changes
git commit -m "%commitMsg%"

REM Force push to overwrite GitHub with local version
git push origin main --force

pause
