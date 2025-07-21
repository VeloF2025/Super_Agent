@echo off
echo Force restarting dashboard servers...

REM Kill all node processes
echo Killing all Node.js processes...
taskkill /IM node.exe /F 2>nul

timeout /t 3 /nobreak > nul

cd /d "C:\Jarvis\AI Workspace\Super Agent\agent-dashboard"

REM Delete old database to apply new schema
echo Removing old database...
del /f /q data\dashboard.db 2>nul

echo Starting fresh servers...
start "Dashboard" npm run dev

echo.
echo Dashboard is restarting. Please wait a moment and refresh your browser.
echo.
pause