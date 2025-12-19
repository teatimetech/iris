#!/bin/bash
# Platform Detection Script for PyTorch Installation
# Detects OS and GPU to determine appropriate PyTorch index URL

set -e

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
    # Check for Apple Silicon
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" ]]; then
        GPU_TYPE="apple_silicon"
        PYTORCH_INDEX="default"  # PyTorch uses Metal automatically
    else
        GPU_TYPE="none"
        PYTORCH_INDEX="https://download.pytorch.org/whl/cpu"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
    # Check for NVIDIA GPU
    if command -v nvidia-smi &> /dev/null; then
        GPU_TYPE="nvidia"
        # Check CUDA version (assuming CUDA 12.x)
        PYTORCH_INDEX="https://download.pytorch.org/whl/cu128"
    else
        GPU_TYPE="none"
        PYTORCH_INDEX="https://download.pytorch.org/whl/cpu"
    fi
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    OS_TYPE="windows"
    # Check for NVIDIA GPU on Windows
    if command -v nvidia-smi &> /dev/null || [ -f "/c/Program Files/NVIDIA Corporation/NVSMI/nvidia-smi.exe" ]; then
        GPU_TYPE="nvidia"
        PYTORCH_INDEX="https://download.pytorch.org/whl/cu128"
    else
        GPU_TYPE="none"
        PYTORCH_INDEX="https://download.pytorch.org/whl/cpu"
    fi
else
    OS_TYPE="unknown"
    GPU_TYPE="none"
    PYTORCH_INDEX="https://download.pytorch.org/whl/cpu"
fi

# Output results
echo "OS_TYPE=$OS_TYPE"
echo "GPU_TYPE=$GPU_TYPE"
echo "PYTORCH_INDEX=$PYTORCH_INDEX"

# Export for docker-compose
export PYTORCH_INDEX

# Write to .env file
if [ -f ".env" ]; then
    # Update existing .env
    if grep -q "^PYTORCH_INDEX=" .env; then
        sed -i.bak "s|^PYTORCH_INDEX=.*|PYTORCH_INDEX=$PYTORCH_INDEX|" .env
    else
        echo "PYTORCH_INDEX=$PYTORCH_INDEX" >> .env
    fi
else
    # Create new .env
    echo "PYTORCH_INDEX=$PYTORCH_INDEX" > .env
fi

echo "✅ Platform detection complete: $OS_TYPE with $GPU_TYPE"
echo "✅ PyTorch index: $PYTORCH_INDEX"
