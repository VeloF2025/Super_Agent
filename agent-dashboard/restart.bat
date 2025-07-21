@echo off
echo Stopping any running servers...

REM Kill processes on ports
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :3000') do (
    echo Killing process %%p
    taskkill //PID %%p //F 2>nul
)

for /f "tokens=5" %%p in ('netstat -ano ^| findstr :3001') do (
    echo Killing process %%p
    taskkill //PID %%p //F 2>nul
)

timeout /t 3 /nobreak > nul

cd /d "C:\Jarvis\AI Workspace\Super Agent\agent-dashboard"

echo Starting fresh servers...
npm run dev