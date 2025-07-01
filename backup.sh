#!/bin/bash

# Face Recognition Pipeline Backup Script
# Creates a complete backup of your working Docker setup

BACKUP_DIR="../face-recognition-backup-$(date +%Y%m%d-%H%M%S)"
echo "🔄 Creating backup in: $BACKUP_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Save Docker images
echo "📦 Saving Docker images..."
docker save face-recognition-pipeline-web:latest | gzip > "$BACKUP_DIR/face-recognition-web.tar.gz"
docker save face-recognition-pipeline-celery:latest | gzip > "$BACKUP_DIR/face-recognition-celery.tar.gz"
docker save face-recognition-pipeline-flower:latest | gzip > "$BACKUP_DIR/face-recognition-flower.tar.gz"

# Backup database
echo "🗄️ Backing up database..."
docker-compose exec postgres pg_dump -U facerecog face_recognition | gzip > "$BACKUP_DIR/database-backup.sql.gz"

# Backup source code (excluding data and models)
echo "📁 Backing up source code..."
tar -czf "$BACKUP_DIR/source-code-backup.tar.gz" --exclude='data' --exclude='models' --exclude='.git' --exclude='__pycache__' .

# Copy restore script
cp ../face-recognition-backup/restore.sh "$BACKUP_DIR/" 2>/dev/null || echo "Note: restore.sh not found, create manually if needed"

# Create backup info file
cat > "$BACKUP_DIR/backup-info.txt" << EOF
Face Recognition Pipeline Backup
Created: $(date)
Docker Images: 3 files (web, celery, flower)
Database: PostgreSQL dump included
Source Code: Complete project files

To restore:
1. cd to backup directory
2. Run: ./restore.sh
3. Or manually load images with: docker load < image.tar.gz

Backup Size:
$(du -sh "$BACKUP_DIR" | cut -f1)
EOF

echo "✅ Backup complete!"
echo "📁 Location: $BACKUP_DIR"
echo "💾 Total size: $(du -sh "$BACKUP_DIR" | cut -f1)"
echo ""
echo "To restore, run: cd '$BACKUP_DIR' && ./restore.sh"

