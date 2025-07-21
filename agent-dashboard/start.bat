@echo off
echo ====================================
echo OA Agent Dashboard - Starting...
echo ====================================
echo.

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    call npm run setup
    echo.
)

if not exist "client\node_modules" (
    echo Installing client dependencies...
    cd client && npm install && cd ..
    echo.
)

REM Create data directory if it doesn't exist
if not exist "data" (
    echo Creating data directory...
    mkdir data
)

echo Starting dashboard in development mode...
echo.
echo Backend will run on: http://localhost:3001
echo Frontend will run on: http://localhost:3000
echo.
echo Press Ctrl+C to stop the servers
echo ====================================
echo.

npm run dev