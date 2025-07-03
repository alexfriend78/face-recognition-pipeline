FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgl1-mesa-glx \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download InsightFace models
RUN mkdir -p /app/models
RUN python -c "from insightface.app import FaceAnalysis; app = FaceAnalysis(name='buffalo_l', root='/app/models'); app.prepare(ctx_id=-1)"

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/raw data/processed/faces data/embeddings

# Create prometheus multiproc directory
RUN mkdir -p /tmp/prometheus_multiproc

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]