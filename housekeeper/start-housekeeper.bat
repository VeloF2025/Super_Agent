@echo off
echo ========================================
echo      Super Agent Housekeeper Startup
echo ========================================
echo.

echo Installing required Python packages...
pip install schedule

echo.
echo Starting Automated Housekeeper...
start "Housekeeper Service" cmd /k python auto-housekeeper.py start

echo.
echo ✅ Housekeeper is now running automatically!
echo.
echo The housekeeper will:
echo   🧹 Clean up old files every 6 hours
echo   📋 Check for OA instructions every 5 minutes  
echo   📁 Archive processed contexts after 7 days
echo   🗜️  Compress old log files
echo.
echo To give instructions to the housekeeper:
echo   python oa-interface.py status
echo   python oa-interface.py clean "folder-name" 7
echo   python oa-interface.py emergency
echo.
echo Press any key to continue...
pause >nul