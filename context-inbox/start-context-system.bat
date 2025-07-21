@echo off
echo ========================================
echo    Context Engineering System Startup
echo ========================================
echo.

echo Starting OA Monitor...
start "OA Monitor" cmd /k python oa-monitor.py

echo Starting Housekeeper...
start "Context Housekeeper" cmd /k python oa-monitor.py cleanup

echo.
echo ✅ Context Engineering System is running!
echo.
echo 📁 Drop files into:
echo    - new-projects\     (for new project ideas)
echo    - existing-projects\ (for project takeovers)
echo.
echo To process contexts manually, run:
echo    python context-processor.py
echo.
echo Press any key to open the context inbox folder...
pause >nul
explorer "C:\Jarvis\AI Workspace\Super Agent\context-inbox"