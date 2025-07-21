@echo off
echo ==========================================
echo    SUPER AGENT SYSTEM DIAGNOSTICS
echo ==========================================
echo.
echo Starting comprehensive system validation...
echo.

REM Set error handling
setlocal enabledelayedexpansion
set ERRORS=0
set WARNINGS=0

REM Create diagnostics report directory
if not exist "diagnostics-report" mkdir diagnostics-report
set REPORT_FILE=diagnostics-report\report_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.txt
set REPORT_FILE=%REPORT_FILE: =0%

echo Diagnostic Report > %REPORT_FILE%
echo ================== >> %REPORT_FILE%
echo Date: %date% %time% >> %REPORT_FILE%
echo. >> %REPORT_FILE%

REM 1. Check Node.js version
echo [1/10] Checking Node.js version...
echo. >> %REPORT_FILE%
echo NODE.JS CHECK: >> %REPORT_FILE%
node --version > temp.txt 2>&1
if %errorlevel% neq 0 (
    echo    ERROR: Node.js not found!
    echo ERROR: Node.js not found >> %REPORT_FILE%
    set /a ERRORS+=1
) else (
    set /p NODE_VERSION=<temp.txt
    echo    OK: Node.js !NODE_VERSION! installed
    echo OK: Node.js !NODE_VERSION! installed >> %REPORT_FILE%
)

REM 2. Check Python version
echo [2/10] Checking Python version...
echo. >> %REPORT_FILE%
echo PYTHON CHECK: >> %REPORT_FILE%
python --version > temp.txt 2>&1
if %errorlevel% neq 0 (
    echo    WARNING: Python not found - needed for doc generation
    echo WARNING: Python not found >> %REPORT_FILE%
    set /a WARNINGS+=1
) else (
    set /p PYTHON_VERSION=<temp.txt
    echo    OK: !PYTHON_VERSION! installed
    echo OK: !PYTHON_VERSION! installed >> %REPORT_FILE%
)

REM 3. Check npm dependencies
echo [3/10] Checking npm dependencies...
echo. >> %REPORT_FILE%
echo NPM DEPENDENCIES CHECK: >> %REPORT_FILE%
cd agent-dashboard
call npm list --depth=0 > ..\temp.txt 2>&1
if %errorlevel% neq 0 (
    echo    ERROR: Missing npm dependencies!
    echo ERROR: Missing dependencies - run npm install >> %REPORT_FILE%
    set /a ERRORS+=1
) else (
    echo    OK: All dependencies installed
    echo OK: All dependencies installed >> %REPORT_FILE%
)

REM 4. Run security audit
echo [4/10] Running security audit...
echo. >> %REPORT_FILE%
echo SECURITY AUDIT: >> %REPORT_FILE%
call npm audit --production > ..\temp_audit.txt 2>&1
findstr /C:"found 0 vulnerabilities" ..\temp_audit.txt > nul
if %errorlevel% neq 0 (
    echo    WARNING: Security vulnerabilities found
    echo WARNING: Vulnerabilities found - check npm audit >> %REPORT_FILE%
    type ..\temp_audit.txt >> %REPORT_FILE%
    set /a WARNINGS+=1
) else (
    echo    OK: No security vulnerabilities
    echo OK: No vulnerabilities found >> %REPORT_FILE%
)

REM 5. Check environment configuration
echo [5/10] Checking environment configuration...
echo. >> %REPORT_FILE%
echo ENVIRONMENT CHECK: >> %REPORT_FILE%
cd ..
if not exist ".env" (
    echo    WARNING: .env file not found
    echo WARNING: .env file missing - copy from .env.example >> %REPORT_FILE%
    set /a WARNINGS+=1
) else (
    echo    OK: .env file exists
    echo OK: .env file exists >> %REPORT_FILE%
)

REM 6. Run tests
echo [6/10] Running test suite...
echo. >> %REPORT_FILE%
echo TEST SUITE: >> %REPORT_FILE%
cd agent-dashboard
call npm test -- --passWithNoTests > ..\temp_test.txt 2>&1
if %errorlevel% neq 0 (
    echo    ERROR: Tests failed!
    echo ERROR: Test failures detected >> %REPORT_FILE%
    type ..\temp_test.txt >> %REPORT_FILE%
    set /a ERRORS+=1
) else (
    echo    OK: All tests passed
    echo OK: All tests passed >> %REPORT_FILE%
)

REM 7. Check file permissions
echo [7/10] Checking file permissions...
echo. >> %REPORT_FILE%
echo FILE PERMISSIONS CHECK: >> %REPORT_FILE%
cd ..
if exist "ADMIN_CREDENTIALS.txt" (
    echo    WARNING: Admin credentials file exists - should be deleted after use
    echo WARNING: ADMIN_CREDENTIALS.txt exists - delete after noting credentials >> %REPORT_FILE%
    set /a WARNINGS+=1
)
echo OK: File permissions check complete >> %REPORT_FILE%

REM 8. Validate project structure
echo [8/10] Validating project structure...
echo. >> %REPORT_FILE%
echo PROJECT STRUCTURE CHECK: >> %REPORT_FILE%
set REQUIRED_DIRS=agent-dashboard config daily-ops docs
for %%D in (%REQUIRED_DIRS%) do (
    if not exist "%%D" (
        echo    ERROR: Missing directory: %%D
        echo ERROR: Missing directory: %%D >> %REPORT_FILE%
        set /a ERRORS+=1
    )
)
if !ERRORS! equ 0 (
    echo    OK: All required directories present
    echo OK: Project structure valid >> %REPORT_FILE%
)

REM 9. Check Git status
echo [9/10] Checking Git status...
echo. >> %REPORT_FILE%
echo GIT STATUS CHECK: >> %REPORT_FILE%
git status --porcelain > temp_git.txt 2>&1
if %errorlevel% neq 0 (
    echo    ERROR: Git repository issues
    echo ERROR: Git command failed >> %REPORT_FILE%
    set /a ERRORS+=1
) else (
    for /f %%A in ('type temp_git.txt ^| find /c /v ""') do set GIT_CHANGES=%%A
    if !GIT_CHANGES! gtr 0 (
        echo    INFO: !GIT_CHANGES! uncommitted changes
        echo INFO: !GIT_CHANGES! uncommitted changes found >> %REPORT_FILE%
        type temp_git.txt >> %REPORT_FILE%
    ) else (
        echo    OK: Working directory clean
        echo OK: Working directory clean >> %REPORT_FILE%
    )
)

REM 10. Run custom security check
echo [10/10] Running security validation...
echo. >> %REPORT_FILE%
echo SECURITY VALIDATION: >> %REPORT_FILE%
node security-audit.js > temp_security.txt 2>&1
if %errorlevel% neq 0 (
    echo    ERROR: Security audit failed
    echo ERROR: Security audit failed >> %REPORT_FILE%
    set /a ERRORS+=1
) else (
    findstr /C:"CRITICAL VULNERABILITIES: 0" temp_security.txt > nul
    if %errorlevel% equ 0 (
        echo    OK: No critical security issues
        echo OK: No critical vulnerabilities >> %REPORT_FILE%
    ) else (
        echo    ERROR: Critical security issues found!
        echo ERROR: Critical vulnerabilities detected >> %REPORT_FILE%
        type temp_security.txt >> %REPORT_FILE%
        set /a ERRORS+=1
    )
)

REM Clean up temp files
del temp.txt temp_audit.txt temp_test.txt temp_git.txt temp_security.txt 2>nul

REM Generate summary
echo.
echo ==========================================
echo    DIAGNOSTIC SUMMARY
echo ==========================================
echo.
echo    Total Errors:   !ERRORS!
echo    Total Warnings: !WARNINGS!
echo.

echo. >> %REPORT_FILE%
echo SUMMARY: >> %REPORT_FILE%
echo Total Errors: !ERRORS! >> %REPORT_FILE%
echo Total Warnings: !WARNINGS! >> %REPORT_FILE%

if !ERRORS! gtr 0 (
    echo    STATUS: FAILED - Fix errors before pushing to Git!
    echo. >> %REPORT_FILE%
    echo STATUS: FAILED - DO NOT PUSH TO GIT >> %REPORT_FILE%
    echo.
    echo    Critical issues detected. Please fix all errors before proceeding.
    echo    See full report at: %REPORT_FILE%
    echo.
    exit /b 1
) else if !WARNINGS! gtr 0 (
    echo    STATUS: PASSED WITH WARNINGS
    echo. >> %REPORT_FILE%
    echo STATUS: PASSED WITH WARNINGS >> %REPORT_FILE%
    echo.
    echo    System is ready for Git push, but please review warnings.
    echo    See full report at: %REPORT_FILE%
    echo.
    choice /C YN /M "Continue with warnings"
    if errorlevel 2 exit /b 1
) else (
    echo    STATUS: PASSED - System ready for Git push!
    echo. >> %REPORT_FILE%
    echo STATUS: PASSED - READY FOR GIT PUSH >> %REPORT_FILE%
    echo.
    echo    All checks passed successfully!
    echo    See full report at: %REPORT_FILE%
    echo.
)

echo ==========================================
echo Full diagnostic report saved to:
echo %REPORT_FILE%
echo ==========================================
echo.

endlocal
pause