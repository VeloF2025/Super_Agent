@echo off
REM Claude Context Management Setup Script
REM Initializes the environment for Super Agent System

echo ========================================
echo Claude Context Management Setup
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Create necessary directories
echo Creating directory structure...
if not exist ".claude\contexts\private" mkdir ".claude\contexts\private"
if not exist ".claude\contexts\templates" mkdir ".claude\contexts\templates"
if not exist ".claude\cache" mkdir ".claude\cache"
if not exist ".claude\logs" mkdir ".claude\logs"

REM Copy config template if needed
if not exist ".claude\config.local.json" (
    if exist ".claude\config.local.example.json" (
        echo Creating local config from template...
        copy ".claude\config.local.example.json" ".claude\config.local.json"
        echo Please edit .claude\config.local.json with your settings
    )
)

REM Install required Python packages
echo.
echo Installing required Python packages...
pip install psutil --quiet

REM Run initial validation
echo.
echo Running context validation...
python .claude\context-router.py validate

REM Check for existing CLAUDE.md files
echo.
echo Checking existing CLAUDE.md files...
python .claude\enhance-context.py check

REM Display status
echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .claude\config.local.json with your settings
echo 2. Run 'python .claude\enhance-context.py batch --apply' to enhance existing files
echo 3. Run 'python .claude\context-monitor.py status' to check system status
echo.
echo For help, see .claude\IMPLEMENTATION_GUIDE.md
echo.
pause