#!/bin/bash

# Face Recognition Pipeline - Database Check Script
# Usage: ./monitoring-scripts/check-database.sh

echo "💾 Face Recognition Database Status"
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

# Check if database container is running
if ! docker exec face-recognition-pipeline-postgres-1 pg_isready -U facerecog >/dev/null 2>&1; then
    print_error "Database container is not running or not responding"
    echo "Try: docker-compose restart postgres"
    exit 1
fi

print_success "Database connection established"

# Database size and basic info
echo -e "\n📊 Database Information:"
echo "========================"
docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -c "
SELECT 
    pg_database.datname AS database_name,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database 
WHERE datname = 'face_recognition';
"

# Table statistics
echo -e "\n📋 Table Statistics:"
echo "===================="
docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -c "
SELECT 
    schemaname,
    tablename,
    n_tup_ins AS inserts,
    n_tup_upd AS updates,
    n_tup_del AS deletes,
    n_live_tup AS live_rows
FROM pg_stat_user_tables
ORDER BY live_rows DESC;
"

# File upload statistics
echo -e "\n📁 File Upload Statistics:"
echo "=========================="
docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -c "
SELECT 
    'Total files uploaded: ' || COUNT(*) AS statistic
FROM uploaded_files
UNION ALL
SELECT 
    'Files completed: ' || COUNT(*)
FROM uploaded_files 
WHERE processing_status = 'completed'
UNION ALL
SELECT 
    'Files pending: ' || COUNT(*)
FROM uploaded_files 
WHERE processing_status = 'pending'
UNION ALL
SELECT 
    'Files failed: ' || COUNT(*)
FROM uploaded_files 
WHERE processing_status = 'failed'
UNION ALL
SELECT 
    'Files in progress: ' || COUNT(*)
FROM uploaded_files 
WHERE processing_status = 'processing';
"

# File type breakdown
echo -e "\n🎬 File Type Breakdown:"
echo "======================="
docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -c "
SELECT 
    file_type,
    processing_status,
    COUNT(*) as count
FROM uploaded_files 
GROUP BY file_type, processing_status
ORDER BY file_type, processing_status;
"

# Face detection statistics
echo -e "\n👤 Face Detection Statistics:"
echo "============================="
docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -c "
SELECT 
    'Total faces detected: ' || COUNT(*) AS statistic
FROM faces
UNION ALL
SELECT 
    'Average confidence: ' || ROUND(AVG(confidence), 3)
FROM faces
UNION ALL
SELECT 
    'Files with faces: ' || COUNT(DISTINCT uploaded_file_id)
FROM faces;
"

# Recent uploads
echo -e "\n📅 Recent Uploads (Last 10):"
echo "============================="
docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -c "
SELECT 
    id,
    original_filename,
    file_type,
    processing_status,
    upload_date
FROM uploaded_files 
ORDER BY upload_date DESC 
LIMIT 10;
"

# Top files by face count
echo -e "\n🏆 Top Files by Face Count:"
echo "==========================="
docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -c "
SELECT 
    uf.original_filename,
    COUNT(f.id) as face_count,
    ROUND(AVG(f.confidence), 3) as avg_confidence,
    uf.processing_status
FROM uploaded_files uf
LEFT JOIN faces f ON uf.id = f.uploaded_file_id
WHERE uf.processing_status = 'completed'
GROUP BY uf.id, uf.original_filename, uf.processing_status
HAVING COUNT(f.id) > 0
ORDER BY face_count DESC
LIMIT 10;
"

# Processing time statistics
echo -e "\n⏱️  Processing Performance:"
echo "=========================="
docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -c "
SELECT 
    file_type,
    processing_status,
    COUNT(*) as files,
    AVG(EXTRACT(EPOCH FROM (completed_at - upload_date))) as avg_processing_time_seconds
FROM uploaded_files 
WHERE completed_at IS NOT NULL
GROUP BY file_type, processing_status
ORDER BY file_type, processing_status;
"

# Database connections
echo -e "\n🔗 Active Database Connections:"
echo "==============================="
docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -c "
SELECT 
    datname as database,
    usename as username,
    application_name,
    client_addr,
    state,
    query_start
FROM pg_stat_activity 
WHERE datname = 'face_recognition'
ORDER BY query_start DESC;
"

# Check for potential issues
echo -e "\n🔍 Potential Issues Check:"
echo "========================="

# Check for failed uploads
failed_count=$(docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -t -c "SELECT COUNT(*) FROM uploaded_files WHERE processing_status = 'failed';" 2>/dev/null | xargs)

if [ "$failed_count" -gt 0 ]; then
    print_warning "$failed_count files have failed processing"
    echo "Recent failed files:"
    docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -c "
    SELECT original_filename, upload_date, error_message 
    FROM uploaded_files 
    WHERE processing_status = 'failed' 
    ORDER BY upload_date DESC 
    LIMIT 5;
    "
else
    print_success "No failed file processing found"
fi

# Check for stuck processing
stuck_count=$(docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -t -c "SELECT COUNT(*) FROM uploaded_files WHERE processing_status = 'processing' AND upload_date < NOW() - INTERVAL '1 hour';" 2>/dev/null | xargs)

if [ "$stuck_count" -gt 0 ]; then
    print_warning "$stuck_count files appear to be stuck in processing (>1 hour)"
    docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -c "
    SELECT original_filename, upload_date 
    FROM uploaded_files 
    WHERE processing_status = 'processing' AND upload_date < NOW() - INTERVAL '1 hour'
    ORDER BY upload_date DESC;
    "
else
    print_success "No stuck processing files found"
fi

# Database backup recommendation
echo -e "\n💾 Database Backup Information:"
echo "==============================="
db_size=$(docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -t -c "SELECT pg_size_pretty(pg_database_size('face_recognition'));" 2>/dev/null | xargs)
print_info "Current database size: $db_size"
print_info "To backup database: docker exec face-recognition-pipeline-postgres-1 pg_dump -U facerecog face_recognition > backup_\$(date +%Y%m%d).sql"

echo -e "\n✅ Database check complete!"
