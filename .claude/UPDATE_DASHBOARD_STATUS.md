# Getting Orchestrator ONLINE in Dashboard

## Quick Fix

To get the Orchestrator showing as ONLINE:

1. **Start the heartbeat monitor**:
   ```bash
   cd "C:\Jarvis\AI Workspace\Super Agent"
   .claude\start-orchestrator.bat
   ```

2. **Keep it running** - The script will:
   - Register the orchestrator with the system
   - Send heartbeats every 30 seconds
   - Show as ONLINE in the dashboard

## What Was Wrong

The Orchestrator was showing OFFLINE because:
- No heartbeat files were being created
- The dashboard checks `shared/heartbeats/` for `.heartbeat` files
- If a heartbeat file is older than 60 seconds, agent shows as OFFLINE

## What I Created

### 1. **agent-heartbeat.py**
- Sends heartbeats to keep agents ONLINE
- Auto-detects which agent is running
- Integrates with Claude context system
- Can manage multiple agents

### 2. **start-orchestrator.bat**
- Easy one-click solution
- Registers orchestrator
- Starts heartbeat monitor
- Keeps running until you stop it

## Additional Commands

```bash
# Check heartbeat status
python .claude\agent-heartbeat.py status

# Start all agents
python .claude\agent-heartbeat.py start-all

# Start specific agent
python .claude\agent-heartbeat.py start --agent development

# Register without starting
python .claude\agent-heartbeat.py register --agent orchestrator
```

## Integration with Context System

The heartbeat system is now integrated with the Claude context management:
- Uses same config files
- Respects instance IDs
- Works with multiple IDEs
- Shows context activity status

## For Production Use

To keep agents always ONLINE:

1. **Windows Task Scheduler**:
   - Create task to run `start-orchestrator.bat` at startup
   - Set to run whether user logged in or not

2. **As a Service**:
   - Use NSSM to install as Windows service
   - Auto-restart on failure

3. **With Agent Dashboard**:
   - The dashboard can auto-start heartbeats
   - Configure in dashboard settings

## Troubleshooting

If still showing OFFLINE:
1. Check `shared/heartbeats/` folder exists
2. Verify `.heartbeat` files are being created
3. Ensure dashboard is checking correct path
4. Check Windows Firewall isn't blocking

The Orchestrator should now show as ONLINE in your dashboard!