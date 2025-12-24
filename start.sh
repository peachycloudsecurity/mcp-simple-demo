#!/bin/bash
# Start the AI Agent

set -e

cd "$(dirname "${BASH_SOURCE[0]}")"

[ ! -d venv ] && { echo "Run ./setup.sh first"; exit 1; }

source venv/bin/activate
pgrep -x ollama >/dev/null || { nohup ollama serve >ollama.log 2>&1 & sleep 2; }

python3 main.py
