@echo off
REM Navigate to project folder
cd /d "C:\Users\Kakasha\alien tutor"

REM Add all changes
git add .

REM Create commit message with current date and time
for /f "tokens=1-5 delims=.:/ " %%d in ("%date% %time%") do (
    set commitMsg=Auto commit %%d-%%e-%%f %%g:%%h
)

REM Commit changes
git commit -m "%commitMsg%"

REM Push to GitHub
git push origin main

REM Pause to show any messages
pause
