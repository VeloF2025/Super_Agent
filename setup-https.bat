@echo off
echo ==========================================
echo    SUPER AGENT HTTPS SETUP
echo ==========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges...
) else (
    echo This script requires administrator privileges for certificate generation.
    echo Please run as administrator.
    pause
    exit /b 1
)

REM Create certificates directory
if not exist "certs" (
    mkdir certs
    echo Created certs directory
)

REM Check if OpenSSL is installed
where openssl >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ERROR: OpenSSL is not installed or not in PATH.
    echo.
    echo Please install OpenSSL:
    echo 1. Download from: https://slproweb.com/products/Win32OpenSSL.html
    echo 2. Install Win64 OpenSSL (full version, not light)
    echo 3. Add OpenSSL\bin to your PATH environment variable
    echo.
    pause
    exit /b 1
)

echo.
echo Found OpenSSL installation...
openssl version

REM Check if certificates already exist
if exist "certs\server.crt" (
    echo.
    echo WARNING: SSL certificates already exist!
    echo Do you want to regenerate them? This will overwrite existing certificates.
    echo.
    choice /C YN /M "Continue"
    if errorlevel 2 goto :skip_generation
)

:generate_certs
echo.
echo ==========================================
echo    GENERATING SSL CERTIFICATES
echo ==========================================
echo.
echo This will generate a self-signed certificate for development.
echo For production, use certificates from a trusted CA.
echo.

REM Generate private key and certificate
echo Generating private key...
openssl genrsa -out certs\server.key 4096

echo.
echo Generating certificate signing request...
echo Please fill in the following information:
echo - Country Name: Your country code (e.g., US)
echo - State/Province: Your state
echo - Locality: Your city
echo - Organization: Your company name
echo - Organizational Unit: IT Department
echo - Common Name: localhost (or your domain)
echo - Email: your-email@example.com
echo.

openssl req -new -key certs\server.key -out certs\server.csr

echo.
echo Generating self-signed certificate (valid for 365 days)...
openssl x509 -req -days 365 -in certs\server.csr -signkey certs\server.key -out certs\server.crt

REM Clean up CSR file
del certs\server.csr

echo.
echo ✅ SSL certificates generated successfully!

:skip_generation

REM Create or update .env file
echo.
echo ==========================================
echo    UPDATING ENVIRONMENT CONFIGURATION
echo ==========================================

if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env >nul
)

REM Update .env file for HTTPS
echo.
echo Updating .env file for HTTPS...
powershell -Command "(Get-Content .env) -replace 'ENABLE_HTTPS=\"false\"', 'ENABLE_HTTPS=\"true\"' | Set-Content .env"
powershell -Command "(Get-Content .env) -replace 'SSL_CERT_PATH=.*', 'SSL_CERT_PATH=\"./certs/server.crt\"' | Set-Content .env"
powershell -Command "(Get-Content .env) -replace 'SSL_KEY_PATH=.*', 'SSL_KEY_PATH=\"./certs/server.key\"' | Set-Content .env"

echo ✅ Environment configuration updated

REM Install dependencies if needed
echo.
echo ==========================================
echo    CHECKING DEPENDENCIES
echo ==========================================

cd agent-dashboard
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
) else (
    echo Dependencies already installed
)

echo.
echo ==========================================
echo    HTTPS SETUP COMPLETE!
echo ==========================================
echo.
echo Your Super Agent Dashboard is now configured for HTTPS.
echo.
echo To start the secure server:
echo   cd agent-dashboard
echo   npm run start:secure
echo.
echo The dashboard will be available at:
echo   https://localhost:3010
echo.
echo NOTE: Your browser will show a security warning because this is
echo a self-signed certificate. This is normal for development.
echo Click "Advanced" and "Proceed to localhost" to continue.
echo.
echo For production, replace the certificates in the certs/ directory
echo with certificates from a trusted Certificate Authority.
echo.
pause