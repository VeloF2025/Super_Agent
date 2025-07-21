# Context Engineering Inbox

This folder is the central hub for all project initialization and takeover requests.

## 📁 Folder Structure

```
context-inbox/
├── new-projects/          # Drop new project ideas here
├── existing-projects/     # Drop existing project info for takeover
├── processed/            # Completed contexts (cleaned by housekeeper)
└── templates/            # Quick-start templates
```

## 🚀 How to Use

### For New Projects:
1. Drop any of these into `new-projects/`:
   - Text files with project ideas
   - Requirements documents (PDF, DOCX, MD)
   - Design mockups
   - Technical specifications
   - Or use a template from `templates/`

2. OA will:
   - Scan the folder regularly
   - Process all files
   - Generate comprehensive context
   - Create agent briefings
   - Move processed files to `processed/`

### For Existing Projects:
1. Drop into `existing-projects/`:
   - Project README or documentation
   - Link to repository
   - Brief description of takeover needs
   - Current issues/challenges

2. Agents will:
   - Analyze the project
   - Create preliminary context
   - Generate `[project-name]-context.json`

3. OA will:
   - Review agent findings
   - Complete context engineering
   - Deploy specialized agents
   - Archive in `processed/`

## 🧹 Automatic Cleanup

The Housekeeper agent monitors `processed/` and:
- Archives contexts older than 7 days
- Compresses large files
- Maintains processing history
- Cleans up temporary files

## 📝 File Naming Convention

- New projects: `[date]-[project-name]-idea.*`
- Existing projects: `[date]-[project-name]-takeover.*`
- Processed: `[date]-[project-name]-context-complete.json`

## ⚡ Quick Start

```bash
# New SaaS project
echo "Task management SaaS with AI features" > new-projects/2025-01-21-taskflow-idea.txt

# Existing project takeover
echo "https://github.com/mycompany/legacy-app - needs modernization" > existing-projects/2025-01-21-legacy-app-takeover.txt
```