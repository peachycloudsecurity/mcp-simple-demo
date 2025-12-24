# MCP Security Lab - Learning MCP with Local LLM

A complete Model Context Protocol (MCP) implementation with server, client, and LLM integration for security tool execution.

## Quick Start

1. **Setup:**
   ```bash
   ./setup.sh
   ```

2. **Run:**
   ```bash
   ./start.sh
   ```

## Troubleshooting

### Memory Error

If you see: `model requires more system memory than is available`

**Solution:**
```bash
# Edit .env file
OLLAMA_MODEL=llama3.2:1b

# Pull smaller model
ollama pull llama3.2:1b

# Restart
./start.sh
```

### Model Options

- `llama3.2:1b` - ~1.3GB ⭐ **Recommended for low memory** (supports tools)
- `llama3.2:3b` - ~2.3GB (better quality, requires 3GB+ free RAM, supports tools)

**Important:** 
- `tinyllama` does **NOT** support tools, so it won't work with MCP
- Use `llama3.2:1b` for low memory systems
- Setup script automatically detects memory and selects appropriate model

## Cleanup Models

To remove models that don't support tools (like tinyllama):

```bash
# List all models
ollama list

# Remove specific model
ollama rm tinyllama

# Or use the cleanup script
./cleanup_models.sh
```