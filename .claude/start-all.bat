@echo off
REM Start everything needed for the Super Agent System

echo ========================================
echo Starting Super Agent System
echo ========================================
echo.

cd /d "C:\Jarvis\AI Workspace\Super Agent"

REM Start the dashboard first
echo Starting Agent Dashboard...
start "Starting Dashboard" cmd /c "cd agent-dashboard && start-dashboard.bat"

REM Wait for dashboard to initialize
timeout /t 5 /nobreak > nul

REM Start orchestrator heartbeat
echo.
echo Starting Orchestrator Heartbeat...
start "Orchestrator Heartbeat" cmd /k ".claude\start-orchestrator.bat"

echo.
echo ========================================
echo System Starting Up!
echo ========================================
echo.
echo Dashboard will be available at:
echo   http://localhost:5173 (Frontend)
echo   http://localhost:3001 (Backend API)
echo.
echo The Orchestrator should show as ONLINE shortly.
echo.
echo To stop everything, close all the command windows.
echo.
pause