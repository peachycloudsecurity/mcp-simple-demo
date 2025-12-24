#!/bin/bash
# Fix corrupted Ollama model

set -e

echo "=========================================="
echo "Fixing Corrupted Ollama Model"
echo "=========================================="

# Step 1: Stop Ollama
echo ""
echo "[1/5] Stopping Ollama..."
pkill ollama || echo "  Ollama not running (OK)"
sleep 2

# Step 2: Remove corrupted model
echo ""
echo "[2/5] Removing corrupted model..."
ollama rm llama3.2:1b 2>/dev/null || echo "  Model not found (OK)"

# Step 3: Start Ollama server
echo ""
echo "[3/5] Starting Ollama server..."
ollama serve > /dev/null 2>&1 &
OLLAMA_PID=$!
echo "  Ollama started (PID: $OLLAMA_PID)"

# Step 4: Wait for server to be ready
echo ""
echo "[4/5] Waiting for Ollama to be ready..."
for i in {1..10}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "  ✓ Ollama is ready!"
        break
    fi
    echo "  Waiting... ($i/10)"
    sleep 1
done

# Step 5: Pull fresh model
echo ""
echo "[5/5] Pulling fresh model (this may take a few minutes)..."
ollama pull llama3.2:1b

# Verify
echo ""
echo "=========================================="
echo "Verification"
echo "=========================================="
echo ""
echo "Testing model..."
ollama run llama3.2:1b "test" --verbose 2>&1 | head -5

echo ""
echo "=========================================="
echo "✓ Fix complete!"
echo "=========================================="
echo ""
echo "You can now run your mcp-mine application:"
echo "  python main.py"
echo ""

