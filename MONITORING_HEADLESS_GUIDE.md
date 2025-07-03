# Face Recognition Pipeline - Headless Server Monitoring Guide

This guide provides comprehensive monitoring tools and scripts for checking your face recognition pipeline running on a headless server.

## 📁 Quick Access Scripts

All monitoring scripts are located in the `monitoring-scripts/` folder:

```bash
# Make all scripts executable (run once)
chmod +x monitoring-scripts/*.sh

# Quick health check
./monitoring-scripts/health-check.sh

# Check app status
./monitoring-scripts/check-app-status.sh

# Check database content
./monitoring-scripts/check-database.sh

# Monitor services
./monitoring-scripts/monitor-services.sh

# Check file processing
./monitoring-scripts/check-file-processing.sh
```

---

## 🔍 1. Check if App is Running

### Quick Status Check
```bash
# Run the comprehensive health check script
./monitoring-scripts/health-check.sh
```

### Manual Commands
```bash
# Check Docker containers
docker ps --filter "name=face-recognition-pipeline" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check Docker Compose services
docker-compose ps

# Test main application
curl -s -o /dev/null -w "%{http_code}" http://localhost
```

---

## 🌐 2. Test HTTP Endpoints

### Automated Endpoint Testing
```bash
# Run endpoint checker script
./monitoring-scripts/check-endpoints.sh
```

### Manual Testing
```bash
# Main application (should return 200)
curl -s -o /dev/null -w "Main App: %{http_code}\n" http://localhost

# Grafana (may return 302 redirect - normal)
curl -s -o /dev/null -w "Grafana: %{http_code}\n" http://localhost:3000

# Prometheus (use GET instead of HEAD)
curl -s http://localhost:9090 > /dev/null && echo "Prometheus: OK" || echo "Prometheus: FAILED"

# Kibana (may return 302 redirect - normal)  
curl -s -o /dev/null -w "Kibana: %{http_code}\n" http://localhost:5601

# Flower (Celery Monitor)
curl -s -o /dev/null -w "Flower: %{http_code}\n" http://localhost/flower
```

### Understanding HTTP Status Codes
- **200**: ✅ Service is working perfectly
- **302**: ✅ Service is working (redirect to login/setup page)
- **405**: ✅ Service is running but doesn't support HEAD requests (use GET)
- **404**: ❌ Service not found or not configured
- **500**: ❌ Service error
- **Connection refused**: ❌ Service not running

---

## 💾 3. Check Database Content

### Quick Database Check
```bash
# Run database checker script
./monitoring-scripts/check-database.sh
```

### Manual Database Access
```bash
# Connect to PostgreSQL database
docker exec -it face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition

# Quick stats from command line
docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -c "
SELECT 'Total files: ' || COUNT(*) FROM uploaded_files;
SELECT 'Processed files: ' || COUNT(*) FROM uploaded_files WHERE processing_status = 'completed';
SELECT 'Total faces detected: ' || COUNT(*) FROM faces;
"
```

### Useful Database Queries
```sql
-- Check recent uploads
SELECT id, original_filename, file_type, processing_status, upload_date 
FROM uploaded_files 
ORDER BY upload_date DESC 
LIMIT 10;

-- Count files by status
SELECT processing_status, COUNT(*) as count
FROM uploaded_files 
GROUP BY processing_status;

-- Check face detection results
SELECT 
    uf.original_filename,
    COUNT(f.id) as face_count,
    AVG(f.confidence) as avg_confidence
FROM uploaded_files uf
LEFT JOIN faces f ON uf.id = f.uploaded_file_id
WHERE uf.processing_status = 'completed'
GROUP BY uf.id, uf.original_filename
ORDER BY face_count DESC
LIMIT 10;
```

---

## 🔧 4. Check Process Health

### Automated Process Monitoring
```bash
# Run service monitor script
./monitoring-scripts/monitor-services.sh
```

### Manual Health Checks
```bash
# Check container health and resource usage
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Check Celery workers (background processing)
docker-compose logs --tail=10 celery

# Check Redis (cache/queue)
docker exec face-recognition-pipeline-redis-1 redis-cli ping

# Check PostgreSQL
docker exec face-recognition-pipeline-postgres-1 pg_isready -U facerecog

# Check recent errors
docker-compose logs --since=1h | grep -i error
```

---

## 📁 5. Check File Processing

### Automated File Processing Check
```bash
# Run file processing monitor
./monitoring-scripts/check-file-processing.sh
```

### Manual File Processing Checks
```bash
# Check watch folder for new files
ls -la data/watch/

# Check processed files
find data/processed/ -type f -name "*.jpg" | wc -l

# Check embeddings
ls -la data/embeddings/

# Check processing queue
docker exec face-recognition-pipeline-redis-1 redis-cli llen celery

# Monitor real-time processing
docker-compose logs -f celery | grep -E "(Processing|Completed|Error)"
```

---

## 📊 6. System Resource Monitoring

### System Health Check
```bash
# Check disk usage
df -h

# Check memory usage
free -h

# Check CPU usage
top -bn1 | grep "Cpu(s)"

# Check Docker system usage
docker system df
```

---

## 🚨 7. Troubleshooting Common Issues

### Service Not Responding
```bash
# Restart specific service
docker-compose restart web

# Restart all services
docker-compose down && docker-compose up -d

# Check logs for errors
docker-compose logs web | tail -20
```

### Database Connection Issues
```bash
# Check database container
docker exec face-recognition-pipeline-postgres-1 pg_isready -U facerecog

# Check database logs
docker-compose logs postgres | tail -20
```

### High Resource Usage
```bash
# Check resource usage
docker stats --no-stream

# Check disk space
df -h

# Clean up Docker resources
docker system prune -f
```

---

## 📅 8. Regular Monitoring Schedule

### Daily Checks
```bash
# Run daily health check
./monitoring-scripts/health-check.sh > logs/health-$(date +%Y%m%d).log
```

### Weekly Checks
```bash
# Check database growth
./monitoring-scripts/check-database.sh

# Check file processing statistics
./monitoring-scripts/check-file-processing.sh
```

### Monthly Maintenance
```bash
# Clean up old logs
docker-compose logs --since=720h > logs/archive-$(date +%Y%m).log

# Check system resources
docker system df
df -h
```

---

## 🔗 Quick Reference Commands

```bash
# Essential one-liners
docker-compose ps                                              # Service status
curl -s -o /dev/null -w "%{http_code}" http://localhost       # App accessibility
docker-compose logs --tail=5 web                              # Recent web logs
docker exec face-recognition-pipeline-postgres-1 psql -U facerecog -d face_recognition -c "SELECT COUNT(*) FROM uploaded_files;" # File count
docker stats --no-stream | head -5                            # Resource usage
```

---

## 📞 Support

If you encounter issues:

1. **Run the health check script**: `./monitoring-scripts/health-check.sh`
2. **Check service logs**: `docker-compose logs [service-name]`
3. **Verify network connectivity**: Test endpoints with curl
4. **Check system resources**: Ensure adequate disk/memory
5. **Restart services if needed**: `docker-compose restart [service-name]`

---

**💡 Tip**: Bookmark this guide and keep the monitoring scripts handy for quick system checks!
