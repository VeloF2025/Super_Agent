@echo off
echo ==========================================
echo    JARVIS DOCUMENTATION AUTOMATION SETUP
echo ==========================================
echo.

echo Setting up automated documentation system...
echo.

REM Initialize git repository if not already done
if not exist ".git" (
    echo 📁 Initializing git repository...
    git init
    echo.
)

REM Install git hooks for automated doc updates
echo 🔗 Installing git hooks...
python pre-deployment-docs.py install-hooks

REM Generate initial documentation
echo 📚 Generating initial documentation...
python docs-generator.py all

REM Test the pre-deployment system
echo 🧪 Testing pre-deployment system...
python pre-deployment-docs.py docs-only

echo.
echo ✅ Documentation automation setup complete!
echo.
echo 📋 What was configured:
echo    • Git pre-commit hook - Updates docs before commits
echo    • Git pre-push hook - Full deployment readiness check
echo    • Complete documentation suite generated
echo    • Pre-deployment validation system
echo.
echo 🚀 Usage:
echo    python docs-generator.py all          # Generate all docs
echo    python pre-deployment-docs.py         # Full pre-deployment check
echo    python pre-deployment-docs.py quick   # Quick doc update
echo.
echo 📖 Generated Documentation:
echo    • README.md - Professional project overview
echo    • docs/ARCHITECTURE.md - System architecture
echo    • docs/guides/GETTING_STARTED.md - User guide
echo    • docs/api/ - Complete API documentation
echo    • DEPLOYMENT_CHECKLIST.md - Pre-deployment checklist
echo.
echo Now your docs will automatically update before every push!
echo.
pause