@echo off
echo ====================================
echo OA Agent Dashboard - Quick Start
echo ====================================
echo.

cd /d "C:\Jarvis\AI Workspace\Super Agent\agent-dashboard"

REM Check if backend dependencies are installed
if not exist "node_modules" (
    echo Installing backend dependencies...
    npm install
    if errorlevel 1 (
        echo ERROR: Failed to install backend dependencies
        pause
        exit /b 1
    )
)

REM Check if frontend dependencies are installed
if not exist "client\node_modules" (
    echo Installing frontend dependencies...
    cd client
    npm install
    if errorlevel 1 (
        echo ERROR: Failed to install frontend dependencies
        cd ..
        pause
        exit /b 1
    )
    cd ..
)

REM Create data directory
if not exist "data" mkdir data

echo.
echo Starting servers...
echo Backend: http://localhost:3001
echo Frontend: http://localhost:3000
echo.

REM Start backend in new window
start "Dashboard Backend" cmd /k "node server/index.js"

REM Wait a moment for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend in new window
start "Dashboard Frontend" cmd /k "cd client && npm run dev"

echo.
echo Dashboard is starting up...
echo Close this window to keep servers running.
echo.
pause