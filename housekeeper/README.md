# Super Agent Housekeeper System

Automated cleanup system that keeps the workspace tidy and responds to OA instructions.

## 🚀 Quick Start

```bash
# Start the automated housekeeper
start-housekeeper.bat

# Or manually
python auto-housekeeper.py start
```

## 🤖 How It Works

### Automatic Mode
- **Runs every 6 hours**: Cleans up old files automatically
- **Checks every 5 minutes**: For new OA instructions
- **Smart cleanup**: Different retention policies for different folders

### OA Instruction Mode
The OA can give specific cleaning instructions:

```python
from housekeeper.oa_interface import OAHousekeeperInterface

oa = OAHousekeeperInterface()

# Clean up old files
oa.clean_folder("context-inbox/processed", days=7)

# Archive files  
oa.archive_folder("suggestions/incoming", "suggestions/processed")

# Emergency cleanup
oa.emergency_clean()

# Deep clean everything
oa.deep_clean()

# Check status
oa.status()
```

## 📁 Default Cleanup Rules

| Folder | Retention | Action |
|--------|-----------|---------|
| `context-inbox/processed` | 7 days | Archive to `context-inbox/archive` |
| `suggestions/incoming` | 1 day | Move to `suggestions/processed` |
| `temp/` | 1 day | Delete permanently |
| `logs/` | 30 days | Compress after 7 days |
| `*.tmp, *.temp` | Immediate | Delete on sight |

## 🎛️ Configuration

Edit `config.json` to customize:

```json
{
  "retention_days": 7,
  "auto_cleanup_interval_hours": 6,
  "auto_enabled": true,
  "cleanup_targets": [
    {
      "path": "context-inbox/processed",
      "retention_days": 7,
      "archive_to": "context-inbox/archive"
    }
  ]
}
```

## 📋 OA Commands

### Command Line Interface

```bash
# Check status
python oa-interface.py status

# Clean specific folder
python oa-interface.py clean "context-inbox/processed" 7

# Archive files
python oa-interface.py archive "source-folder" "target-folder"

# Emergency cleanup (frees space immediately)
python oa-interface.py emergency

# Deep clean everything
python oa-interface.py deep
```

### Programmatic Interface

```python
oa = OAHousekeeperInterface()

# Queue cleaning instructions
instruction_id = oa.clean_folder("temp", days=1)

# Check what's been done
recent_tasks = oa.status()
```

## 🧹 Cleanup Types

### Regular Cleanup
- Runs every 6 hours
- Follows retention policies
- Archives important files
- Deletes temporary files

### Deep Clean
- Comprehensive cleanup
- Processes all target folders
- Compresses logs
- Frees maximum space

### Emergency Cleanup
- Immediate action
- Deletes all temp files
- Compresses all logs
- Archives all processed contexts
- For when space is critically low

## 📊 Monitoring

Check these files for activity:
- `cleanup.log` - Detailed cleanup operations
- `instructions.json` - OA instruction queue and results
- `config.json` - Current configuration

## 🔧 Maintenance

The housekeeper maintains itself by:
- Rotating its own log files
- Compressing old logs
- Archiving old instruction history
- Self-monitoring for errors

## 🚨 Troubleshooting

**Housekeeper not running?**
```bash
python auto-housekeeper.py manual
```

**Check recent activity:**
```bash
python oa-interface.py status
```

**Force emergency cleanup:**
```bash
python oa-interface.py emergency
```

**Reset everything:**
1. Stop housekeeper service
2. Delete `config.json` (will recreate with defaults)
3. Restart housekeeper