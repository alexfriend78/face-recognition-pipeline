#!/bin/bash

# Face Recognition Pipeline - File Processing Monitor Script
# Usage: ./monitoring-scripts/check-file-processing.sh

echo "📁 Face Recognition File Processing Monitor"
echo "=========================================="
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

# Check data directories
echo "📂 Data Directory Status:"
echo "========================="

# Watch folder
watch_count=$(find data/watch/ -type f 2>/dev/null | wc -l)
if [ "$watch_count" -gt 0 ]; then
    print_warning "Files in watch folder: $watch_count (waiting for processing)"
    echo "Recent files in watch folder:"
    find data/watch/ -type f -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -5 | while read timestamp filepath; do
        filename=$(basename "$filepath")
        filedate=$(date -d "@$timestamp" "+%Y-%m-%d %H:%M" 2>/dev/null || date -r "$timestamp" "+%Y-%m-%d %H:%M" 2>/dev/null || echo "unknown")
        echo "  $filename ($filedate)"
    done
else
    print_success "Watch folder is empty - no files waiting"
fi

# Raw folder
raw_count=$(find data/raw/ -type f 2>/dev/null | wc -l)
print_info "Files in raw folder: $raw_count"

# Processed faces
processed_count=$(find data/processed/faces/ -type f -name "*.jpg" 2>/dev/null | wc -l)
print_info "Processed face images: $processed_count"

# Embeddings
embedding_count=$(find data/embeddings/ -type f -name "*.npy" 2>/dev/null | wc -l)
print_info "Face embedding files: $embedding_count"

# Check folder sizes
echo -e "\n💾 Data Folder Sizes:"
echo "===================="
if [ -d "data" ]; then
    du -sh data/* 2>/dev/null | sort -hr | sed 's/^/  /'
else
    print_warning "Data directory not found"
fi

# Check processing queue
echo -e "\n🚦 Processing Queue Status:"
echo "=========================="
if docker exec face-recognition-pipeline-redis-1 redis-cli ping >/dev/null 2>&1; then
    celery_queue=$(docker exec face-recognition-pipeline-redis-1 redis-cli llen celery 2>/dev/null)
    if [ "$celery_queue" -gt 0 ]; then
        print_warning "Celery queue length: $celery_queue tasks pending"
    else
        print_success "Celery queue is empty"
    fi
    
    # Check active tasks
    active_tasks=$(docker exec face-recognition-pipeline-redis-1 redis-cli llen celery.active 2>/dev/null || echo "0")
    print_info "Active processing tasks: $active_tasks"
else
    print_error "Cannot connect to Redis queue"
fi

# Database processing status
echo -e "\n📊 Database Processing Statistics:"
echo "=================================="
if docker exec face-recognition-pipeline-postgres-1 pg_isready -U facerecog >/dev/null 2>&1; then
    # Get processing statistics
    docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -c "
    SELECT 
        processing_status,
        file_type,
        COUNT(*) as count
    FROM uploaded_files 
    GROUP BY processing_status, file_type
    ORDER BY processing_status, file_type;
    "
    
    # Recent processing activity
    echo -e "\n📈 Recent Processing Activity (Last 24 hours):"
    docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -c "
    SELECT 
        DATE_TRUNC('hour', upload_date) as hour,
        COUNT(*) as files_uploaded,
        SUM(CASE WHEN processing_status = 'completed' THEN 1 ELSE 0 END) as completed,
        SUM(CASE WHEN processing_status = 'failed' THEN 1 ELSE 0 END) as failed
    FROM uploaded_files 
    WHERE upload_date > NOW() - INTERVAL '24 hours'
    GROUP BY DATE_TRUNC('hour', upload_date)
    ORDER BY hour DESC
    LIMIT 10;
    "
else
    print_error "Cannot connect to database"
fi

# Check for stuck files
echo -e "\n⚠️  Potential Issues:"
echo "===================="

# Files stuck in processing
if docker exec face-recognition-pipeline-postgres-1 pg_isready -U facerecog >/dev/null 2>&1; then
    stuck_count=$(docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -t -c "SELECT COUNT(*) FROM uploaded_files WHERE processing_status = 'processing' AND upload_date < NOW() - INTERVAL '1 hour';" 2>/dev/null | xargs)
    
    if [ "$stuck_count" -gt 0 ]; then
        print_warning "$stuck_count files appear stuck in processing (>1 hour)"
        echo "Stuck files:"
        docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -c "
        SELECT 
            original_filename,
            upload_date,
            NOW() - upload_date as stuck_duration
        FROM uploaded_files 
        WHERE processing_status = 'processing' AND upload_date < NOW() - INTERVAL '1 hour'
        ORDER BY upload_date;
        "
    else
        print_success "No stuck processing files found"
    fi
    
    # Failed files
    failed_count=$(docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -t -c "SELECT COUNT(*) FROM uploaded_files WHERE processing_status = 'failed';" 2>/dev/null | xargs)
    
    if [ "$failed_count" -gt 0 ]; then
        print_warning "$failed_count files have failed processing"
        echo "Recent failed files:"
        docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -c "
        SELECT 
            original_filename,
            upload_date,
            error_message
        FROM uploaded_files 
        WHERE processing_status = 'failed'
        ORDER BY upload_date DESC
        LIMIT 5;
        "
    else
        print_success "No failed processing files found"
    fi
fi

# Check worker performance
echo -e "\n🐝 Worker Performance:"
echo "====================="
print_info "Recent worker activity (last 20 log lines):"
docker-compose logs --tail=20 celery | grep -E "(Processing|Completed|Failed|Error)" | sed 's/^/  /'

# Celery worker status
echo -e "\n📋 Celery Worker Information:"
echo "============================="
worker_count=$(docker ps --filter "name=celery" --format "{{.Names}}" | wc -l)
print_info "Active Celery workers: $worker_count"

if [ "$worker_count" -gt 0 ]; then
    echo "Worker containers:"
    docker ps --filter "name=celery" --format "table {{.Names}}\t{{.Status}}\t{{.RunningFor}}" | sed 's/^/  /'
else
    print_error "No Celery workers found!"
fi

# Processing recommendations
echo -e "\n💡 Processing Optimization Tips:"
echo "==============================="

# Calculate processing rate
if docker exec face-recognition-pipeline-postgres-1 pg_isready -U facerecog >/dev/null 2>&1; then
    recent_completed=$(docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -t -c "SELECT COUNT(*) FROM uploaded_files WHERE processing_status = 'completed' AND completed_at > NOW() - INTERVAL '1 hour';" 2>/dev/null | xargs)
    
    if [ "$recent_completed" -gt 0 ]; then
        print_info "Files processed in last hour: $recent_completed"
        print_info "Average processing rate: $(echo "scale=1; $recent_completed / 60" | bc 2>/dev/null || echo "~$(($recent_completed / 60))") files per minute"
    fi
fi

# Recommendations based on queue status
if [ "$celery_queue" -gt 10 ]; then
    echo "🚀 Consider scaling up workers: docker-compose up -d --scale celery=4"
elif [ "$celery_queue" -eq 0 ] && [ "$worker_count" -gt 2 ]; then
    echo "💰 Consider scaling down workers: docker-compose up -d --scale celery=2"
fi

if [ "$watch_count" -gt 0 ]; then
    echo "📂 Files in watch folder will be auto-processed by folder-monitor service"
fi

# Quick actions
echo -e "\n🛠️  Quick Actions:"
echo "=================="
echo "Monitor processing in real-time:"
echo "  docker-compose logs -f celery"
echo ""
echo "Process files in watch folder manually:"
echo "  docker-compose restart folder-monitor"
echo ""
echo "Clear failed files (if needed):"
echo "  # Connect to database and update status if recoverable"
echo ""
echo "Scale workers up/down:"
echo "  docker-compose up -d --scale celery=4  # Scale up to 4 workers"
echo "  docker-compose up -d --scale celery=2  # Scale down to 2 workers"

echo -e "\n✅ File processing check complete!"
