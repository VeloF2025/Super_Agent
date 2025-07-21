@echo off
REM Start Orchestrator Agent with Heartbeat
REM This keeps the agent showing as ONLINE in the dashboard

echo ========================================
echo Starting Orchestrator Agent
echo ========================================
echo.

cd /d "C:\Jarvis\AI Workspace\Super Agent"

REM Register the orchestrator
echo Registering orchestrator...
python .claude\agent-heartbeat.py register --agent orchestrator

REM Start heartbeat (30 second interval)
echo.
echo Starting heartbeat monitor...
echo The orchestrator will now show as ONLINE in the dashboard
echo.
echo Press Ctrl+C to stop
echo.

python .claude\agent-heartbeat.py start --agent orchestrator --interval 30