# cli_tool.py
import click
import os
import glob
from pathlib import Path
from database_schema import get_session, UploadedFile, Face, init_db
from celery_tasks import process_uploaded_file, search_similar_faces
from face_processor import FaceProcessor
import shutil
import uuid
import json
from tabulate import tabulate
from tqdm import tqdm

@click.group()
def cli():
    """Face Recognition Pipeline CLI Tool"""
    pass

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--wait', is_flag=True, help='Wait for processing to complete')
def process(file_path, wait):
    """Process a single image or video file"""
    
    # Check file type
    ext = Path(file_path).suffix.lower().lstrip('.')
    if ext in {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}:
        file_type = 'image'
    elif ext in {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv'}:
        file_type = 'video'
    else:
        click.echo(f"Error: Unsupported file type '{ext}'", err=True)
        return
    
    # Copy file to processing directory
    filename = os.path.basename(file_path)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    dest_path = os.path.join('./data/raw', unique_filename)
    os.makedirs('./data/raw', exist_ok=True)
    shutil.copy2(file_path, dest_path)
    
    # Add to database
    session = get_session()
    try:
        uploaded_file = UploadedFile(
            filename=unique_filename,
            original_filename=filename,
            file_type=file_type,
            file_path=dest_path,
            processing_status='pending'
        )
        session.add(uploaded_file)
        session.commit()
        file_id = uploaded_file.id
        
        click.echo(f"File added to database with ID: {file_id}")
        
        # Start processing
        task = process_uploaded_file.apply_async(
            args=[file_id, dest_path, file_type]
        )
        
        click.echo(f"Processing started with task ID: {task.id}")
        
        if wait:
            click.echo("Waiting for processing to complete...")
            with tqdm(total=100) as pbar:
                last_progress = 0
                while not task.ready():
                    result = task.result
                    if isinstance(result, dict) and 'current' in result:
                        progress = result['current']
                        pbar.update(progress - last_progress)
                        last_progress = progress
                pbar.update(100 - last_progress)
            
            if task.successful():
                result = task.result
                click.echo(f"\nProcessing completed! Found {result['total_faces']} faces")
            else:
                click.echo("\nProcessing failed!", err=True)
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        session.rollback()
    finally:
        session.close()

@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--recursive', is_flag=True, help='Process subdirectories')
@click.option('--pattern', default='*', help='File pattern (e.g., *.jpg)')
def batch(directory, recursive, pattern):
    """Process all files in a directory"""
    
    # Find files
    if recursive:
        files = list(Path(directory).rglob(pattern))
    else:
        files = list(Path(directory).glob(pattern))
    
    # Filter by supported extensions
    supported_ext = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'}
    files = [f for f in files if f.suffix.lower() in supported_ext]
    
    if not files:
        click.echo("No supported files found")
        return
    
    click.echo(f"Found {len(files)} files to process")
    
    # Process each file
    with click.progressbar(files, label='Processing files') as bar:
        for file_path in bar:
            try:
                # Use the process function logic
                ext = file_path.suffix.lower().lstrip('.')
                file_type = 'image' if ext in {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'} else 'video'
                
                filename = file_path.name
                unique_filename = f"{uuid.uuid4()}_{filename}"
                dest_path = os.path.join('./data/raw', unique_filename)
                shutil.copy2(str(file_path), dest_path)
                
                session = get_session()
                try:
                    uploaded_file = UploadedFile(
                        filename=unique_filename,
                        original_filename=filename,
                        file_type=file_type,
                        file_path=dest_path,
                        processing_status='pending'
                    )
                    session.add(uploaded_file)
                    session.commit()
                    
                    process_uploaded_file.apply_async(
                        args=[uploaded_file.id, dest_path, file_type]
                    )
                    
                except Exception:
                    session.rollback()
                finally:
                    session.close()
                    
            except Exception as e:
                click.echo(f"\nError processing {file_path}: {str(e)}", err=True)

@cli.command()
@click.argument('query_image', type=click.Path(exists=True))
@click.option('--threshold', default=0.6, help='Similarity threshold (0-1)')
@click.option('--limit', default=10, help='Maximum results')
def search(query_image, threshold, limit):
    """Search for similar faces"""
    
    click.echo(f"Searching for faces similar to: {query_image}")
    
    # Perform search
    result = search_similar_faces(query_image, threshold, limit)
    
    if result['status'] == 'error':
        click.echo(f"Error: {result['message']}", err=True)
        return
    
    if not result['results']:
        click.echo("No similar faces found")
        return
    
    # Display results
    table_data = []
    for r in result['results']:
        table_data.append([
            r['face_id'][:8] + '...',
            f"{r['similarity']:.2%}",
            r['file_name'],
            r['quality_score'],
            r['timestamp'] if r['timestamp'] else 'N/A'
        ])
    
    headers = ['Face ID', 'Similarity', 'File', 'Quality', 'Timestamp']
    click.echo("\nSearch Results:")
    click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))

@cli.command()
def stats():
    """Show database statistics"""
    
    session = get_session()
    try:
        total_files = session.query(UploadedFile).count()
        total_faces = session.query(Face).count()
        
        # Files by status
        status_counts = {}
        for status in ['pending', 'processing', 'completed', 'failed']:
            count = session.query(UploadedFile).filter_by(processing_status=status).count()
            status_counts[status] = count
        
        # Files by type
        image_count = session.query(UploadedFile).filter_by(file_type='image').count()
        video_count = session.query(UploadedFile).filter_by(file_type='video').count()
        
        click.echo("\n=== Face Recognition Pipeline Statistics ===\n")
        click.echo(f"Total Files: {total_files}")
        click.echo(f"Total Faces: {total_faces}")
        click.echo(f"\nFiles by Status:")
        for status, count in status_counts.items():
            click.echo(f"  {status.capitalize()}: {count}")
        click.echo(f"\nFiles by Type:")
        click.echo(f"  Images: {image_count}")
        click.echo(f"  Videos: {video_count}")
        
        if total_files > 0:
            avg_faces = total_faces / total_files
            click.echo(f"\nAverage Faces per File: {avg_faces:.1f}")
        
    finally:
        session.close()

@cli.command()
@click.option('--file-id', type=int, help='List faces from specific file')
@click.option('--limit', default=20, help='Maximum faces to display')
def list_faces(file_id, limit):
    """List faces in the database"""
    
    session = get_session()
    try:
        query = session.query(Face)
        if file_id:
            query = query.filter_by(file_id=file_id)
        
        faces = query.limit(limit).all()
        
        if not faces:
            click.echo("No faces found")
            return
        
        table_data = []
        for face in faces:
            table_data.append([
                face.face_id[:8] + '...',
                face.file.original_filename,
                f"{face.confidence:.2%}",
                f"{face.quality_score:.2%}",
                face.gender if face.gender else 'N/A',
                face.age if face.age else 'N/A'
            ])
        
        headers = ['Face ID', 'File', 'Confidence', 'Quality', 'Gender', 'Age']
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
        
    finally:
        session.close()

@cli.command()
def init():
    """Initialize the database"""
    click.echo("Initializing database...")
    try:
        init_db()
        click.echo("Database initialized successfully!")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

@cli.command()
@click.option('--watch-folder', default='./data/watch', help='Folder to monitor')
@click.option('--process-existing', is_flag=True, help='Process existing files')
def monitor(watch_folder, process_existing):
    """Start folder monitoring service"""
    from folder_monitor import start_folder_monitor
    
    click.echo(f"Starting folder monitor on: {watch_folder}")
    click.echo("Press Ctrl+C to stop")
    
    try:
        start_folder_monitor(watch_folder, process_existing)
    except KeyboardInterrupt:
        click.echo("\nMonitoring stopped")

if __name__ == '__main__':
    cli()