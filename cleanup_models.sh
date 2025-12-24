#!/bin/bash

# Cleanup Ollama Models Script
# Removes models that don't support tools or are not needed

set -e

echo "========================================"
echo "Ollama Models Cleanup"
echo "========================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# List all models
echo -e "\n${YELLOW}Current models:${NC}"
ollama list

# Models to keep (that support tools)
KEEP_MODELS=("llama3.2:1b" "llama3.2:3b" "llama3.2" "qwen2.5" "mistral")

# Models to remove (don't support tools or not needed)
REMOVE_MODELS=("tinyllama")

echo -e "\n${YELLOW}Models that will be removed (don't support tools):${NC}"
for model in "${REMOVE_MODELS[@]}"; do
    if ollama list | grep -q "$model"; then
        echo -e "  - ${RED}$model${NC}"
    fi
done

# Ask for confirmation
echo -e "\n${YELLOW}Do you want to remove these models? (y/n)${NC}"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    for model in "${REMOVE_MODELS[@]}"; do
        if ollama list | grep -q "$model"; then
            echo -e "\n${YELLOW}Removing $model...${NC}"
            ollama rm "$model"
            echo -e "${GREEN}Removed $model${NC}"
        else
            echo -e "${YELLOW}$model not found, skipping${NC}"
        fi
    done
    
    echo -e "\n${GREEN}========================================"
    echo -e "Cleanup complete!"
    echo -e "========================================${NC}"
    echo -e "\n${YELLOW}Remaining models:${NC}"
    ollama list
else
    echo -e "\n${YELLOW}Cleanup cancelled${NC}"
fi

