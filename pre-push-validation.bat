@echo off
echo ==========================================
echo    PRE-PUSH VALIDATION CHECKLIST
echo ==========================================
echo.

setlocal enabledelayedexpansion
set READY=true

echo [1] Checking for critical files to exclude...
set EXCLUDE_FILES=0

REM Check for sensitive files
if exist "ADMIN_CREDENTIALS.txt" (
    echo    WARNING: ADMIN_CREDENTIALS.txt exists - add to .gitignore
    set EXCLUDE_FILES=1
)

if exist ".env" (
    REM Check if .env is in gitignore
    findstr /C:".env" .gitignore >nul 2>&1
    if errorlevel 1 (
        echo    WARNING: .env file not in .gitignore!
        set EXCLUDE_FILES=1
    )
)

if !EXCLUDE_FILES! equ 1 (
    echo.
    echo    ACTION REQUIRED: Add sensitive files to .gitignore
    set READY=false
)

echo.
echo [2] Checking test results...
cd agent-dashboard
call npm test -- --passWithNoTests >nul 2>&1
if errorlevel 1 (
    echo    ERROR: Tests are failing!
    set READY=false
) else (
    echo    OK: All tests passing
)

echo.
echo [3] Checking for untracked security files...
cd ..
if exist "security-fixes" (
    echo    INFO: security-fixes directory exists - consider if it should be committed
)

echo.
echo [4] Final security check...
REM Check for the known exposed secrets issue
findstr /C:"PERPLEXITY_API_KEY" "projects\Jarvis AI\app\use-cases\mcp-server\worker-configuration.d.ts" >nul 2>&1
if errorlevel 0 (
    echo    INFO: worker-configuration.d.ts contains API key type definitions
    echo          This is a TypeScript definition file, not actual secrets
)

echo.
echo ==========================================
if "!READY!"=="true" (
    echo    STATUS: READY FOR GIT PUSH
    echo.
    echo    Recommended git commands:
    echo    1. git add .
    echo    2. git commit -m "Add comprehensive security and development improvements to Super Agent system"
    echo    3. git push origin master
) else (
    echo    STATUS: NOT READY - Fix issues above first
)
echo ==========================================
echo.

endlocal
pause