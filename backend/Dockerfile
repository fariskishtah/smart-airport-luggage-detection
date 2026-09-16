FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install system dependencies: ffmpeg for H.264 video processing, libgl for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy source, configs, and models
COPY src /app/src
COPY configs /app/configs
COPY models/deployment /app/models/deployment
COPY models/yolo11n.pt /app/models/yolo11n.pt
COPY backend /app/backend

# Create storage directories
RUN mkdir -p /app/backend/storage/uploads /app/backend/storage/outputs

EXPOSE 8000

# Run FastAPI backend with Uvicorn
CMD exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
