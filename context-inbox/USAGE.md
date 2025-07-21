# Context Engineering System - Usage Guide

## 🚀 Quick Start

### Starting a New Project

1. **Option A - Use Template**:
   ```bash
   cp templates/quick-project-template.md new-projects/2025-01-21-myproject-idea.md
   # Edit the file with your project details
   ```

2. **Option B - Simple Text**:
   ```bash
   echo "Build a task management app with React and Node.js" > new-projects/2025-01-21-taskapp-idea.txt
   ```

3. **Option C - Drop Files**:
   - Drag any requirements documents into `new-projects/`
   - Supports: .txt, .md, .pdf, .docx, .json, .yaml

### Taking Over an Existing Project

1. **Use the takeover template**:
   ```bash
   cp templates/takeover-template.md existing-projects/2025-01-21-legacy-app-takeover.md
   # Fill in the details
   ```

2. **Or simply provide repo link**:
   ```bash
   echo "https://github.com/company/project - needs modernization" > existing-projects/2025-01-21-project-takeover.txt
   ```

## 🤖 Running the System

### Start the OA Monitor
```bash
python oa-monitor.py
```
This will:
- Watch for new files every 30 seconds
- Process them automatically
- Move processed files to `processed/`

### Run the Context Processor
```bash
python context-processor.py
```
This will:
- Process pending contexts
- Generate agent allocations
- Create CLAUDE.md files for each agent

### Start the Housekeeper
```bash
python oa-monitor.py cleanup
```
This will:
- Clean up files older than 7 days
- Archive important contexts
- Keep the system tidy

## 📁 Where Files End Up

```
context-inbox/
├── new-projects/        ← Drop new ideas here
├── existing-projects/   ← Drop takeover requests here
├── processed/          ← Monitor moves files here
│   ├── original-*      ← Your original files
│   └── *-context.json  ← Generated contexts
├── agent-contexts/     ← Final processed contexts
│   ├── *-complete.json ← Full context data
│   └── *-CLAUDE.md     ← Agent-specific guides
└── archive/            ← Old contexts (after 7 days)
    └── YYYY-MM/        ← Organized by month
```

## 🔄 Workflow Example

1. **You**: Drop `project-idea.txt` into `new-projects/`
2. **OA Monitor**: Detects file, creates initial context
3. **OA**: Reviews and processes the context
4. **Context Processor**: Generates full context and agent briefs
5. **Agents**: Receive their CLAUDE.md files and start work
6. **Housekeeper**: Cleans up after 7 days

## 💡 Tips

- **Batch Processing**: Drop multiple files at once
- **Templates**: Faster than writing from scratch
- **Naming**: Use dates in filenames for easy sorting
- **Updates**: Add new info by creating new files

## 🛠️ Customization

Edit these values in the scripts:
- `check_interval`: How often to check for files (default: 30s)
- `retention_days`: How long to keep processed files (default: 7 days)
- `archive_interval`: How often to run cleanup (default: 24 hours)

## 📊 Monitoring

Check `processing.log` for:
- Processing history
- Any errors
- Performance metrics

## 🤝 Integration

The generated contexts can be:
- Used by the Super Agent system
- Imported into project management tools
- Shared with human developers
- Version controlled in Git