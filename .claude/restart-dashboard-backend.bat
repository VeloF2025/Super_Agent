@echo off
echo Restarting Dashboard Backend...
echo.

REM Kill existing Node processes on port 3001
echo Stopping existing backend...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3001"') do (
    taskkill /F /PID %%a 2>nul
)

REM Wait a moment
timeout /t 2 /nobreak > nul

echo Starting backend server...
cd /d "C:\Jarvis\AI Workspace\Super Agent\agent-dashboard"

REM Start just the backend server
start "Dashboard Backend" cmd /k "node server/index.js"

echo.
echo Backend starting...
echo Frontend should connect in a few seconds.
echo.
echo If issues persist, restart the full dashboard with: npm run dev
echo.
pause