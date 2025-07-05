# Face Recognition Pipeline - Deployment Update Guide

This guide covers how to update your Face Recognition Pipeline deployment from GitHub across different operating systems.

## Table of Contents
- [Prerequisites](#prerequisites)
- [General Update Process](#general-update-process)
- [Platform-Specific Instructions](#platform-specific-instructions)
  - [CentOS/RHEL](#centosrhel)
  - [Ubuntu](#ubuntu)
  - [Windows](#windows)
- [Post-Update Verification](#post-update-verification)
- [Rollback Procedures](#rollback-procedures)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before updating, ensure you have:
- Git installed on your system
- Docker and Docker Compose installed
- SSH access to your deployment server
- Backup of your current deployment (recommended)
- Network access to GitHub

## General Update Process

The update process follows these general steps across all platforms:

1. **Create Backup** (Optional but recommended)
2. **Stop Running Services**
3. **Pull Latest Changes from Git**
4. **Rebuild Docker Images**
5. **Start Services**
6. **Verify Deployment**

---

## Platform-Specific Instructions

## CentOS/RHEL

### Initial Setup (First Time Only)

```bash
# Install Git if not already installed
sudo yum update -y
sudo yum install -y git

# Install Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
```

### Update Process

```bash
# 1. Navigate to your deployment directory
cd /path/to/face-recognition-pipeline

# 2. Create backup (optional but recommended)
sudo ./backup.sh

# 3. Stop running services
sudo docker-compose down

# 4. Pull latest changes
git fetch origin
git pull origin main

# Alternative: Update to specific version
# git checkout v1.1.0

# 5. Rebuild images with latest changes
sudo docker-compose build --no-cache

# 6. Start services
sudo docker-compose up -d

# 7. Check service status
sudo docker-compose ps
sudo docker-compose logs -f
```

### System Service Integration (Optional)

Create a systemd service for automatic startup:

```bash
# Create service file
sudo tee /etc/systemd/system/face-recognition.service > /dev/null <<EOF
[Unit]
Description=Face Recognition Pipeline
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/face-recognition-pipeline
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable face-recognition.service
sudo systemctl start face-recognition.service
```

---

## Ubuntu

### Initial Setup (First Time Only)

```bash
# Update package list
sudo apt update

# Install Git
sudo apt install -y git

# Install Docker
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in for group changes to take effect
```

### Update Process

```bash
# 1. Navigate to your deployment directory
cd /path/to/face-recognition-pipeline

# 2. Create backup (optional but recommended)
./backup.sh

# 3. Stop running services
docker-compose down

# 4. Pull latest changes
git fetch origin
git pull origin main

# Alternative: Update to specific version
# git checkout v1.1.0

# 5. Rebuild images with latest changes
docker-compose build --no-cache

# 6. Start services
docker-compose up -d

# 7. Check service status
docker-compose ps
docker-compose logs -f
```

### System Service Integration (Optional)

```bash
# Create service file
sudo tee /etc/systemd/system/face-recognition.service > /dev/null <<EOF
[Unit]
Description=Face Recognition Pipeline
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/face-recognition-pipeline
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=your-username
Group=docker

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable face-recognition.service
sudo systemctl start face-recognition.service
```

---

## Windows

### Initial Setup (First Time Only)

**Using PowerShell as Administrator:**

```powershell
# Install Chocolatey (package manager)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install Git
choco install git -y

# Install Docker Desktop
# Download and install Docker Desktop from: https://www.docker.com/products/docker-desktop
# Make sure to enable WSL 2 backend during installation

# Restart PowerShell after installation
```

**Alternative: Manual Installation**
1. Download Git from: https://git-scm.com/download/win
2. Download Docker Desktop from: https://www.docker.com/products/docker-desktop
3. Install both applications following their setup wizards

### Update Process

**Using PowerShell:**

```powershell
# 1. Navigate to your deployment directory
cd C:\path\to\face-recognition-pipeline

# 2. Create backup (optional but recommended)
.\backup.sh  # If using Git Bash
# Or manually backup using PowerShell
$backupDir = "..\face-recognition-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Path $backupDir
Copy-Item -Path ".\*" -Destination $backupDir -Recurse -Exclude @("data", "models", ".git")

# 3. Stop running services
docker-compose down

# 4. Pull latest changes
git fetch origin
git pull origin main

# Alternative: Update to specific version
# git checkout v1.1.0

# 5. Rebuild images with latest changes
docker-compose build --no-cache

# 6. Start services
docker-compose up -d

# 7. Check service status
docker-compose ps
docker-compose logs -f
```

**Using Git Bash (Recommended):**

```bash
# 1. Navigate to your deployment directory
cd /c/path/to/face-recognition-pipeline

# 2. Create backup (optional but recommended)
./backup.sh

# 3. Stop running services
docker-compose down

# 4. Pull latest changes
git fetch origin
git pull origin main

# 5. Rebuild images with latest changes
docker-compose build --no-cache

# 6. Start services
docker-compose up -d

# 7. Check service status
docker-compose ps
docker-compose logs -f
```

### Windows Service Integration (Optional)

Create a Windows service using NSSM (Non-Sucking Service Manager):

```powershell
# Install NSSM
choco install nssm -y

# Create the service
nssm install FaceRecognitionPipeline "C:\Program Files\Docker\Docker\resources\bin\docker-compose.exe"
nssm set FaceRecognitionPipeline AppParameters "up -d"
nssm set FaceRecognitionPipeline AppDirectory "C:\path\to\face-recognition-pipeline"
nssm set FaceRecognitionPipeline DisplayName "Face Recognition Pipeline"
nssm set FaceRecognitionPipeline Description "AI-powered face recognition and search system"

# Start the service
nssm start FaceRecognitionPipeline
```

---

## Post-Update Verification

After updating on any platform, verify the deployment:

### 1. Check Service Status
```bash
docker-compose ps
```
All services should show "Up" status.

### 2. Check Application Health
```bash
# Test main application
curl http://localhost/health

# Expected response:
# {"status": "healthy", "timestamp": "...", "service": "face-recognition-pipeline"}
```

### 3. Verify Metrics
```bash
# Check Prometheus metrics
curl http://localhost/metrics | grep face_recognition

# Check Grafana dashboard
# Open http://localhost:3000 in browser
```

### 4. Test File Upload
```bash
# Test file upload endpoint
curl -X POST -F "file=@test_image.jpg" http://localhost/upload
```

### 5. Check Logs
```bash
# Check for any errors in logs
docker-compose logs --tail=50

# Check specific service logs
docker-compose logs web
docker-compose logs celery
```

---

## Rollback Procedures

If the update fails, you can rollback using these methods:

### Method 1: Git Rollback
```bash
# Stop services
docker-compose down

# Rollback to previous commit
git log --oneline -10  # Find the previous commit hash
git checkout <previous-commit-hash>

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d
```

### Method 2: Tag Rollback
```bash
# Stop services
docker-compose down

# Rollback to previous tagged version
git checkout v1.0.0  # Replace with desired version

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d
```

### Method 3: Backup Restore
```bash
# Stop services
docker-compose down

# Restore from backup
cd ../face-recognition-backup-YYYYMMDD-HHMMSS
./restore.sh
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Permission Denied Errors (Linux/macOS)
```bash
# Fix Docker permissions
sudo chown -R $USER:$USER /path/to/face-recognition-pipeline
sudo chmod +x *.sh

# Or run with sudo
sudo docker-compose down
sudo docker-compose up -d
```

#### 2. Port Already in Use
```bash
# Find process using port 80
sudo netstat -tulpn | grep :80
# Or on newer systems
sudo ss -tulpn | grep :80

# Kill the process
sudo kill -9 <PID>

# Restart services
docker-compose up -d
```

#### 3. Out of Disk Space
```bash
# Clean up Docker
docker system prune -a -f
docker volume prune -f

# Check disk space
df -h
```

#### 4. Git Merge Conflicts
```bash
# Reset local changes
git stash
git pull origin main
git stash pop

# Or force reset (loses local changes)
git reset --hard origin/main
```

#### 5. Docker Build Failures
```bash
# Clear build cache
docker builder prune -a -f

# Rebuild from scratch
docker-compose build --no-cache --pull

# Check Docker daemon status
# Linux/macOS:
sudo systemctl status docker
# Windows: Check Docker Desktop is running
```

#### 6. Network Connectivity Issues
```bash
# Test GitHub connectivity
curl -I https://github.com

# Check DNS resolution
nslookup github.com

# Use different Git remote if needed
git remote set-url origin git@github.com:alexfriend78/face-recognition-pipeline.git
```

---

## Environment-Specific Notes

### CentOS/RHEL Specific
- SELinux may block Docker operations. Consider setting to permissive mode for Docker:
  ```bash
  sudo setsebool -P container_manage_cgroup on
  ```
- Firewall configuration may be needed:
  ```bash
  sudo firewall-cmd --permanent --add-port=80/tcp
  sudo firewall-cmd --reload
  ```

### Ubuntu Specific
- UFW firewall may block ports:
  ```bash
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  ```

### Windows Specific
- Ensure Docker Desktop is running before executing commands
- Use PowerShell as Administrator for best results
- WSL 2 backend is recommended for better performance
- Windows Defender may interfere with Docker operations

---

## Automation Scripts

### Linux/macOS Update Script

Create `update.sh`:
```bash
#!/bin/bash
set -e

echo "🔄 Starting Face Recognition Pipeline Update..."

# Navigate to script directory
cd "$(dirname "$0")"

# Create backup
echo "📦 Creating backup..."
./backup.sh

# Stop services
echo "⏹️ Stopping services..."
docker-compose down

# Pull latest changes
echo "🔄 Pulling latest changes..."
git fetch origin
git pull origin main

# Rebuild images
echo "🏗️ Rebuilding images..."
docker-compose build --no-cache

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# Verify deployment
echo "✅ Verifying deployment..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Update completed successfully!"
    docker-compose ps
else
    echo "❌ Health check failed. Check logs:"
    docker-compose logs --tail=20
    exit 1
fi
```

### Windows PowerShell Update Script

Create `update.ps1`:
```powershell
$ErrorActionPreference = "Stop"

Write-Host "🔄 Starting Face Recognition Pipeline Update..." -ForegroundColor Green

# Navigate to script directory
Set-Location -Path $PSScriptRoot

# Create backup
Write-Host "📦 Creating backup..." -ForegroundColor Yellow
$backupDir = "..\face-recognition-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Path $backupDir | Out-Null
Copy-Item -Path ".\*" -Destination $backupDir -Recurse -Exclude @("data", "models", ".git")

# Stop services
Write-Host "⏹️ Stopping services..." -ForegroundColor Yellow
docker-compose down

# Pull latest changes
Write-Host "🔄 Pulling latest changes..." -ForegroundColor Yellow
git fetch origin
git pull origin main

# Rebuild images
Write-Host "🏗️ Rebuilding images..." -ForegroundColor Yellow
docker-compose build --no-cache

# Start services
Write-Host "🚀 Starting services..." -ForegroundColor Yellow
docker-compose up -d

# Wait for services to start
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Verify deployment
Write-Host "✅ Verifying deployment..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost/health" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Update completed successfully!" -ForegroundColor Green
        docker-compose ps
    }
} catch {
    Write-Host "❌ Health check failed. Check logs:" -ForegroundColor Red
    docker-compose logs --tail=20
    exit 1
}
```

---

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**: Check for updates and security patches
2. **Monthly**: Review logs and performance metrics
3. **Quarterly**: Full backup and disaster recovery testing

### Monitoring

- Monitor application logs: `docker-compose logs -f`
- Check resource usage: `docker stats`
- Monitor disk space: `df -h`
- Review Grafana dashboards: http://localhost:3000

### Getting Help

1. Check application logs for error messages
2. Review this troubleshooting guide
3. Check GitHub issues: https://github.com/alexfriend78/face-recognition-pipeline/issues
4. Contact system administrator or development team

---

## Conclusion

This guide provides comprehensive instructions for updating the Face Recognition Pipeline across different platforms. Always test updates in a development environment before applying to production systems.

For additional support or questions, refer to the project documentation or contact the development team.
