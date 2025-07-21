@echo off
echo Starting OA Agent Dashboard...

REM Kill any existing Node processes
echo Killing existing Node processes...
taskkill //IM node.exe //F 2>nul
timeout /t 2 /nobreak > nul

cd /d "C:\Jarvis\AI Workspace\Super Agent\agent-dashboard"

REM Start backend server
echo Starting backend server on port 3001...
start "Backend Server" cmd /k "cd server && npm start"

REM Wait for backend to start
timeout /t 5 /nobreak > nul

REM Start frontend server
echo Starting frontend server on port 5173...
start "Frontend Server" cmd /k "cd client && npm run dev"

echo.
echo Dashboard starting...
echo Backend: http://localhost:3001
echo Frontend: http://localhost:5173
echo.
echo Press any key to stop servers...
pause > nul

REM Kill servers when done
taskkill //IM node.exe //F