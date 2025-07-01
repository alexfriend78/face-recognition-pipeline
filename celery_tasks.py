# celery_tasks.py
from celery import Celery
from celery import current_task
import os
import json
from database_schema import get_session, UploadedFile, Face
from face_processor import FaceProcessor
from sqlalchemy.orm import Session
import logging
from datetime import datetime

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
logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def process_uploaded_file(self, file_id: int, file_path: str, file_type: str):
    """
    Process uploaded image or video file
    """
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
        logger.error(f"Error processing file {file_id}: {str(e)}")
        
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
        
        return {
            'status': 'success',
            'query_face': {
                'bbox': query_face['bbox'],
                'quality_score': query_face['quality_score']
            },
            'results': results,
            'total_results': len(results)
        }
        
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

# To run Celery worker:
# celery -A celery_tasks worker --loglevel=info