# Face Recognition Pipeline - Linux Installation Guide

This guide provides step-by-step instructions for installing and running the Face Recognition Pipeline on Linux systems (CentOS/RHEL and Ubuntu/Debian).

## 🐧 Supported Linux Distributions

- **Ubuntu**: 18.04, 20.04, 22.04 LTS
- **CentOS**: 7, 8, Stream
- **RHEL**: 7, 8, 9
- **Debian**: 10, 11, 12

---

## 📋 Prerequisites

### System Requirements:
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 20GB free space
- **CPU**: 4 cores minimum
- **Network**: Internet connection for downloading packages

---

## 🚀 Installation Methods

### Method 1: Docker Installation (Recommended)

This is the easiest and most reliable method.

#### For Ubuntu/Debian:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group (optional, allows running docker without sudo)
sudo usermod -aG docker $USER
newgrp docker

# Install Git
sudo apt install -y git

# Clone the repository
git clone https://github.com/alexfriend78/face-recognition-pipeline.git
cd face-recognition-pipeline

# Make startup script executable
chmod +x start-monitoring.sh

# Run the application (this will build images and start services)
./start-monitoring.sh
```

#### For CentOS/RHEL:

```bash
# Update system
sudo yum update -y

# Install Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group (optional)
sudo usermod -aG docker $USER
newgrp docker

# Install Git
sudo yum install -y git

# Clone the repository
git clone https://github.com/alexfriend78/face-recognition-pipeline.git
cd face-recognition-pipeline

# Make startup script executable
chmod +x start-monitoring.sh

# Run the application
./start-monitoring.sh
```

---

### Method 2: Native Installation (Advanced)

For those who prefer not to use Docker, here's how to install everything natively.

#### Prerequisites for Native Installation:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib redis-server nginx git build-essential libpq-dev
```

**CentOS/RHEL:**
```bash
sudo yum install -y python3 python3-pip postgresql postgresql-server postgresql-contrib redis nginx git gcc gcc-c++ postgresql-devel
```

#### Step 1: Set Up PostgreSQL

**Ubuntu/Debian:**
```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE face_recognition;"
sudo -u postgres psql -c "CREATE USER facerecog WITH PASSWORD 'facerecog123';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE face_recognition TO facerecog;"

# Install pgvector extension
sudo -u postgres psql face_recognition -c "CREATE EXTENSION vector;"
```

**CentOS/RHEL:**
```bash
# Initialize and start PostgreSQL
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE face_recognition;"
sudo -u postgres psql -c "CREATE USER facerecog WITH PASSWORD 'facerecog123';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE face_recognition TO facerecog;"
```

#### Step 2: Set Up Redis

```bash
# Start Redis
sudo systemctl start redis
sudo systemctl enable redis

# Test Redis connection
redis-cli ping
```

#### Step 3: Set Up Python Environment

```bash
# Clone the repository
git clone https://github.com/alexfriend78/face-recognition-pipeline.git
cd face-recognition-pipeline

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

#### Step 4: Configure Environment Variables

```bash
# Create environment file
cat > .env << EOF
DATABASE_URL=postgresql://facerecog:facerecog123@localhost:5432/face_recognition
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
UPLOAD_FOLDER=/opt/face-recognition/data/raw
PROCESSED_FOLDER=/opt/face-recognition/data/processed
EMBEDDINGS_FOLDER=/opt/face-recognition/data/embeddings
ENVIRONMENT=production
SERVICE_VERSION=1.0.0
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
EOF

# Create data directories
sudo mkdir -p /opt/face-recognition/data/{raw,processed,embeddings,watch}
sudo chown -R $USER:$USER /opt/face-recognition/
```

#### Step 5: Set Up Database Schema

```bash
# Activate virtual environment
source venv/bin/activate

# Run database migrations
python -c "
from database_schema import create_tables
create_tables()
print('Database tables created successfully!')
"
```

#### Step 6: Configure Nginx

```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/face-recognition << 'EOF'
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /flower/ {
        proxy_pass http://127.0.0.1:5555/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /metrics {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable site (Ubuntu/Debian)
sudo ln -s /etc/nginx/sites-available/face-recognition /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# For CentOS/RHEL, copy to /etc/nginx/conf.d/
sudo cp /etc/nginx/sites-available/face-recognition /etc/nginx/conf.d/face-recognition.conf
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 7: Create Systemd Services

**Flask App Service:**
```bash
sudo tee /etc/systemd/system/face-recognition-web.service << EOF
[Unit]
Description=Face Recognition Web Application
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/face-recognition-pipeline
Environment=PATH=/home/$USER/face-recognition-pipeline/venv/bin
EnvironmentFile=/home/$USER/face-recognition-pipeline/.env
ExecStart=/home/$USER/face-recognition-pipeline/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF
```

**Celery Worker Service:**
```bash
sudo tee /etc/systemd/system/face-recognition-celery.service << EOF
[Unit]
Description=Face Recognition Celery Worker
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/face-recognition-pipeline
Environment=PATH=/home/$USER/face-recognition-pipeline/venv/bin
EnvironmentFile=/home/$USER/face-recognition-pipeline/.env
ExecStart=/home/$USER/face-recognition-pipeline/venv/bin/celery -A celery_tasks worker --loglevel=info --concurrency=4
Restart=always

[Install]
WantedBy=multi-user.target
EOF
```

**Flower Service:**
```bash
sudo tee /etc/systemd/system/face-recognition-flower.service << EOF
[Unit]
Description=Face Recognition Flower Monitor
After=network.target redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/face-recognition-pipeline
Environment=PATH=/home/$USER/face-recognition-pipeline/venv/bin
EnvironmentFile=/home/$USER/face-recognition-pipeline/.env
ExecStart=/home/$USER/face-recognition-pipeline/venv/bin/celery -A celery_tasks flower --port=5555
Restart=always

[Install]
WantedBy=multi-user.target
EOF
```

#### Step 8: Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable face-recognition-web face-recognition-celery face-recognition-flower
sudo systemctl start face-recognition-web face-recognition-celery face-recognition-flower

# Check status
sudo systemctl status face-recognition-web
sudo systemctl status face-recognition-celery
sudo systemctl status face-recognition-flower
```

---

## 🌐 Accessing the Application

Once installation is complete, you can access:

- **Main Application**: http://your-server-ip or http://localhost
- **Flower (Celery Monitor)**: http://your-server-ip/flower

---

## 🔧 Firewall Configuration

### Ubuntu (UFW):
```bash
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS (if using SSL)
sudo ufw enable
```

### CentOS/RHEL (firewalld):
```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

---

## 📊 Optional: Install Monitoring Stack

For the complete monitoring experience, you can install Prometheus, Grafana, and ELK stack natively:

### Quick Monitoring Setup:
```bash
# Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
sudo mv prometheus-*/prometheus /usr/local/bin/
sudo mv prometheus-*/promtool /usr/local/bin/

# Install Grafana (Ubuntu/Debian)
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt update && sudo apt install grafana

# Install Grafana (CentOS/RHEL)
sudo yum install -y https://dl.grafana.com/oss/release/grafana-10.0.0-1.x86_64.rpm

# Start services
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

---

## 🛑 Managing Services

### Start Services:
```bash
# Docker method
./start-monitoring.sh

# Native method
sudo systemctl start face-recognition-web face-recognition-celery face-recognition-flower
```

### Stop Services:
```bash
# Docker method
./stop-monitoring.sh

# Native method
sudo systemctl stop face-recognition-web face-recognition-celery face-recognition-flower
```

### View Logs:
```bash
# Docker method
docker-compose logs -f web

# Native method
sudo journalctl -u face-recognition-web -f
```

---

## 🔧 Troubleshooting

### Common Issues:

1. **Port Already in Use**:
   ```bash
   sudo netstat -tulpn | grep :80
   sudo systemctl stop apache2  # or httpd on CentOS
   ```

2. **PostgreSQL Connection Issues**:
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Test connection
   psql -h localhost -U facerecog -d face_recognition
   ```

3. **Redis Connection Issues**:
   ```bash
   # Check Redis status
   sudo systemctl status redis
   
   # Test connection
   redis-cli ping
   ```

4. **Python Dependencies Issues**:
   ```bash
   # Reinstall in virtual environment
   source venv/bin/activate
   pip install --force-reinstall -r requirements.txt
   ```

---

## 🚀 Production Recommendations

1. **Use HTTPS**: Configure SSL certificates with Let's Encrypt
2. **Database Security**: Use strong passwords and restrict access
3. **Backup Strategy**: Regular database and file backups
4. **Monitoring**: Set up log rotation and monitoring alerts
5. **Updates**: Keep system and dependencies updated

---

**✅ You're all set! The Face Recognition Pipeline is now running on your Linux system.**
