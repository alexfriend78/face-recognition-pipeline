# Face Recognition Pipeline

A complete face recognition system built with Python, Flask, and Docker that automatically processes images and videos to detect, extract, and search for faces using state-of-the-art AI models.

## 🚀 Features

### Core Functionality
- **Automatic File Processing**: Drop files into a watch folder for automatic processing
- **Real-time Face Detection**: Uses InsightFace models for accurate face detection
- **Face Recognition & Search**: Find similar faces across your dataset
- **Video Support**: Process videos frame by frame to extract faces
- **Web Interface**: Modern web UI for file management and face search
- **RESTful API**: Complete API for integration with other applications
- **Background Processing**: Celery-based task queue for scalable processing
- **Vector Database**: PostgreSQL with pgvector for efficient similarity search
- **Batch Processing**: Efficient GPU-optimized batch processing for multiple files
- **Redis Caching**: Smart caching for faster search results

### Monitoring & Observability
- **Prometheus Metrics**: 15+ comprehensive metrics for application and infrastructure monitoring
- **Grafana Dashboards**: Pre-built dashboards with real-time visualizations
- **Structured Logging**: JSON-formatted logs with correlation IDs and context
- **ELK Stack**: Complete log aggregation with Elasticsearch, Logstash, and Kibana
- **Intelligent Alerting**: AlertManager with email, Slack, and webhook notifications
- **Performance Monitoring**: GPU utilization, memory usage, and processing times
- **Cache Analytics**: Redis performance metrics and hit ratio monitoring
- **Infrastructure Monitoring**: System metrics via Node Exporter, cAdvisor
- **Database Monitoring**: PostgreSQL and Redis performance metrics

## 🛠 Tech Stack

### Core Application
- **Backend**: Python, Flask, Celery
- **Database**: PostgreSQL with pgvector extension
- **Message Queue**: Redis
- **Web Server**: Nginx (reverse proxy)
- **AI Models**: InsightFace (buffalo_l)
- **Frontend**: HTML, CSS, JavaScript (Tailwind CSS)
- **Deployment**: Docker & Docker Compose

### Monitoring & Observability
- **Metrics**: Prometheus + Node Exporter + cAdvisor
- **Visualization**: Grafana with custom dashboards
- **Alerting**: AlertManager with multi-channel notifications
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Log Shipping**: Filebeat for container log collection
- **Task Monitoring**: Flower (Celery monitoring)
- **Database Monitoring**: Postgres Exporter + Redis Exporter
- **Structured Logging**: structlog for JSON formatted logs

## 📋 Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available
- 10GB free disk space (for models and data)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/face-recognition-pipeline.git
cd face-recognition-pipeline
```

### 2. Start the Application

#### Option A: Basic Application Only
```bash
docker-compose up -d
```

#### Option B: Complete Stack with Monitoring (Recommended)
```bash
# Start everything with comprehensive monitoring
./start-monitoring.sh
```

This will start all required services:
- Nginx Web Server (http://localhost:80)
- Web Application (via nginx) 
- PostgreSQL Database
- Redis Message Broker
- Celery Worker
- Flower Dashboard (via nginx)
- Folder Monitor
- **Prometheus** (Metrics Collection)
- **Grafana** (Dashboards & Visualization)
- **AlertManager** (Intelligent Alerting)
- **ELK Stack** (Log Aggregation & Analysis)
- **Infrastructure Monitoring** (Node, Redis, Postgres exporters)

### 3. Access the Application

#### Core Services
- **Main Interface**: http://localhost
- **Task Monitor**: http://localhost/flower
- **Cache Dashboard**: http://localhost/cache
- **Metrics Endpoint**: http://localhost/metrics

#### Monitoring Stack (if using `./start-monitoring.sh`)
- **📊 Grafana Dashboards**: http://localhost:3000 (admin/admin123)
- **🔥 Prometheus**: http://localhost:9090
- **🚨 AlertManager**: http://localhost:9093
- **📋 Kibana (Logs)**: http://localhost:5601
- **🖥️ Node Exporter**: http://localhost:9100
- **🔴 Redis Exporter**: http://localhost:9121
- **🐘 Postgres Exporter**: http://localhost:9187
- **📦 cAdvisor**: http://localhost:8080

## 📁 Project Structure

```
face-recognition-pipeline/
├── app.py                           # Main Flask application
├── celery_tasks.py                  # Background task definitions
├── folder_monitor.py                # Automatic file monitoring
├── face_processor.py                # Face detection and processing logic
├── database_schema.py               # Database models and schema
├── cache_helper.py                  # Redis caching utilities
├── logging_config.py                # Structured logging configuration
├── metrics.py                       # Prometheus metrics collection
├── docker-compose.yml               # Main application services
├── docker-compose.monitoring.yml    # Complete monitoring stack
├── Dockerfile                       # Container build instructions
├── requirements.txt                 # Python dependencies
├── start-monitoring.sh              # Start complete stack script
├── stop-monitoring.sh               # Stop all services script
├── MONITORING_GUIDE.md              # Comprehensive monitoring guide
├── data/                           # Data storage
│   ├── watch/                     # Drop files here for auto-processing
│   ├── raw/                       # Processed files
│   ├── processed/                 # Face detection results
│   └── embeddings/                # Face embedding vectors
├── monitoring/                     # Complete monitoring configuration
│   ├── prometheus/                # Prometheus config and alerts
│   ├── grafana/                   # Grafana dashboards and provisioning
│   ├── alertmanager/              # AlertManager configuration
│   ├── logstash/                  # Logstash pipeline configuration
│   └── filebeat/                  # Filebeat log shipping config
├── nginx/                          # Nginx reverse proxy configuration
├── static/                         # Web assets
├── templates/                      # HTML templates
└── models/                         # AI model storage
```

## 💡 Usage

### Automatic Processing
1. Drop image or video files into `./data/watch/` folder
2. Files are automatically detected and processed
3. Results are stored in the database
4. View results in the web interface

### Manual Upload
1. Visit http://localhost
2. Use the upload interface to select files
3. Monitor processing progress in real-time

### Face Search
1. Go to the Search section in the web interface
2. Upload a query image
3. Adjust similarity threshold and result count
4. View matching faces from your database

### Supported File Types
- **Images**: PNG, JPG, JPEG, GIF, BMP, WEBP
- **Videos**: MP4, AVI, MOV, WMV, FLV, MKV

## 🔧 API Endpoints

### Core API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Upload single file for processing |
| `/upload-batch` | POST | Upload multiple files for batch processing |
| `/search` | POST | Search for similar faces |
| `/files` | GET | List uploaded files with pagination |
| `/faces/{file_id}` | GET | Get faces from specific file |
| `/face-image/{face_id}` | GET | Get face image |
| `/stats` | GET | Get system statistics |
| `/task-status/{task_id}` | GET | Get task processing status |

### Monitoring & Caching
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/metrics` | GET | Prometheus metrics endpoint |
| `/cache` | GET | Cache statistics dashboard |
| `/cache/stats` | GET | Cache statistics API |
| `/cache/clear` | POST | Clear search cache |
| `/flower` | GET | Celery task monitoring (Flower) |

## 🐳 Docker Services

### Main Application Stack (6 services)
- **nginx**: Reverse proxy and load balancer
- **web**: Main Flask application with metrics
- **postgres**: PostgreSQL database with pgvector
- **redis**: Message broker for task queue
- **celery**: Background task worker
- **flower**: Task monitoring dashboard
- **folder-monitor**: Automatic file processing

### Monitoring Stack (8 additional services)
- **prometheus**: Metrics collection and storage
- **grafana**: Visualization and dashboards
- **alertmanager**: Intelligent alerting
- **node-exporter**: System metrics
- **redis-exporter**: Redis performance metrics
- **postgres-exporter**: Database metrics
- **cadvisor**: Container metrics
- **elasticsearch**: Log storage
- **logstash**: Log processing
- **kibana**: Log visualization
- **filebeat**: Log shipping

## 📊 Monitoring & Observability

### Quick Start Monitoring
```bash
# Start complete monitoring stack
./start-monitoring.sh

# Stop everything
./stop-monitoring.sh
```

### 🎯 Key Monitoring Features

#### Real-time Metrics (Prometheus + Grafana)
- **File Processing**: Upload rates, processing times, success/failure rates
- **Face Detection**: Detection rates, quality scores, processing duration
- **Search Performance**: Search times, cache hit ratios, result counts
- **System Health**: CPU, memory, GPU utilization, disk usage
- **Database Metrics**: Connection counts, query performance
- **Cache Metrics**: Redis performance, memory usage, hit rates

#### Intelligent Alerting (AlertManager)
- **Application Alerts**: High error rates, long processing times, low cache performance
- **Infrastructure Alerts**: High resource usage, service downtime
- **Multi-channel Notifications**: Email, Slack, webhooks
- **Smart Routing**: Alert severity-based routing and escalation

#### Log Analysis (ELK Stack)
- **Structured Logging**: JSON logs with correlation IDs
- **Real-time Search**: Instant log search and filtering
- **Error Tracking**: Automatic error detection and grouping
- **Performance Analysis**: Request timing and bottleneck identification

#### Traditional Monitoring
- **Flower Dashboard**: http://localhost/flower (Celery task monitoring)
- **Cache Dashboard**: http://localhost/cache (Redis statistics)

### Monitoring Dashboards

#### Grafana (Primary Dashboard)
- **URL**: http://localhost:3000
- **Login**: admin/admin123
- **Features**: Real-time metrics, custom dashboards, alerting

#### Kibana (Log Analysis)
- **URL**: http://localhost:5601
- **Features**: Log search, error tracking, performance analysis

#### Prometheus (Raw Metrics)
- **URL**: http://localhost:9090
- **Features**: Metric exploration, alert rule testing

### Log Management

#### View Logs in Kibana
1. Access Kibana: http://localhost:5601
2. Create index pattern: `face-recognition-logs-*`
3. Use Discover tab for log analysis

#### Traditional Log Viewing
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f folder-monitor

# Monitoring services
docker-compose -f docker-compose.monitoring.yml logs -f prometheus
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file to customize settings:

```env
DATABASE_URL=postgresql://facerecog:facerecog123@postgres:5432/face_recognition
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key-here
UPLOAD_FOLDER=/app/data/raw
PROCESSED_FOLDER=/app/data/processed
EMBEDDINGS_FOLDER=/app/data/embeddings
```

### Database Configuration
The system uses PostgreSQL with the pgvector extension for efficient vector similarity search.

Default credentials:
- Username: `facerecog`
- Password: `facerecog123`
- Database: `face_recognition`

## 📊 Monitoring & Observability

### Structured Logging
The application uses structured logging with `structlog` for better log analysis:

- **Development**: Colored console output
- **Production**: JSON formatted logs
- **Context**: Automatic request IDs, task IDs, and operation context
- **Performance**: Execution time tracking

### Prometheus Metrics
Comprehensive metrics collection available at: http://localhost/metrics

**Available Metrics:**
- `face_recognition_files_uploaded_total` - File upload counter
- `face_recognition_files_processed_total` - File processing counter with status
- `face_recognition_file_processing_duration_seconds` - Processing time histogram
- `face_recognition_faces_detected_total` - Face detection counter
- `face_recognition_face_quality_score` - Face quality distribution
- `face_recognition_searches_total` - Search operations with cache status
- `face_recognition_search_duration_seconds` - Search time histogram
- `face_recognition_cache_hit_ratio` - Cache hit ratio percentage
- `face_recognition_http_requests_total` - HTTP request counter
- `face_recognition_gpu_utilization_percent` - GPU usage (if available)
- `face_recognition_memory_usage_bytes` - Memory usage tracking
- `face_recognition_batch_processing_duration_seconds` - Batch processing times

### Dashboards

#### Flower Dashboard
Access the Celery task monitoring dashboard at: http://localhost/flower

#### Cache Statistics
View Redis cache statistics at: http://localhost/cache

The cache dashboard shows:
- Cache hit/miss ratios
- Memory usage
- Number of cached searches
- Performance metrics

### Setting up Prometheus

1. Use the provided `prometheus.yml` configuration
2. Run Prometheus: `prometheus --config.file=prometheus.yml`
3. Access Prometheus UI at http://localhost:9090
4. Import dashboards into Grafana for visualization

### Environment Variables for Monitoring

```bash
ENVIRONMENT=production          # Enables JSON logging
SERVICE_VERSION=1.0.0          # Service version in metrics
PROMETHEUS_MULTIPROC_DIR=/tmp   # For multi-worker metrics
```

## 🚀 Quick Start Commands

### Complete Stack with Monitoring
```bash
# Start everything (recommended)
./start-monitoring.sh

# Stop everything
./stop-monitoring.sh

# Clean reset (removes all data)
docker-compose down -v
docker-compose -f docker-compose.monitoring.yml down -v
```

### Basic Application Only
```bash
# Start basic stack
docker-compose up -d

# Stop basic stack
docker-compose down
```

### Monitoring Commands
```bash
# Check service status
docker ps

# View logs
docker-compose logs -f [service-name]

# Restart specific service
docker-compose restart [service-name]
```

## 🛠 Development

### Running in Development Mode
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://facerecog:facerecog123@localhost:5432/face_recognition"
export REDIS_URL="redis://localhost:6379/0"

# Run the application
python app.py
```

### Adding New Features
1. Modify the relevant Python files
2. Update requirements.txt if new dependencies are added
3. Rebuild Docker images: `docker-compose build`
4. Restart services: `docker-compose up -d`

## 🐛 Troubleshooting

### Common Issues

**Service won't start**
```bash
docker-compose down
docker-compose up -d
```

**Database connection issues**
```bash
docker-compose logs postgres
```

**Out of memory errors**
- Ensure you have at least 4GB RAM available
- Reduce batch sizes in processing

**File permission issues**
```bash
chmod -R 755 ./data
```

### Performance Tuning

For better performance with large datasets:
- Increase PostgreSQL shared_buffers
- Add more Celery workers
- Use SSD storage for data directory

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📧 Support

For support and questions, please open an issue in the GitHub repository.

## 🙏 Acknowledgments

- [InsightFace](https://github.com/deepinsight/insightface) for the face recognition models
- [pgvector](https://github.com/pgvector/pgvector) for vector similarity search
- Flask and Celery communities for excellent documentation

