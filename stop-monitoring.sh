#!/bin/bash

# Face Recognition Pipeline - Stop Monitoring Stack Script

echo "🛑 Stopping Face Recognition Pipeline and Monitoring Stack"
echo "=========================================================="

echo "📊 Stopping monitoring services..."
docker-compose -f docker-compose.monitoring.yml down

echo "🔧 Stopping main application services..."
docker-compose down

echo "🧹 Cleaning up..."
# Optional: Remove volumes (uncomment if you want to clean up data)
# echo "⚠️  Removing all data volumes..."
# docker-compose -f docker-compose.monitoring.yml down -v
# docker-compose down -v

echo "✅ All services stopped successfully!"
echo ""
echo "💡 To start again: ./start-monitoring.sh"
echo "🗑️  To remove all data: docker-compose down -v && docker-compose -f docker-compose.monitoring.yml down -v"

