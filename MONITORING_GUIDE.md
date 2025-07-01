# 📊 Complete Monitoring & Observability Guide

This guide covers the complete monitoring and observability stack for the Face Recognition Pipeline, including Prometheus, Grafana, AlertManager, and ELK stack.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Application    │───▶│   Prometheus    │───▶│    Grafana      │
│   (Metrics)     │    │  (Collection)   │    │ (Visualization) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        
                                ▼                        
                       ┌─────────────────┐               
                       │  AlertManager   │               
                       │   (Alerting)    │               
                       └─────────────────┘               

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Application    │───▶│    Logstash     │───▶│ Elasticsearch   │
│    (Logs)       │    │  (Processing)   │    │   (Storage)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                              │
         ▼                                              ▼
┌─────────────────┐                            ┌─────────────────┐
│    Filebeat     │                            │     Kibana      │
│ (Log Shipping)  │                            │ (Log Analysis)  │
└─────────────────┘                            └─────────────────┘
```

## 🚀 Quick Start

### 1. Start Everything
```bash
# Make scripts executable (first time only)
chmod +x start-monitoring.sh stop-monitoring.sh

# Start the complete stack
./start-monitoring.sh
```

### 2. Access Services
- **Main App**: http://localhost
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093
- **Kibana**: http://localhost:5601
- **Flower**: http://localhost/flower

### 3. Stop Everything
```bash
./stop-monitoring.sh
```

## 📊 Metrics Collection (Prometheus)

### Application Metrics
The Face Recognition Pipeline exposes comprehensive metrics at `/metrics`:

#### File Processing Metrics
- `face_recognition_files_uploaded_total` - File upload counter
- `face_recognition_files_processed_total{status}` - Processing results
- `face_recognition_file_processing_duration_seconds` - Processing time

#### Face Detection Metrics
- `face_recognition_faces_detected_total` - Number of faces found
- `face_recognition_face_quality_score` - Quality distribution
- `face_recognition_face_detection_duration_seconds` - Detection time

#### Search & Cache Metrics
- `face_recognition_searches_total{cache_status}` - Search operations
- `face_recognition_search_duration_seconds` - Search performance
- `face_recognition_cache_hit_ratio` - Cache efficiency

#### System Metrics
- `face_recognition_memory_usage_bytes{type}` - Memory consumption
- `face_recognition_gpu_utilization_percent` - GPU usage
- `face_recognition_http_requests_total` - HTTP request counts

### Infrastructure Metrics

#### Node Exporter (System Metrics)
- CPU usage, memory, disk, network
- Available at: http://localhost:9100

#### Redis Exporter
- Redis performance and memory metrics
- Available at: http://localhost:9121

#### Postgres Exporter
- Database connections, query performance
- Available at: http://localhost:9187

#### cAdvisor (Container Metrics)
- Docker container resource usage
- Available at: http://localhost:8080

## 📈 Visualization (Grafana)

### Pre-built Dashboards

#### Face Recognition Overview Dashboard
Located: `monitoring/grafana/dashboards/face-recognition-overview.json`

**Panels Include:**
- File processing rates
- Processing duration percentiles
- Cache hit ratio
- Memory usage
- GPU utilization
- Total faces detected

### Creating Custom Dashboards

1. **Access Grafana**: http://localhost:3000
2. **Login**: admin/admin123
3. **Create Dashboard**: Click "+" → Dashboard
4. **Add Panel**: Click "Add Panel"
5. **Configure Query**: Use PromQL queries

**Example Queries:**
```promql
# File processing rate
rate(face_recognition_files_processed_total[5m])

# Average processing time
avg(rate(face_recognition_file_processing_duration_seconds_sum[5m]) / rate(face_recognition_file_processing_duration_seconds_count[5m]))

# Error rate
rate(face_recognition_files_processed_total{status="failed"}[5m]) / rate(face_recognition_files_processed_total[5m])
```

### Dashboard Management

#### Import Dashboard
1. Go to "+" → Import
2. Upload JSON file or paste dashboard ID
3. Configure data source (Prometheus)

#### Export Dashboard
1. Go to Dashboard Settings (⚙️)
2. Click "JSON Model"
3. Copy and save the JSON

## 🚨 Alerting (AlertManager)

### Alert Rules
Configured in: `monitoring/prometheus/alerts.yml`

#### Application Alerts
- **HighFileProcessingErrorRate**: Error rate > 10%
- **LongFileProcessingTime**: Processing > 5 minutes
- **LowCacheHitRate**: Cache hit rate < 70%
- **HighMemoryUsage**: Memory > 2GB
- **NoFileUploads**: No uploads for 1 hour

#### Infrastructure Alerts
- **HighCPUUsage**: CPU > 80%
- **HighDiskUsage**: Disk > 80%
- **PostgreSQLDown**: Database unavailable
- **RedisDown**: Cache unavailable

### Alert Channels
Configured in: `monitoring/alertmanager/alertmanager.yml`

#### Email Notifications
```yaml
email_configs:
  - to: 'admin@example.com'
    subject: '[ALERT] Face Recognition System'
    body: |
      Alert: {{ .GroupLabels.alertname }}
      Description: {{ .Annotations.description }}
```

#### Slack Integration
```yaml
slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#alerts'
    title: 'Face Recognition Alert'
```

#### Webhook Integration
```yaml
webhook_configs:
  - url: 'http://your-webhook-endpoint'
    send_resolved: true
```

### Testing Alerts

#### Create Test Alert
```bash
# Trigger high CPU alert
docker run --rm -it busybox sh -c "while true; do :; done"
```

#### View Active Alerts
- **Prometheus**: http://localhost:9090/alerts
- **AlertManager**: http://localhost:9093

## 📋 Log Aggregation (ELK Stack)

### Log Flow
1. **Application** → Structured JSON logs
2. **Filebeat** → Collects Docker container logs
3. **Logstash** → Processes and enriches logs
4. **Elasticsearch** → Stores processed logs
5. **Kibana** → Provides search and visualization

### Log Types

#### Application Logs
- **Request logs**: HTTP requests with timing
- **Task logs**: Celery task execution
- **Error logs**: Exceptions and failures
- **Performance logs**: Processing times

#### Infrastructure Logs
- **Nginx**: Access and error logs
- **PostgreSQL**: Database logs
- **Redis**: Cache operation logs

### Log Fields
Automatically extracted fields:
- `service_name`: Source service
- `log_level`: Log severity
- `request_id`: Request correlation
- `task_id`: Celery task ID
- `duration_seconds`: Operation timing
- `operation`: Operation type

### Kibana Dashboards

#### Index Patterns
- `face-recognition-logs-*`: Application logs
- `filebeat-*`: Infrastructure logs

#### Discover
1. **Access Kibana**: http://localhost:5601
2. **Go to Discover**: Sidebar → Analytics → Discover
3. **Select Index**: face-recognition-logs-*
4. **Add Filters**: service_name, log_level, etc.

#### Visualizations
- **Error Rate**: Count of ERROR level logs
- **Response Times**: Average duration_seconds
- **Request Volume**: Count by timestamp
- **Service Health**: Log counts by service_name

## 🔧 Configuration

### Prometheus Configuration
File: `monitoring/prometheus/prometheus.yml`

#### Adding New Targets
```yaml
scrape_configs:
  - job_name: 'my-service'
    static_configs:
      - targets: ['my-service:8080']
    scrape_interval: 15s
```

### Grafana Configuration
Directory: `monitoring/grafana/provisioning/`

#### Adding Data Sources
File: `datasources/prometheus.yml`
```yaml
datasources:
  - name: MyPrometheus
    type: prometheus
    url: http://prometheus:9090
    isDefault: true
```

### AlertManager Configuration
File: `monitoring/alertmanager/alertmanager.yml`

#### Route Configuration
```yaml
route:
  group_by: ['alertname']
  group_wait: 10s
  repeat_interval: 1h
  receiver: 'default'
```

### ELK Configuration

#### Logstash Pipelines
Directory: `monitoring/logstash/pipeline/`

#### Filebeat Configuration
File: `monitoring/filebeat/filebeat.yml`

## 📊 Monitoring Best Practices

### Metrics Best Practices

1. **Use Labels Wisely**
   - Keep cardinality low
   - Use meaningful label names
   - Avoid user IDs in labels

2. **Naming Conventions**
   - Use snake_case
   - Include units in name
   - Be descriptive but concise

3. **Metric Types**
   - **Counters**: Total counts (requests, errors)
   - **Gauges**: Current values (memory, connections)
   - **Histograms**: Distributions (response times)

### Alerting Best Practices

1. **Alert on Symptoms, Not Causes**
   - Alert on user-facing issues
   - Use cause-based alerts for debugging

2. **Alert Fatigue Prevention**
   - Set appropriate thresholds
   - Use alert inhibition
   - Group related alerts

3. **Alert Documentation**
   - Include runbook links
   - Provide context in descriptions
   - Test alert procedures

### Log Management Best Practices

1. **Structured Logging**
   - Use JSON format
   - Include correlation IDs
   - Add contextual information

2. **Log Levels**
   - **ERROR**: Failures requiring attention
   - **WARN**: Potential issues
   - **INFO**: Important events
   - **DEBUG**: Detailed debugging

3. **Log Retention**
   - Set appropriate retention periods
   - Consider storage costs
   - Implement log rotation

## 🛠️ Troubleshooting

### Common Issues

#### Prometheus Not Scraping Targets
```bash
# Check target status
curl http://localhost:9090/api/v1/targets

# Check application metrics endpoint
curl http://localhost/metrics
```

#### Grafana Dashboard Not Loading
1. Check data source connection
2. Verify metric names in queries
3. Check time range selection

#### AlertManager Not Sending Alerts
1. Verify alert rules syntax
2. Check AlertManager configuration
3. Test webhook endpoints

#### ELK Stack Issues
```bash
# Check Elasticsearch health
curl http://localhost:9200/_cluster/health

# Check Logstash processing
docker logs logstash

# Check Filebeat status
docker exec filebeat filebeat test output
```

### Performance Tuning

#### Prometheus
- Adjust scrape intervals
- Optimize query performance
- Configure storage retention

#### Elasticsearch
- Adjust JVM heap size
- Configure index templates
- Set up index lifecycle management

#### Grafana
- Optimize dashboard queries
- Use query caching
- Limit data source connections

## 📚 Additional Resources

### Documentation Links
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [AlertManager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/)
- [Kibana Documentation](https://www.elastic.co/guide/en/kibana/current/)

### Community Dashboards
- [Grafana Dashboard Library](https://grafana.com/grafana/dashboards/)
- [Prometheus Exporters](https://prometheus.io/docs/instrumenting/exporters/)

### Training Resources
- [Prometheus Tutorial](https://prometheus.io/docs/tutorials/)
- [Grafana Learning](https://grafana.com/tutorials/)
- [Elastic Stack Training](https://www.elastic.co/training/)

---

## 🆘 Support

For issues and questions:
1. Check this documentation
2. Review application logs in Kibana
3. Check service status in Grafana
4. Create an issue in the repository

**Happy Monitoring! 📊🎉**

