#!/bin/bash

# Face Recognition Pipeline - Comprehensive Health Check Script
# Usage: ./monitoring-scripts/health-check.sh

echo "🔍 Face Recognition Pipeline Health Check"
echo "========================================"
echo "📅 $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check Docker containers
echo -e "\n📦 Container Status:"
echo "==================="
containers=$(docker ps --filter "name=face-recognition-pipeline" --format "{{.Names}}" 2>/dev/null)
if [ $? -eq 0 ] && [ -n "$containers" ]; then
    docker ps --filter "name=face-recognition-pipeline" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -10
    container_count=$(echo "$containers" | wc -l)
    print_info "Found $container_count face recognition containers running"
else
    print_status 1 "No face recognition containers found"
fi

# Check HTTP endpoints
echo -e "\n🌐 HTTP Endpoints:"
echo "=================="

# Main application
main_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost 2>/dev/null)
if [ "$main_status" = "200" ]; then
    print_status 0 "Main Application (http://localhost) - $main_status"
elif [ "$main_status" = "302" ]; then
    print_status 0 "Main Application (http://localhost) - $main_status (redirect - normal)"
else
    print_status 1 "Main Application (http://localhost) - $main_status"
fi

# Grafana
grafana_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null)
if [ "$grafana_status" = "200" ] || [ "$grafana_status" = "302" ]; then
    print_status 0 "Grafana (http://localhost:3000) - $grafana_status"
else
    print_status 1 "Grafana (http://localhost:3000) - $grafana_status"
fi

# Prometheus (use GET method)
prometheus_status=$(curl -s http://localhost:9090 >/dev/null 2>&1 && echo "OK" || echo "FAILED")
if [ "$prometheus_status" = "OK" ]; then
    print_status 0 "Prometheus (http://localhost:9090) - $prometheus_status"
else
    print_status 1 "Prometheus (http://localhost:9090) - $prometheus_status"
fi

# Kibana
kibana_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5601 2>/dev/null)
if [ "$kibana_status" = "200" ] || [ "$kibana_status" = "302" ]; then
    print_status 0 "Kibana (http://localhost:5601) - $kibana_status"
else
    print_status 1 "Kibana (http://localhost:5601) - $kibana_status"
fi

# Flower
flower_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/flower 2>/dev/null)
if [ "$flower_status" = "200" ] || [ "$flower_status" = "302" ]; then
    print_status 0 "Flower (http://localhost/flower) - $flower_status"
else
    print_status 1 "Flower (http://localhost/flower) - $flower_status"
fi

# Check database
echo -e "\n💾 Database Status:"
echo "=================="
db_status=$(docker exec face-recognition-pipeline-postgres-1 pg_isready -U facerecog 2>/dev/null)
if [ $? -eq 0 ]; then
    print_status 0 "PostgreSQL - Running and accepting connections"
    
    # Get database statistics
    echo -e "\n📊 Database Statistics:"
    docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -t -c "
    SELECT 'Total files uploaded: ' || COUNT(*) FROM uploaded_files;
    SELECT 'Files processed: ' || COUNT(*) FROM uploaded_files WHERE processing_status = 'completed';
    SELECT 'Files pending: ' || COUNT(*) FROM uploaded_files WHERE processing_status = 'pending';
    SELECT 'Total faces detected: ' || COUNT(*) FROM faces;
    " 2>/dev/null | grep -v "^$" | sed 's/^/  /'
else
    print_status 1 "PostgreSQL - Not responding"
fi

# Check Redis
echo -e "\n🔴 Redis Status:"
echo "==============="
redis_status=$(docker exec face-recognition-pipeline-redis-1 redis-cli ping 2>/dev/null)
if [ "$redis_status" = "PONG" ]; then
    print_status 0 "Redis - Running and responding"
    
    # Check queue length
    queue_length=$(docker exec face-recognition-pipeline-redis-1 redis-cli llen celery 2>/dev/null)
    if [ $? -eq 0 ]; then
        print_info "Celery queue length: $queue_length tasks"
    fi
else
    print_status 1 "Redis - Not responding"
fi

# Check system resources
echo -e "\n💻 System Resources:"
echo "==================="

# Disk usage
disk_usage=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$disk_usage" -lt 80 ]; then
    print_status 0 "Disk usage: ${disk_usage}% ($(df -h / | tail -1 | awk '{print $3 " used of " $2}'))"
elif [ "$disk_usage" -lt 90 ]; then
    print_warning "Disk usage: ${disk_usage}% - Consider cleaning up"
else
    print_status 1 "Disk usage: ${disk_usage}% - Critical! Clean up needed"
fi

# Memory usage (if available)
if command -v free >/dev/null 2>&1; then
    memory_info=$(free -h | grep Mem)
    print_info "Memory: $(echo $memory_info | awk '{print $3 " used of " $2}')"
fi

# Docker system usage
echo -e "\n🐳 Docker Resources:"
docker_size=$(docker system df --format "table {{.Type}}\t{{.TotalCount}}\t{{.Size}}" 2>/dev/null | tail -n +2)
if [ $? -eq 0 ]; then
    echo "$docker_size" | sed 's/^/  /'
fi

# Check recent errors
echo -e "\n🚨 Recent Errors (last 1 hour):"
echo "================================"
recent_errors=$(docker-compose logs --since=1h 2>/dev/null | grep -i error | tail -5)
if [ -n "$recent_errors" ]; then
    echo "$recent_errors" | sed 's/^/  /'
else
    print_status 0 "No recent errors found"
fi

# File processing status
echo -e "\n📁 File Processing:"
echo "=================="
watch_files=$(find data/watch/ -type f 2>/dev/null | wc -l)
processed_files=$(find data/processed/ -type f -name "*.jpg" 2>/dev/null | wc -l)
embedding_files=$(find data/embeddings/ -type f -name "*.npy" 2>/dev/null | wc -l)

print_info "Files in watch folder: $watch_files"
print_info "Processed face images: $processed_files"
print_info "Embedding files: $embedding_files"

# Summary
echo -e "\n📋 Health Check Summary:"
echo "========================"
current_time=$(date)
print_info "Health check completed at: $current_time"

# Create logs directory if it doesn't exist
mkdir -p logs

# Save summary to log file
{
    echo "Health Check Summary - $current_time"
    echo "Containers: $(echo "$containers" | wc -l)"
    echo "Main App Status: $main_status"
    echo "Database: $([ "$db_status" ] && echo "OK" || echo "ERROR")"
    echo "Redis: $([ "$redis_status" = "PONG" ] && echo "OK" || echo "ERROR")"
    echo "Disk Usage: ${disk_usage}%"
    echo "Watch Files: $watch_files"
    echo "Processed Files: $processed_files"
} >> logs/health-summary.log

echo -e "\n💡 For detailed monitoring, run:"
echo "  ./monitoring-scripts/check-database.sh     - Database details"
echo "  ./monitoring-scripts/monitor-services.sh   - Service monitoring"
echo "  ./monitoring-scripts/check-file-processing.sh - File processing status"
echo ""
echo "✅ Health check complete! Summary saved to logs/health-summary.log"
