# folder_monitor.py
import os
import time
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import logging
from database_schema import get_session, UploadedFile
from celery_tasks import process_uploaded_file
import hashlib

class FaceRecognitionHandler(FileSystemEventHandler):
    """
    Monitors a folder and automatically processes new image/video files
    """
    
    def __init__(self, watch_folder, processed_folder, allowed_extensions):
        self.watch_folder = watch_folder
        self.processed_folder = processed_folder
        self.allowed_extensions = allowed_extensions
        self.processing_files = set()  # Track files being processed
        self.logger = logging.getLogger(__name__)
        
        # Create folders if they don't exist
        os.makedirs(watch_folder, exist_ok=True)
        os.makedirs(processed_folder, exist_ok=True)
        
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory:
            self.process_file(event.src_path)
    
    def on_moved(self, event):
        """Handle file move events (some systems use move instead of create)"""
        if not event.is_directory:
            self.process_file(event.dest_path)
    
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory:
            # Wait a bit to ensure file write is complete
            time.sleep(0.5)
            self.process_file(event.src_path)
    
    def process_file(self, file_path):
        """Process a new file"""
        # Check if file is already being processed
        if file_path in self.processing_files:
            return
        
        # Check file extension
        file_ext = Path(file_path).suffix.lower().lstrip('.')
        if file_ext not in self.allowed_extensions:
            self.logger.info(f"Skipping file {file_path} - unsupported extension")
            return
        
        # Wait for file to be fully written (check if size is stable)
        if not self._is_file_ready(file_path):
            return
        
        try:
            self.processing_files.add(file_path)
            self.logger.info(f"Processing new file: {file_path}")
            
            # Get file info
            filename = os.path.basename(file_path)
            file_type = 'image' if file_ext in {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'} else 'video'
            
            # Generate unique filename to avoid conflicts
            file_hash = self._get_file_hash(file_path)
            unique_filename = f"{file_hash}_{filename}"
            
            # Copy file to processing directory
            dest_path = os.path.join(self.processed_folder, unique_filename)
            shutil.copy2(file_path, dest_path)
            
            # Add to database
            session = get_session()
            try:
                # Check if file already exists (by hash)
                existing = session.query(UploadedFile).filter_by(filename=unique_filename).first()
                if existing:
                    self.logger.info(f"File already processed: {filename}")
                    return
                
                # Create database record
                uploaded_file = UploadedFile(
                    filename=unique_filename,
                    original_filename=filename,
                    file_type=file_type,
                    file_path=dest_path,
                    processing_status='pending'
                )
                session.add(uploaded_file)
                session.commit()
                
                # Trigger processing
                task = process_uploaded_file.apply_async(
                    args=[uploaded_file.id, dest_path, file_type]
                )
                
                self.logger.info(f"Started processing task {task.id} for file {filename}")
                
            except Exception as e:
                self.logger.error(f"Database error: {str(e)}")
                session.rollback()
                # Clean up copied file
                if os.path.exists(dest_path):
                    os.remove(dest_path)
            finally:
                session.close()
                
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
        finally:
            self.processing_files.discard(file_path)
    
    def _is_file_ready(self, file_path, stability_time=2):
        """Check if file has finished being written"""
        try:
            # Check if file exists and is accessible
            if not os.path.exists(file_path):
                return False
            
            # Check if file size is stable
            size1 = os.path.getsize(file_path)
            time.sleep(stability_time)
            size2 = os.path.getsize(file_path)
            
            return size1 == size2 and size1 > 0
            
        except Exception:
            return False
    
    def _get_file_hash(self, file_path, chunk_size=8192):
        """Generate hash of file for deduplication"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()[:12]
        except Exception:
            return str(int(time.time()))

def start_folder_monitor(watch_folder=None, process_existing=False):
    """
    Start monitoring a folder for new files
    
    Args:
        watch_folder: Folder to monitor (default: ./data/watch)
        process_existing: Whether to process existing files in folder
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Set folders
    if watch_folder is None:
        watch_folder = os.path.join('./data', 'watch')
    processed_folder = os.path.join('./data', 'raw')
    
    # Allowed extensions
    allowed_extensions = {
        'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp',  # Images
        'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv'     # Videos
    }
    
    # Create handler
    event_handler = FaceRecognitionHandler(
        watch_folder, 
        processed_folder,
        allowed_extensions
    )
    
    # Process existing files if requested
    if process_existing:
        logger.info("Processing existing files in watch folder...")
        for file_path in Path(watch_folder).glob('*'):
            if file_path.is_file() and file_path.suffix.lower().lstrip('.') in allowed_extensions:
                event_handler.process_file(str(file_path))
    
    # Set up observer
    observer = Observer()
    observer.schedule(event_handler, watch_folder, recursive=False)
    
    # Start monitoring
    observer.start()
    logger.info(f"Started monitoring folder: {watch_folder}")
    logger.info("Drop image or video files into this folder for automatic processing")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Stopped folder monitoring")
    
    observer.join()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor folder for automatic face processing')
    parser.add_argument('--watch-folder', type=str, help='Folder to monitor')
    parser.add_argument('--process-existing', action='store_true', 
                       help='Process existing files in folder on startup')
    
    args = parser.parse_args()
    
    start_folder_monitor(
        watch_folder=args.watch_folder,
        process_existing=args.process_existing
    )