# Build argument for PyTorch index URL (platform-specific)
ARG PYTORCH_INDEX=https://download.pytorch.org/whl/cpu

# Use Debian-slim instead of Alpine for better Python package compatibility
# Alpine has issues with numpy and other scientific packages
FROM python:3.11-slim

WORKDIR /app

# Declare build arg in this stage
ARG PYTORCH_INDEX

# Install system dependencies required for Python packages
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++

# Install PyTorch with platform-specific index
RUN pip install torch torchvision --index-url ${PYTORCH_INDEX}

RUN pip install -r requirements.txt

RUN apt-get purge -y gcc g++ && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Run the FastAPI application using Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
