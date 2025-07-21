#!/bin/bash

echo "=========================================="
echo "   SUPER AGENT SYSTEM DIAGNOSTICS"
echo "=========================================="
echo
echo "Starting comprehensive system validation..."
echo

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Initialize counters
ERRORS=0
WARNINGS=0

# Create diagnostics report directory
mkdir -p diagnostics-report
REPORT_FILE="diagnostics-report/report_$(date +%Y%m%d_%H%M%S).txt"

echo "Diagnostic Report" > "$REPORT_FILE"
echo "==================" >> "$REPORT_FILE"
echo "Date: $(date)" >> "$REPORT_FILE"
echo >> "$REPORT_FILE"

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Check Node.js version
echo "[1/10] Checking Node.js version..."
echo >> "$REPORT_FILE"
echo "NODE.JS CHECK:" >> "$REPORT_FILE"
if command_exists node; then
    NODE_VERSION=$(node --version)
    echo -e "   ${GREEN}OK${NC}: Node.js $NODE_VERSION installed"
    echo "OK: Node.js $NODE_VERSION installed" >> "$REPORT_FILE"
else
    echo -e "   ${RED}ERROR${NC}: Node.js not found!"
    echo "ERROR: Node.js not found" >> "$REPORT_FILE"
    ((ERRORS++))
fi

# 2. Check Python version
echo "[2/10] Checking Python version..."
echo >> "$REPORT_FILE"
echo "PYTHON CHECK:" >> "$REPORT_FILE"
if command_exists python || command_exists python3; then
    PYTHON_CMD=$(command_exists python3 && echo "python3" || echo "python")
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
    echo -e "   ${GREEN}OK${NC}: $PYTHON_VERSION installed"
    echo "OK: $PYTHON_VERSION installed" >> "$REPORT_FILE"
else
    echo -e "   ${YELLOW}WARNING${NC}: Python not found - needed for doc generation"
    echo "WARNING: Python not found" >> "$REPORT_FILE"
    ((WARNINGS++))
fi

# 3. Check npm dependencies
echo "[3/10] Checking npm dependencies..."
echo >> "$REPORT_FILE"
echo "NPM DEPENDENCIES CHECK:" >> "$REPORT_FILE"
cd agent-dashboard
if npm list --depth=0 &>/dev/null; then
    echo -e "   ${GREEN}OK${NC}: All dependencies installed"
    echo "OK: All dependencies installed" >> "$REPORT_FILE"
else
    echo -e "   ${RED}ERROR${NC}: Missing npm dependencies!"
    echo "ERROR: Missing dependencies - run npm install" >> "$REPORT_FILE"
    ((ERRORS++))
fi

# 4. Run security audit
echo "[4/10] Running security audit..."
echo >> "$REPORT_FILE"
echo "SECURITY AUDIT:" >> "$REPORT_FILE"
AUDIT_OUTPUT=$(npm audit --production 2>&1)
if echo "$AUDIT_OUTPUT" | grep -q "found 0 vulnerabilities"; then
    echo -e "   ${GREEN}OK${NC}: No security vulnerabilities"
    echo "OK: No vulnerabilities found" >> "$REPORT_FILE"
else
    echo -e "   ${YELLOW}WARNING${NC}: Security vulnerabilities found"
    echo "WARNING: Vulnerabilities found - check npm audit" >> "$REPORT_FILE"
    echo "$AUDIT_OUTPUT" >> "$REPORT_FILE"
    ((WARNINGS++))
fi

# 5. Check environment configuration
echo "[5/10] Checking environment configuration..."
echo >> "$REPORT_FILE"
echo "ENVIRONMENT CHECK:" >> "$REPORT_FILE"
cd ..
if [ ! -f ".env" ]; then
    echo -e "   ${YELLOW}WARNING${NC}: .env file not found"
    echo "WARNING: .env file missing - copy from .env.example" >> "$REPORT_FILE"
    ((WARNINGS++))
else
    echo -e "   ${GREEN}OK${NC}: .env file exists"
    echo "OK: .env file exists" >> "$REPORT_FILE"
fi

# 6. Run tests
echo "[6/10] Running test suite..."
echo >> "$REPORT_FILE"
echo "TEST SUITE:" >> "$REPORT_FILE"
cd agent-dashboard
if npm test -- --passWithNoTests &>/dev/null; then
    echo -e "   ${GREEN}OK${NC}: All tests passed"
    echo "OK: All tests passed" >> "$REPORT_FILE"
else
    echo -e "   ${RED}ERROR${NC}: Tests failed!"
    echo "ERROR: Test failures detected" >> "$REPORT_FILE"
    npm test -- --passWithNoTests >> "$REPORT_FILE" 2>&1
    ((ERRORS++))
fi

# 7. Check file permissions
echo "[7/10] Checking file permissions..."
echo >> "$REPORT_FILE"
echo "FILE PERMISSIONS CHECK:" >> "$REPORT_FILE"
cd ..
if [ -f "ADMIN_CREDENTIALS.txt" ]; then
    echo -e "   ${YELLOW}WARNING${NC}: Admin credentials file exists - should be deleted after use"
    echo "WARNING: ADMIN_CREDENTIALS.txt exists - delete after noting credentials" >> "$REPORT_FILE"
    ((WARNINGS++))
fi

# Check execute permissions on scripts
for script in setup-https.sh run-diagnostics.sh; do
    if [ -f "$script" ] && [ ! -x "$script" ]; then
        echo -e "   ${YELLOW}WARNING${NC}: $script is not executable"
        echo "WARNING: $script needs execute permission" >> "$REPORT_FILE"
        ((WARNINGS++))
    fi
done
echo "OK: File permissions check complete" >> "$REPORT_FILE"

# 8. Validate project structure
echo "[8/10] Validating project structure..."
echo >> "$REPORT_FILE"
echo "PROJECT STRUCTURE CHECK:" >> "$REPORT_FILE"
REQUIRED_DIRS=("agent-dashboard" "config" "daily-ops" "docs")
STRUCTURE_OK=true
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo -e "   ${RED}ERROR${NC}: Missing directory: $dir"
        echo "ERROR: Missing directory: $dir" >> "$REPORT_FILE"
        ((ERRORS++))
        STRUCTURE_OK=false
    fi
done
if $STRUCTURE_OK; then
    echo -e "   ${GREEN}OK${NC}: All required directories present"
    echo "OK: Project structure valid" >> "$REPORT_FILE"
fi

# 9. Check Git status
echo "[9/10] Checking Git status..."
echo >> "$REPORT_FILE"
echo "GIT STATUS CHECK:" >> "$REPORT_FILE"
if command_exists git; then
    GIT_STATUS=$(git status --porcelain 2>&1)
    if [ $? -ne 0 ]; then
        echo -e "   ${RED}ERROR${NC}: Git repository issues"
        echo "ERROR: Git command failed" >> "$REPORT_FILE"
        ((ERRORS++))
    else
        CHANGES=$(echo "$GIT_STATUS" | wc -l)
        if [ "$GIT_STATUS" != "" ]; then
            echo -e "   INFO: $CHANGES uncommitted changes"
            echo "INFO: $CHANGES uncommitted changes found" >> "$REPORT_FILE"
            echo "$GIT_STATUS" >> "$REPORT_FILE"
        else
            echo -e "   ${GREEN}OK${NC}: Working directory clean"
            echo "OK: Working directory clean" >> "$REPORT_FILE"
        fi
    fi
else
    echo -e "   ${RED}ERROR${NC}: Git not installed"
    echo "ERROR: Git not found" >> "$REPORT_FILE"
    ((ERRORS++))
fi

# 10. Run custom security check
echo "[10/10] Running security validation..."
echo >> "$REPORT_FILE"
echo "SECURITY VALIDATION:" >> "$REPORT_FILE"
if node security-audit.js &>/dev/null; then
    SECURITY_OUTPUT=$(node security-audit.js 2>&1)
    if echo "$SECURITY_OUTPUT" | grep -q "CRITICAL VULNERABILITIES: 0"; then
        echo -e "   ${GREEN}OK${NC}: No critical security issues"
        echo "OK: No critical vulnerabilities" >> "$REPORT_FILE"
    else
        echo -e "   ${RED}ERROR${NC}: Critical security issues found!"
        echo "ERROR: Critical vulnerabilities detected" >> "$REPORT_FILE"
        echo "$SECURITY_OUTPUT" >> "$REPORT_FILE"
        ((ERRORS++))
    fi
else
    echo -e "   ${RED}ERROR${NC}: Security audit failed"
    echo "ERROR: Security audit failed" >> "$REPORT_FILE"
    ((ERRORS++))
fi

# Generate summary
echo
echo "=========================================="
echo "   DIAGNOSTIC SUMMARY"
echo "=========================================="
echo
echo "   Total Errors:   $ERRORS"
echo "   Total Warnings: $WARNINGS"
echo

echo >> "$REPORT_FILE"
echo "SUMMARY:" >> "$REPORT_FILE"
echo "Total Errors: $ERRORS" >> "$REPORT_FILE"
echo "Total Warnings: $WARNINGS" >> "$REPORT_FILE"

if [ $ERRORS -gt 0 ]; then
    echo -e "   STATUS: ${RED}FAILED${NC} - Fix errors before pushing to Git!"
    echo >> "$REPORT_FILE"
    echo "STATUS: FAILED - DO NOT PUSH TO GIT" >> "$REPORT_FILE"
    echo
    echo "   Critical issues detected. Please fix all errors before proceeding."
    echo "   See full report at: $REPORT_FILE"
    echo
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "   STATUS: ${YELLOW}PASSED WITH WARNINGS${NC}"
    echo >> "$REPORT_FILE"
    echo "STATUS: PASSED WITH WARNINGS" >> "$REPORT_FILE"
    echo
    echo "   System is ready for Git push, but please review warnings."
    echo "   See full report at: $REPORT_FILE"
    echo
    read -p "Continue with warnings? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "   STATUS: ${GREEN}PASSED${NC} - System ready for Git push!"
    echo >> "$REPORT_FILE"
    echo "STATUS: PASSED - READY FOR GIT PUSH" >> "$REPORT_FILE"
    echo
    echo "   All checks passed successfully!"
    echo "   See full report at: $REPORT_FILE"
    echo
fi

echo "=========================================="
echo "Full diagnostic report saved to:"
echo "$REPORT_FILE"
echo "=========================================="
echo