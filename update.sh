#!/bin/bash
set -e

echo "🔄 Starting Face Recognition Pipeline Update..."

# Navigate to script directory
cd "$(dirname "$0")"

# Create backup
echo "📦 Creating backup..."
./backup.sh

# Stop services
echo "⏹️ Stopping services..."
docker-compose down

# Pull latest changes
echo "🔄 Pulling latest changes..."
git fetch origin
git pull origin main

# Rebuild images
echo "🏗️ Rebuilding images..."
docker-compose build --no-cache

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# Verify deployment
echo "✅ Verifying deployment..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Update completed successfully!"
    docker-compose ps
else
    echo "❌ Health check failed. Check logs:"
    docker-compose logs --tail=20
    exit 1
fi
