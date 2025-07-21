# 🏠 Housekeeper Demo - OA Commands

## Quick Demo of OA Instructions

### 1. Check Current Status
```bash
python oa-interface.py status
```
**Output**: Shows recent instructions and their status

### 2. Start Housekeeper Service  
```bash
python oa-interface.py start
```
**Result**: Queues instruction to start the automated housekeeper service

### 3. Clean Up Old Files
```bash
python oa-interface.py clean "context-inbox/processed" 7
```
**Result**: Removes files older than 7 days from the processed folder

### 4. Archive Files
```bash
python oa-interface.py archive "suggestions/incoming" "suggestions/processed"
```
**Result**: Moves files from incoming to processed folder

### 5. Emergency Cleanup
```bash
python oa-interface.py emergency
```
**Result**: Immediate space-freeing cleanup (deletes temp files, compresses logs)

### 6. Deep Clean Everything
```bash
python oa-interface.py deep
```
**Result**: Comprehensive cleanup following all configured rules

## 📋 Example Session

```bash
# OA wants to start the housekeeper
$ python oa-interface.py start
Instruction queued: start_service (ID: 20250721_074847)
Housekeeper service start requested

# Check what's happening
$ python oa-interface.py status
Recent Housekeeper Instructions:
==================================================
[WAIT] 2025-07-21T07:48 | start_service | pending

# Clean up old context files
$ python oa-interface.py clean "context-inbox/processed" 3
Instruction queued: cleanup_folder (ID: 20250721_075102)

# Check status again
$ python oa-interface.py status
Recent Housekeeper Instructions:
==================================================
[WAIT] 2025-07-21T07:48 | start_service | pending
[WAIT] 2025-07-21T07:51 | cleanup_folder | pending
```

## 🎯 Key Points

1. **OA gives simple commands** - No complex syntax needed
2. **Instructions are queued** - Housekeeper processes them automatically  
3. **Status tracking** - Always know what's been done
4. **Safe operations** - Archives instead of deleting important files
5. **Emergency mode** - For urgent space issues

## 🚀 Integration

The OA can easily integrate these commands into any workflow:

```python
# In OA code:
import subprocess

def start_housekeeper():
    subprocess.run(['python', 'oa-interface.py', 'start'])

def emergency_cleanup():
    subprocess.run(['python', 'oa-interface.py', 'emergency'])

def check_cleanup_status():
    result = subprocess.run(['python', 'oa-interface.py', 'status'], 
                          capture_output=True, text=True)
    return result.stdout
```