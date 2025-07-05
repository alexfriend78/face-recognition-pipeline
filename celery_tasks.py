# celery_tasks.py
from celery import Celery
from celery import current_task
from celery import group, chord
import os
import json
from database_schema import get_session, UploadedFile, Face
from face_processor import FaceProcessor
from sqlalchemy.orm import Session
from cache_helper import cache_helper
from logging_config import configure_logging, get_logger
from metrics import metrics, TimedOperation
import hashlib
from datetime import datetime
from typing import List, Dict, Tuple
import time

# Ensure logging is configured for Celery workers
configure_logging()

# Initialize Celery
celery_app = Celery(
    'face_recognition',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Initialize face processor
face_processor = FaceProcessor()
logger = get_logger(__name__)

@celery_app.task(bind=True)
def process_uploaded_file(self, file_id: int, file_path: str, file_type: str):
    """
    Process uploaded image or video file
    """
    start_time = time.time()
    logger = get_logger(__name__).bind(task_id=self.request.id, file_id=file_id, file_type=file_type)
    logger.info("Starting file processing", file_path=file_path)
    
    # Track file upload metric
    metrics.track_file_upload(file_type)
    
    session = get_session()
    
    try:
        # Update status to processing
        file_record = session.query(UploadedFile).filter_by(id=file_id).first()
        if not file_record:
            raise ValueError(f"File record not found: {file_id}")
        
        file_record.processing_status = 'processing'
        session.commit()
        
        # Update progress
        current_task.update_state(
            state='PROCESSING',
            meta={'current': 0, 'total': 100, 'status': 'Starting processing...'}
        )
        
        # Process based on file type
        if file_type == 'image':
            faces = face_processor.process_image(file_path)
            total_faces = len(faces)
            
            # Save faces to database
            for i, face_data in enumerate(faces):
                save_face_to_db(session, file_id, face_data)
                
                # Update progress
                progress = int((i + 1) / total_faces * 100) if total_faces > 0 else 100
                current_task.update_state(
                    state='PROCESSING',
                    meta={
                        'current': progress,
                        'total': 100,
                        'status': f'Processing face {i+1}/{total_faces}'
                    }
                )
        
        elif file_type == 'video':
            def progress_callback(progress, frames_processed, faces_found):
                current_task.update_state(
                    state='PROCESSING',
                    meta={
                        'current': int(progress),
                        'total': 100,
                        'status': f'Processed {frames_processed} frames, found {faces_found} faces'
                    }
                )
            
            faces = face_processor.process_video(
                file_path, 
                frame_interval=30,
                progress_callback=progress_callback
            )
            
            # Save faces to database
            for face_data in faces:
                save_face_to_db(session, file_id, face_data)
        
        # Update file record
        file_record.processing_status = 'completed'
        file_record.total_faces = len(faces)
        session.commit()
        
        # Track metrics
        duration = time.time() - start_time
        metrics.track_file_processing(file_type, 'completed', duration)
        
        # Track face detection metrics
        quality_scores = [face.get('quality_score', 0.0) for face in faces]
        metrics.track_face_detection(
            source_type=file_type,
            num_faces=len(faces),
            duration=duration,
            quality_scores=quality_scores
        )
        
        logger.info("File processing completed", 
                   total_faces=len(faces), 
                   duration_seconds=duration)
        
        # Final update
        current_task.update_state(
            state='SUCCESS',
            meta={
                'current': 100,
                'total': 100,
                'status': f'Completed! Found {len(faces)} faces',
                'total_faces': len(faces)
            }
        )
        
        return {
            'status': 'success',
            'file_id': file_id,
            'total_faces': len(faces),
            'message': f'Successfully processed {len(faces)} faces'
        }
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error("File processing failed", 
                    error=str(e), 
                    duration_seconds=duration)
        
        # Track failed processing metric
        metrics.track_file_processing(file_type, 'failed', duration)
        
        # Update status to failed
        file_record = session.query(UploadedFile).filter_by(id=file_id).first()
        if file_record:
            file_record.processing_status = 'failed'
            session.commit()
        
        # Update task state
        current_task.update_state(
            state='FAILURE',
            meta={
                'current': 0,
                'total': 100,
                'status': f'Error: {str(e)}'
            }
        )
        
        raise
        
    finally:
        session.close()

@celery_app.task
def search_similar_faces(query_image_path: str, threshold: float = 0.6, top_k: int = 20):
    """
    Search for similar faces in the database
    """
    start_time = time.time()
    logger = get_logger(__name__).bind(
        operation="face_search",
        threshold=threshold,
        top_k=top_k
    )
    logger.info("Starting face search", query_image_path=query_image_path)
    
    # Create query parameters for caching with file hash
    try:
        with open(query_image_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
    except:
        file_hash = query_image_path  # Fallback to path if hashing fails
    
    query_params = {
        'file_hash': file_hash,
        'threshold': threshold,
        'top_k': top_k
    }
    
    # Check if result is cached
    cached_result = cache_helper.get_cached_search_result(query_params)
    if cached_result:
        duration = time.time() - start_time
        metrics.track_search(cache_hit=True, duration=duration, num_results=len(cached_result.get('data', {}).get('results', [])))
        logger.info("Cache hit for face search", duration_seconds=duration)
        return cached_result.get('data', cached_result)

    session = get_session()
    try:
        # Process query image
        query_faces = face_processor.process_image(query_image_path, save_faces=False)
        
        if not query_faces:
            return {
                'status': 'error',
                'message': 'No faces found in query image'
            }
        
        # Use the first face found
        query_face = query_faces[0]
        query_embedding = query_face['embedding']
        
        # Get all faces from database
        all_faces = session.query(Face).all()
        
        # Prepare embeddings for comparison
        face_embeddings = [
            (face.face_id, json.loads(face.embedding) if isinstance(face.embedding, str) else face.embedding)
            for face in all_faces
        ]
        
        # Find similar faces
        similar_faces = face_processor.find_similar_faces(
            query_embedding, 
            face_embeddings, 
            threshold, 
            top_k
        )
        
        # Get face details
        results = []
        for face_id, similarity in similar_faces:
            face = session.query(Face).filter_by(face_id=face_id).first()
            if face:
                results.append({
                    'face_id': face.face_id,
                    'similarity': float(similarity),
                    'file_id': face.file_id,
                    'file_name': face.file.original_filename,
                    'face_image_path': face.face_image_path,
                    'bbox': face.bbox,
                    'quality_score': face.quality_score,
                    'timestamp': face.timestamp,
                    'frame_number': face.frame_number
                })
        
        result = {
            'status': 'success',
            'query_face': {
                'bbox': query_face['bbox'],
                'quality_score': query_face['quality_score']
            },
            'results': results,
            'total_results': len(results)
        }

        # Cache the result
        cache_helper.cache_search_result(query_params, result, ttl=3600)  # Cache for 1 hour
        
        # Track metrics
        duration = time.time() - start_time
        metrics.track_search(cache_hit=False, duration=duration, num_results=len(results))
        
        logger.info("Face search completed", 
                   num_results=len(results),
                   duration_seconds=duration)

        return result
        
    except Exception as e:
        logger.error(f"Error searching faces: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }
    finally:
        session.close()

@celery_app.task
def cluster_faces(min_cluster_size: int = 3, distance_threshold: float = 0.4):
    """
    Cluster similar faces together
    """
    from sklearn.cluster import DBSCAN
    import numpy as np
    
    session = get_session()
    
    try:
        # Get all faces
        faces = session.query(Face).all()
        
        if len(faces) < min_cluster_size:
            return {
                'status': 'error',
                'message': f'Not enough faces for clustering. Need at least {min_cluster_size}'
            }
        
        # Extract embeddings
        face_ids = []
        embeddings = []
        
        for face in faces:
            face_ids.append(face.face_id)
            embedding = json.loads(face.embedding) if isinstance(face.embedding, str) else face.embedding
            embeddings.append(embedding)
        
        # Convert to numpy array
        X = np.array(embeddings)
        
        # Perform clustering
        clustering = DBSCAN(
            eps=distance_threshold, 
            min_samples=min_cluster_size,
            metric='cosine'
        ).fit(X)
        
        # Process results
        clusters = {}
        for face_id, label in zip(face_ids, clustering.labels_):
            if label != -1:  # -1 means noise/outlier
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(face_id)
        
        return {
            'status': 'success',
            'num_clusters': len(clusters),
            'clusters': clusters,
            'noise_points': sum(1 for label in clustering.labels_ if label == -1)
        }
        
    except Exception as e:
        logger.error(f"Error clustering faces: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }
    finally:
        session.close()

def save_face_to_db(session: Session, file_id: int, face_data: dict):
    """
    Save face data to database
    """
    face = Face(
        file_id=file_id,
        face_id=face_data['face_id'],
        embedding=face_data['embedding'],
        bbox=face_data['bbox'],
        confidence=face_data['confidence'],
        quality_score=face_data['quality_score'],
        landmark_points=face_data.get('landmark_points'),
        frame_number=face_data.get('frame_number'),
        timestamp=face_data.get('timestamp'),
        face_image_path=face_data.get('face_image_path'),
        age=face_data.get('age'),
        gender=face_data.get('gender'),
        emotion=face_data.get('emotion')
    )
    
    session.add(face)
    session.commit()

@celery_app.task(bind=True)
def process_batch_files(self, file_batch: List[Dict]):
    """
    Process a batch of files efficiently
    
    Args:
        file_batch: List of dicts with 'file_id', 'file_path', 'file_type'
    """
    session = get_session()
    
    try:
        batch_size = len(file_batch)
        processed_files = 0
        total_faces = 0
        
        # Update all files to processing status
        file_ids = [f['file_id'] for f in file_batch]
        session.query(UploadedFile).filter(UploadedFile.id.in_(file_ids)).update(
            {'processing_status': 'processing'}, synchronize_session=False
        )
        session.commit()
        
        # Process files in batch
        for i, file_info in enumerate(file_batch):
            file_id = file_info['file_id']
            file_path = file_info['file_path']
            file_type = file_info['file_type']
            
            try:
                # Update progress
                current_task.update_state(
                    state='PROCESSING',
                    meta={
                        'current': i,
                        'total': batch_size,
                        'status': f'Processing file {i+1}/{batch_size}: {os.path.basename(file_path)}'
                    }
                )
                
                # Process file
                if file_type == 'image':
                    faces = face_processor.process_image(file_path)
                elif file_type == 'video':
                    faces = face_processor.process_video(file_path, frame_interval=30)
                else:
                    continue
                
                # Save faces to database
                for face_data in faces:
                    save_face_to_db(session, file_id, face_data)
                
                # Update file record
                file_record = session.query(UploadedFile).filter_by(id=file_id).first()
                if file_record:
                    file_record.processing_status = 'completed'
                    file_record.total_faces = len(faces)
                
                total_faces += len(faces)
                processed_files += 1
                
            except Exception as e:
                logger.error(f"Error processing file {file_id} in batch: {str(e)}")
                # Mark this file as failed but continue with others
                file_record = session.query(UploadedFile).filter_by(id=file_id).first()
                if file_record:
                    file_record.processing_status = 'failed'
        
        session.commit()
        
        # Final update
        current_task.update_state(
            state='SUCCESS',
            meta={
                'current': batch_size,
                'total': batch_size,
                'status': f'Batch completed! Processed {processed_files}/{batch_size} files, found {total_faces} faces',
                'processed_files': processed_files,
                'total_faces': total_faces
            }
        )
        
        return {
            'status': 'success',
            'batch_size': batch_size,
            'processed_files': processed_files,
            'total_faces': total_faces,
            'message': f'Successfully processed {processed_files}/{batch_size} files with {total_faces} faces'
        }
        
    except Exception as e:
        logger.error(f"Error processing batch: {str(e)}")
        
        # Mark all remaining files as failed
        session.query(UploadedFile).filter(UploadedFile.id.in_(file_ids)).update(
            {'processing_status': 'failed'}, synchronize_session=False
        )
        session.commit()
        
        current_task.update_state(
            state='FAILURE',
            meta={
                'current': 0,
                'total': batch_size,
                'status': f'Batch processing failed: {str(e)}'
            }
        )
        
        raise
        
    finally:
        session.close()

@celery_app.task(bind=True)
def process_batch_images_optimized(self, image_paths: List[str], batch_size: int = 8):
    """
    Optimized batch processing for images using GPU efficiently
    
    Args:
        image_paths: List of image file paths
        batch_size: Number of images to process simultaneously
    """
    session = get_session()
    results = []
    
    try:
        total_images = len(image_paths)
        processed_images = 0
        total_faces = 0
        
        # Process images in batches
        for batch_start in range(0, total_images, batch_size):
            batch_end = min(batch_start + batch_size, total_images)
            batch_paths = image_paths[batch_start:batch_end]
            
            # Update progress
            current_task.update_state(
                state='PROCESSING',
                meta={
                    'current': processed_images,
                    'total': total_images,
                    'status': f'Processing batch {batch_start//batch_size + 1}, images {batch_start+1}-{batch_end}'
                }
            )
            
            # Process batch of images
            batch_results = []
            for img_path in batch_paths:
                try:
                    faces = face_processor.process_image(img_path)
                    batch_results.append({
                        'path': img_path,
                        'faces': faces,
                        'status': 'success'
                    })
                    total_faces += len(faces)
                except Exception as e:
                    logger.error(f"Error processing image {img_path}: {str(e)}")
                    batch_results.append({
                        'path': img_path,
                        'faces': [],
                        'status': 'error',
                        'error': str(e)
                    })
                
                processed_images += 1
            
            results.extend(batch_results)
            
            # Small delay to prevent GPU overheating
            time.sleep(0.1)
        
        # Final update
        current_task.update_state(
            state='SUCCESS',
            meta={
                'current': total_images,
                'total': total_images,
                'status': f'Batch processing completed! Processed {processed_images} images, found {total_faces} faces',
                'total_faces': total_faces
            }
        )
        
        return {
            'status': 'success',
            'total_images': total_images,
            'processed_images': processed_images,
            'total_faces': total_faces,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        current_task.update_state(
            state='FAILURE',
            meta={
                'current': processed_images,
                'total': len(image_paths),
                'status': f'Batch processing failed: {str(e)}'
            }
        )
        raise
    
    finally:
        session.close()

@celery_app.task
def schedule_batch_processing(file_ids: List[int], batch_size: int = 4):
    """
    Schedule multiple files for batch processing
    
    Args:
        file_ids: List of file IDs to process
        batch_size: Size of each processing batch
    """
    session = get_session()
    
    try:
        # Get file information
        files = session.query(UploadedFile).filter(UploadedFile.id.in_(file_ids)).all()
        
        if not files:
            return {'status': 'error', 'message': 'No files found'}
        
        # Group files into batches
        file_batches = []
        current_batch = []
        
        for file_record in files:
            file_info = {
                'file_id': file_record.id,
                'file_path': file_record.file_path,
                'file_type': file_record.file_type
            }
            current_batch.append(file_info)
            
            if len(current_batch) >= batch_size:
                file_batches.append(current_batch)
                current_batch = []
        
        # Add remaining files
        if current_batch:
            file_batches.append(current_batch)
        
        # Create batch processing tasks
        batch_tasks = []
        for batch in file_batches:
            task = process_batch_files.delay(batch)
            batch_tasks.append(task.id)
        
        return {
            'status': 'success',
            'message': f'Scheduled {len(file_batches)} batch tasks for {len(files)} files',
            'batch_count': len(file_batches),
            'total_files': len(files),
            'task_ids': batch_tasks
        }
        
    except Exception as e:
        logger.error(f"Error scheduling batch processing: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }
    
    finally:
        session.close()

# To run Celery worker:
# celery -A celery_tasks worker --loglevel=info
# 
# For batch processing, you can also run multiple workers:
# celery -A celery_tasks worker --loglevel=info --concurrency=4
