@echo off
echo =========================================
echo      JARVIS DAILY OPERATIONS CENTER
echo =========================================
echo.

echo Starting Jarvis daily operation systems...
echo.

REM Start the agent dashboard for monitoring
echo 🖥️ Starting Agent Dashboard...
start "Agent Dashboard" cmd /k "cd /d C:\Jarvis\AI Workspace\Super Agent\agent-dashboard && npm run dev"

REM Wait a moment for dashboard to initialize
timeout /t 3 /nobreak >nul

REM Start housekeeper service
echo 🧹 Starting Housekeeper Service...
start "Housekeeper" cmd /k "cd /d C:\Jarvis\AI Workspace\Super Agent\housekeeper && python start-service.py"

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start context monitoring
echo 📥 Starting Context Monitoring...
start "Context Monitor" cmd /k "cd /d C:\Jarvis\AI Workspace\Super Agent\context-inbox && python oa-monitor.py"

REM Start the scheduler
echo ⏰ Starting Jarvis Scheduler...
start "Jarvis Scheduler" cmd /k "cd /d C:\Jarvis\AI Workspace\Super Agent\daily-ops && python jarvis-scheduler.py auto"

echo.
echo ✅ All Jarvis systems are starting up!
echo.
echo 🖥️ Agent Dashboard: http://localhost:3000
echo 📋 Systems running in background windows
echo.
echo Available commands:
echo   python jarvis-scheduler.py morning   # Manual morning standup
echo   python jarvis-scheduler.py evening   # Manual evening shutdown
echo   python jarvis-scheduler.py midday    # Manual midday check
echo.
echo Press any key to open the Agent Dashboard...
pause >nul
start http://localhost:3000