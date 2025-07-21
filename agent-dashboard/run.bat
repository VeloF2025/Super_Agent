@echo off
cd /d "C:\Jarvis\AI Workspace\Super Agent\agent-dashboard"

echo Killing any existing Node processes on ports 3000 and 3001...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3001 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul

timeout /t 2 /nobreak > nul

echo Starting OA Agent Dashboard...
npm run dev