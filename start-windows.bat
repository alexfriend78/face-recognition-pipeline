@echo off
REM Face Recognition Pipeline - Windows Startup Script
REM This script starts the face recognition pipeline on Windows using Docker Desktop

echo.
echo =================================================================
echo 🚀 Starting Face Recognition Pipeline with Complete Monitoring
echo =================================================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop and try again.
    echo.
    echo 💡 Steps to start Docker Desktop:
    echo 1. Open Docker Desktop from your Start menu
    echo 2. Wait for it to show "Docker Desktop is running"
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

echo ✅ Docker is running!
echo.

REM Create necessary directories
echo 📁 Creating monitoring directories...
mkdir monitoring\prometheus 2>nul
mkdir monitoring\grafana\provisioning\datasources 2>nul
mkdir monitoring\grafana\provisioning\dashboards 2>nul
mkdir monitoring\grafana\dashboards 2>nul
mkdir monitoring\alertmanager 2>nul
mkdir monitoring\logstash\config 2>nul
mkdir monitoring\logstash\pipeline 2>nul
mkdir monitoring\filebeat 2>nul
mkdir data\watch 2>nul
mkdir data\raw 2>nul
mkdir data\processed 2>nul
mkdir data\embeddings 2>nul

echo 🔧 Starting main application services...
docker-compose up -d

echo ⏳ Waiting for main services to be ready...
timeout /t 30 /nobreak >nul

echo 📊 Starting monitoring stack...
docker-compose -f docker-compose.monitoring.yml up -d

echo ⏳ Waiting for monitoring services to initialize...
timeout /t 60 /nobreak >nul

echo.
echo 🎉 Startup complete! Access your services:
echo ===========================================
echo 📱 Main Application:        http://localhost
echo 📊 Grafana Dashboards:      http://localhost:3000 (admin/admin123)
echo 🔥 Prometheus:              http://localhost:9090
echo 🚨 AlertManager:            http://localhost:9093
echo 📋 Kibana Logs:             http://localhost:5601
echo 🌺 Flower (Celery):         http://localhost/flower
echo 💾 Cache Dashboard:         http://localhost/cache
echo 📈 Metrics Endpoint:        http://localhost/metrics
echo.
echo 🏗️  Infrastructure Metrics:
echo ============================
echo 🖥️  Node Exporter:          http://localhost:9100
echo 🔴 Redis Exporter:          http://localhost:9121
echo 🐘 Postgres Exporter:       http://localhost:9187
echo.
echo 💡 Tips:
echo =======
echo 1. Drop files into .\data\watch\ for automatic processing
echo 2. Import Grafana dashboards from the monitoring\grafana\dashboards\ folder
echo 3. Configure alerting in AlertManager by editing monitoring\alertmanager\alertmanager.yml
echo 4. View logs in Kibana with pre-configured dashboards
echo.
echo 🛑 To stop all services: run stop-windows.bat
echo 📖 For more info, check the README.md file
echo.
pause
