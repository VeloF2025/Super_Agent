#!/bin/bash

echo "=========================================="
echo "   SUPER AGENT HTTPS SETUP"
echo "=========================================="
echo

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running with sudo (if needed)
if [ "$EUID" -ne 0 ] && [ ! -w "." ]; then 
    echo -e "${RED}This script needs write permissions in the current directory.${NC}"
    echo "Please run with appropriate permissions or use sudo."
    exit 1
fi

# Create certificates directory
if [ ! -d "certs" ]; then
    mkdir -p certs
    echo -e "${GREEN}Created certs directory${NC}"
fi

# Check if OpenSSL is installed
if ! command -v openssl &> /dev/null; then
    echo
    echo -e "${RED}ERROR: OpenSSL is not installed.${NC}"
    echo
    echo "Please install OpenSSL:"
    echo "  Ubuntu/Debian: sudo apt-get install openssl"
    echo "  CentOS/RHEL: sudo yum install openssl"
    echo "  macOS: brew install openssl"
    echo
    exit 1
fi

echo
echo "Found OpenSSL installation..."
openssl version

# Check if certificates already exist
if [ -f "certs/server.crt" ]; then
    echo
    echo -e "${YELLOW}WARNING: SSL certificates already exist!${NC}"
    read -p "Do you want to regenerate them? This will overwrite existing certificates. (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping certificate generation..."
    else
        GENERATE_CERTS=true
    fi
else
    GENERATE_CERTS=true
fi

if [ "$GENERATE_CERTS" = true ]; then
    echo
    echo "=========================================="
    echo "   GENERATING SSL CERTIFICATES"
    echo "=========================================="
    echo
    echo "This will generate a self-signed certificate for development."
    echo "For production, use certificates from a trusted CA."
    echo

    # Generate private key
    echo "Generating private key..."
    openssl genrsa -out certs/server.key 4096

    # Generate certificate
    echo
    echo "Generating self-signed certificate..."
    echo "Using default values for development..."
    
    # Create certificate with default values for development
    openssl req -new -x509 -key certs/server.key -out certs/server.crt -days 365 \
        -subj "/C=US/ST=State/L=City/O=Super Agent System/OU=Development/CN=localhost"

    # Set appropriate permissions
    chmod 600 certs/server.key
    chmod 644 certs/server.crt

    echo
    echo -e "${GREEN}✅ SSL certificates generated successfully!${NC}"
fi

# Create or update .env file
echo
echo "=========================================="
echo "   UPDATING ENVIRONMENT CONFIGURATION"
echo "=========================================="

if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

# Update .env file for HTTPS
echo
echo "Updating .env file for HTTPS..."

# Function to update or add environment variable
update_env() {
    local key=$1
    local value=$2
    if grep -q "^${key}=" .env; then
        # Update existing
        sed -i.bak "s|^${key}=.*|${key}=${value}|" .env
    else
        # Add new
        echo "${key}=${value}" >> .env
    fi
}

update_env "ENABLE_HTTPS" "\"true\""
update_env "SSL_CERT_PATH" "\"./certs/server.crt\""
update_env "SSL_KEY_PATH" "\"./certs/server.key\""

# Remove backup file
rm -f .env.bak

echo -e "${GREEN}✅ Environment configuration updated${NC}"

# Install dependencies if needed
echo
echo "=========================================="
echo "   CHECKING DEPENDENCIES"
echo "=========================================="

cd agent-dashboard
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
else
    echo "Dependencies already installed"
fi

# Create systemd service file (optional)
if command -v systemctl &> /dev/null && [ "$EUID" -eq 0 ]; then
    echo
    read -p "Do you want to create a systemd service for auto-start? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cat > /etc/systemd/system/super-agent-dashboard.service << EOF
[Unit]
Description=Super Agent Dashboard
After=network.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/node server/index-secure.js
Restart=on-failure
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=super-agent-dashboard
Environment="NODE_ENV=production"

[Install]
WantedBy=multi-user.target
EOF

        systemctl daemon-reload
        echo -e "${GREEN}✅ Systemd service created${NC}"
        echo "To enable auto-start: sudo systemctl enable super-agent-dashboard"
        echo "To start now: sudo systemctl start super-agent-dashboard"
    fi
fi

echo
echo "=========================================="
echo "   HTTPS SETUP COMPLETE!"
echo "=========================================="
echo
echo -e "${GREEN}Your Super Agent Dashboard is now configured for HTTPS.${NC}"
echo
echo "To start the secure server:"
echo "  cd agent-dashboard"
echo "  npm run start:secure"
echo
echo "The dashboard will be available at:"
echo "  https://localhost:3010"
echo
echo -e "${YELLOW}NOTE: Your browser will show a security warning because this is"
echo "a self-signed certificate. This is normal for development."
echo "Click \"Advanced\" and \"Proceed to localhost\" to continue.${NC}"
echo
echo "For production, replace the certificates in the certs/ directory"
echo "with certificates from a trusted Certificate Authority."
echo