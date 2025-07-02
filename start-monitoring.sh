#!/bin/bash

# Face Recognition Pipeline - Complete Monitoring Stack Startup Script
# This script starts the main application and the complete monitoring stack

set -e

echo "🚀 Starting Face Recognition Pipeline with Complete Monitoring Stack"
echo "=================================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create necessary directories
echo "📁 Creating monitoring directories..."
mkdir -p monitoring/{prometheus,grafana/{provisioning/datasources,provisioning/dashboards,dashboards},alertmanager,logstash/{config,pipeline},filebeat}
mkdir -p data/{watch,raw,processed,embeddings}

# Set proper permissions for data directories
chmod -R 755 data/

echo "🔧 Starting main application services..."
# Start the main application first
docker-compose up -d

echo "⏳ Waiting for main services to be ready..."
sleep 30

echo "📊 Starting monitoring stack..."
# Start the monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

echo "⏳ Waiting for monitoring services to initialize..."
sleep 60

echo "🔍 Checking service status..."

# Check if services are running
services=(
    "nginx"
    "postgres" 
    "redis"
    "web"
    "celery"
    "flower"
    "folder-monitor"
    "prometheus"
    "grafana"
    "alertmanager"
    "elasticsearch"
    "logstash"
    "kibana"
    "filebeat"
)

echo "Service Status:"
echo "==============="
for service in "${services[@]}"; do
    if docker ps --format "{{.Names}}" | grep -q "${service}"; then
        echo "✅ $service - Running"
    else
        echo "❌ $service - Not running"
    fi
done

echo ""
echo "🎉 Startup complete! Access your services:"
echo "==========================================="
echo "📱 Main Application:        http://localhost"
echo "📊 Grafana Dashboards:      http://localhost:3000 (admin/admin123)"
echo "🔥 Prometheus:              http://localhost:9090"
echo "🚨 AlertManager:            http://localhost:9093"
echo "📋 Kibana Logs:             http://localhost:5601"
echo "🌺 Flower (Celery):         http://localhost/flower"
echo "💾 Cache Dashboard:         http://localhost/cache"
echo "📈 Metrics Endpoint:        http://localhost/metrics"
echo ""
echo "🏗️  Infrastructure Metrics:"
echo "============================"
echo "🖥️  Node Exporter:          http://localhost:9100"
echo "🔴 Redis Exporter:          http://localhost:9121"
echo "🐘 Postgres Exporter:       http://localhost:9187"
echo ""
echo "💡 Tips:"
echo "======="
echo "1. Drop files into ./data/watch/ for automatic processing"
echo "2. Import Grafana dashboards from the monitoring/grafana/dashboards/ folder"
echo "3. Configure alerting in AlertManager by editing monitoring/alertmanager/alertmanager.yml"
echo "4. View logs in Kibana with pre-configured dashboards"
echo ""
echo "🛑 To stop all services: ./stop-monitoring.sh"
echo "📖 For more info, check the README.md file"

