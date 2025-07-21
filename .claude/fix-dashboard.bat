@echo off
echo Fixing Dashboard Issues...
echo.

REM Kill any existing Node processes on port 3001
echo Stopping processes on port 3001...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":3001"') do (
    echo Killing process %%a
    taskkill /F /PID %%a 2>nul
)

REM Also try to kill processes on 5173
echo Stopping processes on port 5173...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173"') do (
    echo Killing process %%a
    taskkill /F /PID %%a 2>nul
)

echo.
echo Ports cleared! You can now restart the dashboard.
echo.
echo Run: npm run dev
echo.
pause