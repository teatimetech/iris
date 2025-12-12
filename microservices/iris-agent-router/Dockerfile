# Use Debian-slim instead of Alpine for better Python package compatibility
# Alpine has issues with numpy and other scientific packages
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for Python packages
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r requirements.txt && \
    apt-get purge -y gcc g++ && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Run the FastAPI application using Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
