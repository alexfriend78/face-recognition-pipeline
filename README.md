# Face Recognition Pipeline

A complete face recognition system built with Python, Flask, and Docker that automatically processes images and videos to detect, extract, and search for faces using state-of-the-art AI models.

## 🚀 Features

- **Automatic File Processing**: Drop files into a watch folder for automatic processing
- **Real-time Face Detection**: Uses InsightFace models for accurate face detection
- **Face Recognition & Search**: Find similar faces across your dataset
- **Video Support**: Process videos frame by frame to extract faces
- **Web Interface**: Modern web UI for file management and face search
- **RESTful API**: Complete API for integration with other applications
- **Background Processing**: Celery-based task queue for scalable processing
- **Vector Database**: PostgreSQL with pgvector for efficient similarity search

## 🛠 Tech Stack

- **Backend**: Python, Flask, Celery
- **Database**: PostgreSQL with pgvector extension
- **Message Queue**: Redis
- **AI Models**: InsightFace (buffalo_l)
- **Frontend**: HTML, CSS, JavaScript (Tailwind CSS)
- **Deployment**: Docker & Docker Compose
- **Monitoring**: Flower (Celery monitoring)

## 📋 Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available
- 10GB free disk space (for models and data)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/alexfriend78/face-recognition-pipeline
cd face-recognition-pipeline
```

### 2. Start the Application
```bash
docker-compose up -d
```

This will start all required services:
- Web Application (http://localhost:8000)
- PostgreSQL Database
- Redis Message Broker
- Celery Worker
- Flower Dashboard (http://localhost:5555)
- Folder Monitor

### 3. Access the Application

- **Main Interface**: http://localhost:8000
- **Task Monitor**: http://localhost:5555

## 📁 Project Structure

```
face-recognition-pipeline/
├── app.py                 # Main Flask application
├── celery_tasks.py        # Background task definitions
├── folder_monitor.py      # Automatic file monitoring
├── face_processor.py      # Face detection and processing logic
├── database_schema.py     # Database models and schema
├── docker-compose.yml     # Docker services configuration
├── Dockerfile            # Container build instructions
├── requirements.txt      # Python dependencies
├── data/                 # Data storage
│   ├── watch/           # Drop files here for auto-processing
│   ├── raw/             # Processed files
│   ├── processed/       # Face detection results
│   └── embeddings/      # Face embedding vectors
├── static/              # Web assets
├── templates/           # HTML templates
└── models/              # AI model storage
```

## 💡 Usage

### Automatic Processing
1. Drop image or video files into `./data/watch/` folder
2. Files are automatically detected and processed
3. Results are stored in the database
4. View results in the web interface

### Manual Upload
1. Visit http://localhost:8000
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

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Upload files for processing |
| `/search` | POST | Search for similar faces |
| `/files` | GET | List uploaded files |
| `/faces/{file_id}` | GET | Get faces from specific file |
| `/face-image/{face_id}` | GET | Get face image |
| `/stats` | GET | Get system statistics |
| `/task-status/{task_id}` | GET | Get task processing status |

## 🐳 Docker Services

The application consists of 6 Docker services:

- **web**: Main Flask application
- **postgres**: PostgreSQL database with pgvector
- **redis**: Message broker for task queue
- **celery**: Background task worker
- **flower**: Task monitoring dashboard
- **folder-monitor**: Automatic file processing

## 📊 Monitoring

### Flower Dashboard
Visit http://localhost:5555 to monitor:
- Active tasks and workers
- Task execution times
- Success/failure rates
- Queue status

### Logs
View service logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f folder-monitor
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

