# Face Recognition Pipeline - Complete Distribution Package

A comprehensive face recognition system with real-time monitoring, logging, and analytics capabilities.

## 🚀 Quick Start

**For macOS:**
```bash
git clone https://github.com/alexfriend78/face-recognition-pipeline.git
cd face-recognition-pipeline
chmod +x start-monitoring.sh
./start-monitoring.sh
```

**For Windows (WSL 2):**
```bash
git clone https://github.com/alexfriend78/face-recognition-pipeline.git
cd face-recognition-pipeline
chmod +x start-monitoring.sh
./start-monitoring.sh
```

## 📋 What You Get

### Main Application Features:
- **Face Detection & Recognition**: Powered by InsightFace AI models
- **Image & Video Processing**: Upload and process multiple file formats
- **Real-time Progress Tracking**: See processing status in real-time
- **Face Gallery**: Browse and search detected faces
- **Background Processing**: Scalable Celery worker system

### Complete Monitoring Stack:
- **📊 Grafana Dashboards**: Visual analytics and metrics (http://localhost:3000)
- **📈 Prometheus**: Metrics collection and alerting (http://localhost:9090)
- **📋 Kibana**: Log analysis and search (http://localhost:5601)
- **🌺 Flower**: Celery task monitoring (http://localhost/flower)
- **🚨 AlertManager**: Smart alerting system (http://localhost:9093)

### Infrastructure & Performance:
- **PostgreSQL with pgVector**: Efficient face embedding storage
- **Redis**: High-performance caching and task queuing
- **Nginx**: Load balancing and reverse proxy
- **Docker**: Containerized for easy deployment
- **ELK Stack**: Complete logging solution

## 🖥️ System Requirements

### Minimum Requirements:
- **RAM**: 8GB (16GB recommended)
- **Storage**: 10GB free space
- **CPU**: 4 cores (8 cores recommended)
- **Docker Desktop**: Latest version

### Recommended for Production:
- **RAM**: 32GB or more
- **Storage**: 50GB+ SSD
- **CPU**: 8+ cores
- **GPU**: NVIDIA GPU for faster processing (optional)

## 🌐 Access Points

Once running, access the application at:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Main App** | http://localhost | - |
| **Grafana** | http://localhost:3000 | admin / admin123 |
| **Kibana** | http://localhost:5601 | - |
| **Prometheus** | http://localhost:9090 | - |
| **Flower** | http://localhost/flower | - |
| **AlertManager** | http://localhost:9093 | - |

## 📊 Available Metrics & Monitoring

- **Face Detection Rates**: Real-time face detection analytics
- **System Performance**: CPU, memory, disk, network monitoring
- **Application Health**: Request rates, response times, error rates
- **Database Metrics**: PostgreSQL performance and connection stats
- **Cache Performance**: Redis hit rates and memory usage
- **Worker Status**: Celery task processing and queue depths

## 🛠️ Architecture

```
┌─── Web Interface (Flask) ───┐
│   ├── File Upload           │
│   ├── Face Gallery          │
│   └── Real-time Updates     │
└─────────────────────────────┘
            │
┌─── Background Workers ──────┐
│   ├── Face Detection        │
│   ├── Video Processing      │
│   └── Batch Operations      │
└─────────────────────────────┘
            │
┌─── Data Storage ───────────┐
│   ├── PostgreSQL + pgVector │
│   ├── Redis Cache           │
│   └── File System           │
└─────────────────────────────┘
            │
┌─── Monitoring Stack ───────┐
│   ├── Prometheus            │
│   ├── Grafana               │
│   ├── ELK Stack             │
│   └── AlertManager          │
└─────────────────────────────┘
```

## 🔧 Advanced Configuration

### Environment Variables:
- `UPLOAD_FOLDER`: Directory for uploaded files
- `CELERY_WORKER_CONCURRENCY`: Number of worker processes
- `REDIS_URL`: Redis connection string
- `DATABASE_URL`: PostgreSQL connection string

### Scaling Workers:
```bash
# Scale to 4 Celery workers
docker-compose up -d --scale celery=4
```

### Custom Configuration:
Edit `docker-compose.yml` and `monitoring/` configs for custom setups.

## 📖 Documentation

- **Deployment Guide**: `DEPLOYMENT_GUIDE.md` - Complete setup instructions
- **Monitoring Guide**: `MONITORING_GUIDE.md` - Detailed monitoring setup
- **API Documentation**: Available at `/docs` when running

## 🔄 Backup & Restore

### Create Backup:
```bash
./backup.sh
```

### Restore from Backup:
```bash
cd /path/to/backup/directory
./restore.sh
```

## 🛑 Stopping the Application

```bash
./stop-monitoring.sh
```

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section in `DEPLOYMENT_GUIDE.md`
2. View logs: `docker-compose logs [service-name]`
3. Restart services: `docker-compose restart`
4. Full rebuild: `docker-compose build --no-cache`

## 📄 License

This project includes enterprise-grade monitoring and logging capabilities built on open-source technologies.

---

**🎯 Ready to start? Follow the detailed instructions in `DEPLOYMENT_GUIDE.md`**
