@echo off
REM Start heartbeats for ALL Super Agent agents

echo ========================================
echo Activating ALL Super Agent Agents
echo ========================================
echo.

cd /d "C:\Jarvis\AI Workspace\Super Agent"

echo Starting heartbeats for all agents...
echo All agents will show as ONLINE in the dashboard
echo.
echo Press Ctrl+C to stop
echo.

python ".claude\activate-all-agents.py"