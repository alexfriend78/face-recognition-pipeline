#!/bin/bash

# Celery Worker Scaling Script for Face Recognition Pipeline
# Usage: ./scripts/scale_workers.sh [scale|status|restart] [worker_count]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

function show_usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  scale <count>     Scale Celery workers to specified count (1-10)"
    echo "  status           Show current worker status"
    echo "  restart          Restart all Celery workers"
    echo "  stop             Stop all Celery workers"
    echo "  start            Start Celery workers with default configuration"
    echo ""
    echo "Examples:"
    echo "  $0 scale 4       # Run 4 Celery worker containers"
    echo "  $0 status        # Show current worker status"
    echo "  $0 restart       # Restart all workers"
    echo ""
}

function check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
        echo "Error: Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
    
    if ! docker-compose --version &> /dev/null; then
        # Try docker compose (newer syntax)
        if ! docker compose version &> /dev/null; then
            echo "Error: Docker Compose not working properly."
            exit 1
        fi
        DOCKER_COMPOSE_CMD="docker compose"
    else
        DOCKER_COMPOSE_CMD="docker-compose"
    fi
}

function scale_workers() {
    local worker_count=$1
    
    if [[ ! "$worker_count" =~ ^[1-9][0-9]?$ ]] || [ "$worker_count" -gt 10 ]; then
        echo "Error: Worker count must be between 1 and 10"
        exit 1
    fi
    
    echo "Scaling Celery workers to $worker_count containers..."
    echo "Each worker will run with 4 concurrent threads."
    echo "Total processing capacity: $((worker_count * 4)) concurrent tasks"
    echo ""
    
    $DOCKER_COMPOSE_CMD up -d --scale celery=$worker_count
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully scaled to $worker_count Celery workers"
        echo ""
        show_worker_status
    else
        echo "❌ Failed to scale workers"
        exit 1
    fi
}

function show_worker_status() {
    echo "=== Celery Worker Status ==="
    echo ""
    
    # Show running containers
    echo "📦 Running Celery Containers:"
    $DOCKER_COMPOSE_CMD ps celery
    echo ""
    
    # Show worker statistics via Flower (if available)
    echo "🌸 Worker Statistics (via Flower):"
    if curl -s http://localhost/flower/api/workers >/dev/null 2>&1; then
        curl -s http://localhost/flower/api/workers | python3 -m json.tool 2>/dev/null || echo "Flower API not accessible"
    else
        echo "Flower monitoring not accessible at http://localhost/flower"
        echo "Start the full stack with: docker-compose up -d"
    fi
    echo ""
    
    # Show Redis queue status
    echo "📊 Redis Queue Status:"
    if $DOCKER_COMPOSE_CMD exec -T redis redis-cli llen celery >/dev/null 2>&1; then
        QUEUE_LENGTH=$($DOCKER_COMPOSE_CMD exec -T redis redis-cli llen celery)
        echo "Pending tasks in queue: $QUEUE_LENGTH"
    else
        echo "Redis not accessible - start services first"
    fi
}

function restart_workers() {
    echo "Restarting all Celery workers..."
    $DOCKER_COMPOSE_CMD restart celery
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully restarted Celery workers"
        echo ""
        show_worker_status
    else
        echo "❌ Failed to restart workers"
        exit 1
    fi
}

function stop_workers() {
    echo "Stopping all Celery workers..."
    $DOCKER_COMPOSE_CMD stop celery
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully stopped Celery workers"
    else
        echo "❌ Failed to stop workers"
        exit 1
    fi
}

function start_workers() {
    echo "Starting Celery workers with default configuration..."
    $DOCKER_COMPOSE_CMD up -d celery
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully started Celery workers"
        echo ""
        show_worker_status
    else
        echo "❌ Failed to start workers"
        exit 1
    fi
}

# Main script logic
check_docker_compose

case "${1:-}" in
    "scale")
        if [ -z "${2:-}" ]; then
            echo "Error: Please specify worker count"
            echo "Usage: $0 scale <count>"
            exit 1
        fi
        scale_workers "$2"
        ;;
    "status")
        show_worker_status
        ;;
    "restart")
        restart_workers
        ;;
    "stop")
        stop_workers
        ;;
    "start")
        start_workers
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    "")
        echo "Error: No command specified"
        echo ""
        show_usage
        exit 1
        ;;
    *)
        echo "Error: Unknown command '$1'"
        echo ""
        show_usage
        exit 1
        ;;
esac

