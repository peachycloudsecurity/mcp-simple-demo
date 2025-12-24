#!/bin/bash
# AI Agent Setup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================"
echo "AI Agent Setup"
echo "========================================"

# Python check
echo -e "\n${YELLOW}Checking Python...${NC}"
command -v python3 &>/dev/null || { echo -e "${RED}Python 3 required${NC}"; exit 1; }
PYVER=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}Python $PYVER${NC}"

# System packages (Debian/Ubuntu)
if command -v apt &>/dev/null; then
    echo -e "\n${YELLOW}Installing system packages...${NC}"
    apt update -qq && apt install -y python3-pip python${PYVER}-venv
fi

# Virtual environment
echo -e "\n${YELLOW}Setting up virtual environment...${NC}"
[ -d venv ] && [ ! -f venv/bin/activate ] && rm -rf venv
[ ! -d venv ] && python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# Ollama
echo -e "\n${YELLOW}Checking Ollama...${NC}"
if ! command -v ollama &>/dev/null; then
    echo -e "${YELLOW}Installing Ollama...${NC}"
    curl -fsSL https://ollama.com/install.sh | sh
fi

pgrep -x ollama >/dev/null || { nohup ollama serve >ollama.log 2>&1 & sleep 3; }

# Model selection based on memory
MODEL="llama3.2:3b"
if command -v free &>/dev/null; then
    AVAIL=$(free -g | awk '/^Mem:/{print $7}')
    [ "$AVAIL" -lt 3 ] && MODEL="llama3.2:1b"
fi

echo -e "\n${YELLOW}Pulling model: $MODEL${NC}"
ollama pull "$MODEL"

# Create directories
mkdir -p data logs

# Environment file
[ ! -f .env ] && cat > .env << EOF
# LLM Configuration
LLM_API_ENDPOINT=http://localhost:11434
LLM_MODEL=$MODEL
LLM_TIMEOUT=120

# Server Configuration
SERVER_ID=tool-server
SERVER_HOST=127.0.0.1
SERVER_PORT=8765

# Logging
LOG_LEVEL=INFO
EOF

echo -e "\n${GREEN}========================================"
echo "Setup complete!"
echo "========================================"
echo -e "${NC}"
echo "Run: source venv/bin/activate && python3 main.py"
echo "Or:  ./start.sh"
