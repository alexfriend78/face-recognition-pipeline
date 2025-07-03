#!/bin/bash

# Face Recognition Pipeline - Service Monitor Script
# Usage: ./monitoring-scripts/monitor-services.sh

echo "🔧 Face Recognition Service Monitor"
echo "==================================="
echo "📅 $(date)"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check container resource usage
echo "📊 Container Resource Usage:"
echo "============================"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"

# Check service status
echo -e "\n🐳 Docker Compose Services:"
echo "============================"
docker-compose ps

# Check Redis health
echo -e "\n🔴 Redis Health Check:"
echo "======================="
redis_status=$(docker exec face-recognition-pipeline-redis-1 redis-cli ping 2>/dev/null)
if [ "$redis_status" = "PONG" ]; then
    print_success "Redis is responding"
    
    # Redis info
    echo "Redis info:"
    docker exec face-recognition-pipeline-redis-1 redis-cli info memory | grep -E "(used_memory_human|used_memory_peak_human)" | sed 's/^/  /'
    
    # Check queue lengths
    echo "Queue status:"
    celery_queue=$(docker exec face-recognition-pipeline-redis-1 redis-cli llen celery 2>/dev/null)
    print_info "Celery queue length: $celery_queue tasks"
    
    # Check connected clients
    connected_clients=$(docker exec face-recognition-pipeline-redis-1 redis-cli info clients | grep connected_clients | cut -d: -f2 | tr -d '\r')
    print_info "Connected clients: $connected_clients"
else
    print_error "Redis is not responding"
fi

# Check PostgreSQL health
echo -e "\n🐘 PostgreSQL Health Check:"
echo "============================"
db_status=$(docker exec face-recognition-pipeline-postgres-1 pg_isready -U facerecog 2>/dev/null)
if [ $? -eq 0 ]; then
    print_success "PostgreSQL is ready"
    
    # Connection count
    connections=$(docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -t -c "SELECT COUNT(*) FROM pg_stat_activity;" 2>/dev/null | xargs)
    print_info "Active connections: $connections"
    
    # Database size
    db_size=$(docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -t -c "SELECT pg_size_pretty(pg_database_size('face_recognition'));" 2>/dev/null | xargs)
    print_info "Database size: $db_size"
else
    print_error "PostgreSQL is not ready"
fi

# Check Celery workers
echo -e "\n🐝 Celery Worker Status:"
echo "========================"
print_info "Checking Celery worker logs (last 10 lines):"
docker-compose logs --tail=10 celery | sed 's/^/  /'

# Check for any worker errors
worker_errors=$(docker-compose logs --since=1h celery 2>/dev/null | grep -i error | wc -l)
if [ "$worker_errors" -gt 0 ]; then
    print_warning "Found $worker_errors error messages in Celery logs (last hour)"
    echo "Recent errors:"
    docker-compose logs --since=1h celery | grep -i error | tail -3 | sed 's/^/  /'
else
    print_success "No recent Celery errors found"
fi

# Check web application
echo -e "\n🌐 Web Application Status:"
echo "=========================="
web_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost 2>/dev/null)
if [ "$web_status" = "200" ]; then
    print_success "Web application is responding (HTTP $web_status)"
elif [ "$web_status" = "302" ]; then
    print_success "Web application is responding (HTTP $web_status - redirect)"
else
    print_error "Web application issue (HTTP $web_status)"
fi

# Check web logs for errors
web_errors=$(docker-compose logs --since=1h web 2>/dev/null | grep -i error | wc -l)
if [ "$web_errors" -gt 0 ]; then
    print_warning "Found $web_errors error messages in web logs (last hour)"
    echo "Recent errors:"
    docker-compose logs --since=1h web | grep -i error | tail -3 | sed 's/^/  /'
else
    print_success "No recent web application errors found"
fi

# Check monitoring services
echo -e "\n📈 Monitoring Services:"
echo "======================="

# Prometheus
prometheus_status=$(curl -s http://localhost:9090 >/dev/null 2>&1 && echo "OK" || echo "FAILED")
if [ "$prometheus_status" = "OK" ]; then
    print_success "Prometheus is responding"
else
    print_error "Prometheus is not responding"
fi

# Grafana
grafana_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null)
if [ "$grafana_status" = "200" ] || [ "$grafana_status" = "302" ]; then
    print_success "Grafana is responding (HTTP $grafana_status)"
else
    print_error "Grafana issue (HTTP $grafana_status)"
fi

# Kibana
kibana_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5601 2>/dev/null)
if [ "$kibana_status" = "200" ] || [ "$kibana_status" = "302" ]; then
    print_success "Kibana is responding (HTTP $kibana_status)"
else
    print_error "Kibana issue (HTTP $kibana_status)"
fi

# Check disk space
echo -e "\n💽 System Resources:"
echo "===================="
disk_usage=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
disk_info=$(df -h / | tail -1 | awk '{print $3 " used of " $2}')

if [ "$disk_usage" -lt 80 ]; then
    print_success "Disk usage: ${disk_usage}% ($disk_info)"
elif [ "$disk_usage" -lt 90 ]; then
    print_warning "Disk usage: ${disk_usage}% ($disk_info) - Consider cleanup"
else
    print_error "Disk usage: ${disk_usage}% ($disk_info) - Critical!"
fi

# Memory usage (if free command is available)
if command -v free >/dev/null 2>&1; then
    memory_info=$(free -h | grep Mem | awk '{print $3 " used of " $2 " (" $4 " available)"}')
    print_info "Memory: $memory_info"
fi

# Docker system resources
echo -e "\n🐳 Docker System Usage:"
echo "======================="
docker system df

# Service restart commands
echo -e "\n🔧 Quick Service Management:"
echo "============================"
echo "To restart services if needed:"
echo "  docker-compose restart web      # Restart web application"
echo "  docker-compose restart celery   # Restart background workers"
echo "  docker-compose restart postgres # Restart database"
echo "  docker-compose restart redis    # Restart cache/queue"
echo ""
echo "To view live logs:"
echo "  docker-compose logs -f web      # Follow web logs"
echo "  docker-compose logs -f celery   # Follow worker logs"
echo ""
echo "To scale workers:"
echo "  docker-compose up -d --scale celery=4  # Run 4 worker instances"

echo -e "\n✅ Service monitoring complete!"
