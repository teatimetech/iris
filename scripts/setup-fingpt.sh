#!/bin/bash
# Script to download and setup FinGPT model for Ollama

set -e

MODELS_DIR="./data/ollama/models"
GGUF_FILE="FinGPT-MT-Llama-3-8B-LoRA-Q5_K_M.gguf"
DOWNLOAD_URL="https://huggingface.co/second-state/FinGPT-MT-Llama-3-8B-LoRA-GGUF/resolve/main/FinGPT-MT-Llama-3-8B-LoRA-Q5_K_M.gguf"

echo "=================================================="
echo "FinGPT Model Setup for IRIS"
echo "=================================================="

# Create models directory
mkdir -p "$MODELS_DIR"

# Check if model already exists
if [ -f "$MODELS_DIR/$GGUF_FILE" ]; then
    echo "[OK] FinGPT model already downloaded"
else
    echo "[INFO] Downloading FinGPT model (this may take a while, ~5GB)..."
    echo "Source: $DOWNLOAD_URL"
    
    # Download with wget or curl
    if command -v wget &> /dev/null; then
        wget -O "$MODELS_DIR/$GGUF_FILE" "$DOWNLOAD_URL"
    elif command -v curl &> /dev/null; then
        curl -L -o "$MODELS_DIR/$GGUF_FILE" "$DOWNLOAD_URL"
    else
        echo "[ERROR] Neither wget nor curl found. Please install one of them."
        exit 1
    fi
    
    echo "[OK] Download complete"
fi

# Copy Modelfile to models directory
cp ./data/ollama/Modelfile.fingpt "$MODELS_DIR/"

echo ""
echo "[INFO] To import into Ollama, run:"
echo "  docker-compose exec ollama ollama create fingpt-mt-llama3 -f /root/.ollama/models/Modelfile.fingpt"
echo ""
echo "[OK] Setup complete"
