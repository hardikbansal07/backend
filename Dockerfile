# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies required by some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (for better layer caching)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application source code
COPY backend/ .

# Cloud Run injects the PORT environment variable (default: 8080)
ENV PORT=8080

# Expose the port
EXPOSE 8080

# Start the FastAPI server using uvicorn, listening on $PORT
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
