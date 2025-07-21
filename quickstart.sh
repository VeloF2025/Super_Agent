#!/bin/bash
#
# Jarvis Super Agent - One-Command Quick Start
# This script gets you from zero to running in under 2 minutes
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "     ╦╔═╗╦═╗╦  ╦╦╔═╗"
echo "     ║╠═╣╠╦╝╚╗╔╝║╚═╗"
echo "    ╚╝╩ ╩╩╚═ ╚╝ ╩╚═╝"
echo "  Super Agent System v2.0"
echo -e "${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)

echo -e "${YELLOW}🚀 Starting Jarvis Quick Setup...${NC}\n"

# Check for Docker
if command_exists docker && command_exists docker-compose; then
    echo -e "${GREEN}✓ Docker detected - Using Docker setup (Recommended)${NC}"
    USE_DOCKER=true
else
    echo -e "${YELLOW}⚠ Docker not found - Using local setup${NC}"
    USE_DOCKER=false
fi

# Quick API key setup
echo -e "\n${BLUE}API Keys Setup (Press Enter to skip)${NC}"
read -p "OpenAI API Key: " OPENAI_KEY
read -p "Anthropic API Key: " ANTHROPIC_KEY

# Create .env file
cat > .env << EOF
# Jarvis Configuration
OPENAI_API_KEY=${OPENAI_KEY}
ANTHROPIC_API_KEY=${ANTHROPIC_KEY}
DASHBOARD_PORT=3000
API_PORT=8000
AGENT_COUNT=5
EOF

if [ "$USE_DOCKER" = true ]; then
    # Docker setup
    echo -e "\n${YELLOW}🐳 Setting up with Docker...${NC}"
    
    # Create docker override for development
    cat > docker-compose.override.yml << EOF
version: '3.8'
services:
  jarvis-api:
    volumes:
      - .:/app
    environment:
      - DEBUG=true
EOF
    
    # Build and start
    echo -e "${YELLOW}Building containers...${NC}"
    docker-compose build --quiet
    
    echo -e "${YELLOW}Starting services...${NC}"
    docker-compose up -d
    
    # Wait for services
    echo -e "${YELLOW}Waiting for services to start...${NC}"
    sleep 10
    
    # Check health
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✓ API is running${NC}"
    fi
    
    if curl -s http://localhost:3000 > /dev/null; then
        echo -e "${GREEN}✓ Dashboard is running${NC}"
    fi
    
else
    # Local setup
    echo -e "\n${YELLOW}📦 Setting up locally...${NC}"
    
    # Check Python
    if ! command_exists python3; then
        echo -e "${RED}✗ Python 3 is required${NC}"
        exit 1
    fi
    
    # Check Node
    if ! command_exists node; then
        echo -e "${RED}✗ Node.js is required${NC}"
        echo "Install from: https://nodejs.org/"
        exit 1
    fi
    
    # Install dependencies
    echo -e "${YELLOW}Installing dependencies...${NC}"
    
    # Create virtual environment
    python3 -m venv venv
    
    # Activate virtual environment
    if [ "$OS" = "windows" ]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    # Install Python packages
    pip install -r requirements.txt --quiet
    
    # Install Node packages
    npm install --silent
    cd agent-dashboard && npm install --silent
    cd client && npm install --silent
    cd ../..
    
    # Create directories
    mkdir -p data logs memory/context/jarvis/checkpoints projects config
    
    # Create start script
    cat > start-local.sh << 'SCRIPT'
#!/bin/bash
echo "Starting Jarvis..."

# Start API
python -m uvicorn api.main:app --port 8000 --reload &
API_PID=$!

# Start Dashboard
cd agent-dashboard && npm run dev &
DASHBOARD_PID=$!

echo -e "\n✓ Jarvis is running!"
echo "Dashboard: http://localhost:3000"
echo "API: http://localhost:8000/docs"
echo -e "\nPress Ctrl+C to stop"

trap "kill $API_PID $DASHBOARD_PID; exit" INT
wait
SCRIPT
    
    chmod +x start-local.sh
    
    # Start services
    ./start-local.sh &
    JARVIS_PID=$!
    
    sleep 10
fi

# Create first project
echo -e "\n${YELLOW}📁 Creating your first project...${NC}"

mkdir -p projects/hello_jarvis
cat > projects/hello_jarvis/project.json << EOF
{
  "id": "project-001",
  "name": "Hello Jarvis",
  "type": "tutorial",
  "status": "active",
  "description": "Your first AI-powered project"
}
EOF

# Success message
echo -e "\n${GREEN}✨ Setup Complete!${NC}\n"
echo -e "${BLUE}Jarvis is now running!${NC}"
echo -e "Dashboard: ${GREEN}http://localhost:3000${NC}"
echo -e "API Docs: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Open the dashboard in your browser"
echo "2. Click 'ML Optimization' to see AI insights"
echo "3. Create your first task in the dashboard"
echo -e "\n${BLUE}Quick Commands:${NC}"

if [ "$USE_DOCKER" = true ]; then
    echo "Stop: docker-compose down"
    echo "Logs: docker-compose logs -f"
    echo "Restart: docker-compose restart"
else
    echo "Stop: Press Ctrl+C"
    echo "Restart: ./start-local.sh"
fi

echo -e "\n${GREEN}Enjoy building with Jarvis! 🚀${NC}"

# Open browser
if [ "$OS" = "macos" ]; then
    open http://localhost:3000
elif [ "$OS" = "linux" ]; then
    xdg-open http://localhost:3000 2>/dev/null || echo "Please open http://localhost:3000 in your browser"
fi

# Keep script running if local setup
if [ "$USE_DOCKER" = false ]; then
    wait $JARVIS_PID
fi