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
