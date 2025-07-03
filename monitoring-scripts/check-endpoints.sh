#!/bin/bash

# Face Recognition Pipeline - Endpoint Checker Script
# Usage: ./monitoring-scripts/check-endpoints.sh

echo "🌐 Face Recognition Endpoint Health Check"
echo "========================================="
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

# Function to test HTTP endpoint
test_endpoint() {
    local url=$1
    local name=$2
    local expected_codes=$3  # Space-separated list of acceptable codes
    
    echo -n "Testing $name ($url)... "
    
    # Get HTTP status code
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    # Check if we got a response
    if [ -z "$status_code" ] || [ "$status_code" = "000" ]; then
        print_error "No response (connection failed)"
        return 1
    fi
    
    # Check if status code is acceptable
    for expected in $expected_codes; do
        if [ "$status_code" = "$expected" ]; then
            print_success "HTTP $status_code"
            return 0
        fi
    done
    
    # Status code not in expected list
    print_error "HTTP $status_code (unexpected)"
    return 1
}

# Function to test with GET method (for services that don't support HEAD)
test_endpoint_get() {
    local url=$1
    local name=$2
    
    echo -n "Testing $name ($url)... "
    
    # Use GET method and check if we get any response
    response=$(curl -s "$url" 2>/dev/null | head -c 100)
    
    if [ -n "$response" ]; then
        print_success "OK (responding)"
        return 0
    else
        print_error "No response"
        return 1
    fi
}

echo "🏠 Core Application Endpoints:"
echo "=============================="

# Main application
test_endpoint "http://localhost" "Main Application" "200 302"

# Application health/metrics (if available)
test_endpoint "http://localhost/metrics" "Application Metrics" "200"

# Flower (Celery monitoring)
test_endpoint "http://localhost/flower" "Flower (Celery Monitor)" "200 302"

echo -e "\n📊 Monitoring & Analytics:"
echo "=========================="

# Grafana
test_endpoint "http://localhost:3000" "Grafana Dashboard" "200 302"

# Prometheus (doesn't like HEAD requests, use GET)
test_endpoint_get "http://localhost:9090" "Prometheus Metrics"

# Kibana
test_endpoint "http://localhost:5601" "Kibana Logs" "200 302"

# AlertManager
test_endpoint "http://localhost:9093" "AlertManager" "200 302"

echo -e "\n🔍 Data & Infrastructure:"
echo "========================="

# Elasticsearch
test_endpoint "http://localhost:9200" "Elasticsearch" "200"

# Redis (HTTP interface not typically available, check via CLI)
echo -n "Testing Redis... "
if docker exec face-recognition-pipeline-redis-1 redis-cli ping >/dev/null 2>&1; then
    print_success "PONG (responding)"
else
    print_error "Not responding"
fi

# PostgreSQL (check via pg_isready)
echo -n "Testing PostgreSQL... "
if docker exec face-recognition-pipeline-postgres-1 pg_isready -U facerecog >/dev/null 2>&1; then
    print_success "Ready (accepting connections)"
else
    print_error "Not ready"
fi

echo -e "\n📈 System Metrics:"
echo "=================="

# Node Exporter
test_endpoint "http://localhost:9100" "Node Exporter" "200"

# cAdvisor
test_endpoint "http://localhost:8080" "cAdvisor (Container Metrics)" "200"

# Redis Exporter
test_endpoint "http://localhost:9121" "Redis Exporter" "200"

# Postgres Exporter
test_endpoint "http://localhost:9187" "Postgres Exporter" "200"

# Additional monitoring services
echo -e "\n🔧 Additional Services:"
echo "======================="

# Logstash
test_endpoint "http://localhost:9600" "Logstash API" "200"

# Check if services are accessible externally (if running on server)
echo -e "\n🌍 External Access Check:"
echo "========================="

# Get the server's IP address
server_ip=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
if [ "$server_ip" != "localhost" ] && [ -n "$server_ip" ]; then
    print_info "Server IP: $server_ip"
    
    # Test main application from external IP
    test_endpoint "http://$server_ip" "Main App (External)" "200 302"
    test_endpoint "http://$server_ip:3000" "Grafana (External)" "200 302"
else
    print_info "Running on localhost or IP detection failed"
fi

# API endpoint tests
echo -e "\n🔌 API Endpoints:"
echo "================="

# Test specific API endpoints if available
echo -n "Testing Upload API... "
upload_response=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost/upload 2>/dev/null)
if [ "$upload_response" = "400" ] || [ "$upload_response" = "422" ]; then
    print_success "Available (HTTP $upload_response - expected without file)"
elif [ "$upload_response" = "200" ]; then
    print_success "Available (HTTP $upload_response)"
else
    print_warning "HTTP $upload_response (may not be available)"
fi

# Test metrics endpoint specifically
echo -n "Testing Prometheus metrics endpoint... "
metrics_content=$(curl -s http://localhost/metrics 2>/dev/null | head -1)
if echo "$metrics_content" | grep -q "^#"; then
    print_success "Prometheus metrics available"
else
    print_warning "Metrics may not be properly formatted"
fi

# Response time check
echo -e "\n⏱️  Response Time Check:"
echo "======================="

endpoints=(
    "http://localhost"
    "http://localhost:3000"
    "http://localhost:9090"
)

for endpoint in "${endpoints[@]}"; do
    echo -n "Response time for $endpoint... "
    response_time=$(curl -s -o /dev/null -w "%{time_total}" "$endpoint" 2>/dev/null)
    if [ -n "$response_time" ]; then
        # Convert to milliseconds for easier reading
        response_ms=$(echo "$response_time * 1000" | bc 2>/dev/null || echo "unknown")
        if [ "$response_ms" != "unknown" ]; then
            printf "%.0f ms\n" "$response_ms"
        else
            echo "$response_time seconds"
        fi
    else
        echo "Failed to measure"
    fi
done

# Summary
echo -e "\n📋 Endpoint Summary:"
echo "===================="

# Count successful endpoints
successful=0
total=10

# Quick test count
for url in "http://localhost" "http://localhost:3000" "http://localhost:9090" "http://localhost:5601" "http://localhost:9093"; do
    if curl -s -o /dev/null "$url" 2>/dev/null; then
        ((successful++))
    fi
done

print_info "HTTP endpoints responding: $successful/$total"

if [ $successful -ge 8 ]; then
    print_success "Most services are healthy"
elif [ $successful -ge 5 ]; then
    print_warning "Some services may have issues"
else
    print_error "Multiple services are not responding"
fi

echo -e "\n💡 Troubleshooting Tips:"
echo "======================="
echo "If endpoints are not responding:"
echo "  1. Check container status: docker-compose ps"
echo "  2. Check service logs: docker-compose logs [service-name]"
echo "  3. Restart specific service: docker-compose restart [service-name]"
echo "  4. Check firewall settings if accessing remotely"
echo ""
echo "Status code meanings:"
echo "  200: ✅ Service working perfectly"
echo "  302: ✅ Service working (redirect to login/setup)"
echo "  405: ⚠️  Service running but method not allowed (try browser)"
echo "  404: ❌ Service not configured or endpoint missing"
echo "  000: ❌ Service not running or unreachable"

echo -e "\n✅ Endpoint check complete!"
