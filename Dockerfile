# ============================================================
# ReplicarIA - Dockerfile for Railway Deployment
# ============================================================

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first (for caching)
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy the rest of the application
COPY backend /app/backend

# Set working directory to backend
WORKDIR /app/backend

# Expose port
EXPOSE 5000

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
