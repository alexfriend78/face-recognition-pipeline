# face_processor.py
import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
import os
import json
import uuid
from typing import List, Dict, Tuple, Optional
import logging
from PIL import Image
import io

class FaceProcessor:
    def __init__(self, model_name='buffalo_l', ctx_id=0, det_size=(640, 640)):
        """
        Initialize InsightFace model
        
        Args:
            model_name: Model to use ('buffalo_l', 'buffalo_m', 'buffalo_s')
            ctx_id: GPU device id, -1 for CPU
            det_size: Detection input size
        """
        self.app = FaceAnalysis(
            name=model_name,
            root='./models',
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider'] if ctx_id >= 0 else ['CPUExecutionProvider']
        )
        self.app.prepare(ctx_id=ctx_id, det_size=det_size)
        self.logger = logging.getLogger(__name__)
        
    def process_image(self, image_path: str, save_faces: bool = True) -> List[Dict]:
        """
        Process a single image and extract faces
        
        Args:
            image_path: Path to image file
            save_faces: Whether to save cropped face images
            
        Returns:
            List of face dictionaries with embeddings and metadata
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Cannot read image: {image_path}")
            
            # Detect faces
            faces = self.app.get(img)
            
            results = []
            for idx, face in enumerate(faces):
                face_data = self._extract_face_data(face, img, idx, image_path, save_faces)
                results.append(face_data)
                
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing image {image_path}: {str(e)}")
            raise
    
    def process_video(self, video_path: str, frame_interval: int = 30, 
                     save_faces: bool = True, progress_callback=None) -> List[Dict]:
        """
        Process video and extract faces from frames
        
        Args:
            video_path: Path to video file
            frame_interval: Process every nth frame
            save_faces: Whether to save cropped face images
            progress_callback: Function to call with progress updates
            
        Returns:
            List of face dictionaries with embeddings and metadata
        """
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            results = []
            frame_count = 0
            processed_frames = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_interval == 0:
                    # Detect faces in current frame
                    faces = self.app.get(frame)
                    
                    for idx, face in enumerate(faces):
                        face_data = self._extract_face_data(
                            face, frame, idx, video_path, save_faces,
                            frame_number=frame_count, 
                            timestamp=frame_count / fps
                        )
                        results.append(face_data)
                    
                    processed_frames += 1
                    
                    # Progress callback
                    if progress_callback:
                        progress = (frame_count / total_frames) * 100
                        progress_callback(progress, processed_frames, len(results))
                
                frame_count += 1
            
            cap.release()
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing video {video_path}: {str(e)}")
            raise
    
    def _extract_face_data(self, face, image, face_idx, source_path, 
                          save_face=True, frame_number=None, timestamp=None) -> Dict:
        """
        Extract face data including embedding, bbox, and metadata
        """
        face_id = str(uuid.uuid4())
        
        # Extract bounding box
        bbox = face.bbox.astype(int).tolist()
        
        # Get face embedding
        embedding = face.normed_embedding.tolist()
        
        # Calculate face quality score
        quality_score = self._calculate_face_quality(face, image, bbox)
        
        # Extract landmarks
        landmarks = face.kps.tolist() if hasattr(face, 'kps') else None
        
        face_data = {
            'face_id': face_id,
            'embedding': embedding,
            'bbox': bbox,
            'confidence': float(face.det_score),
            'quality_score': quality_score,
            'landmark_points': json.dumps(landmarks) if landmarks else None,
            'frame_number': frame_number,
            'timestamp': timestamp,
            'source_path': source_path
        }
        
        # Extract additional attributes if available
        if hasattr(face, 'age'):
            face_data['age'] = int(face.age)
        if hasattr(face, 'gender'):
            face_data['gender'] = 'male' if face.gender == 1 else 'female'
        
        # Save cropped face image
        if save_face:
            face_image_path = self._save_face_image(image, bbox, face_id)
            face_data['face_image_path'] = face_image_path
        
        return face_data
    
    def _calculate_face_quality(self, face, image, bbox) -> float:
        """
        Calculate face quality score based on multiple factors
        """
        scores = []
        
        # 1. Detection confidence
        scores.append(float(face.det_score))
        
        # 2. Face size (larger is better)
        x1, y1, x2, y2 = bbox
        face_area = (x2 - x1) * (y2 - y1)
        image_area = image.shape[0] * image.shape[1]
        size_ratio = face_area / image_area
        scores.append(min(size_ratio * 10, 1.0))  # Normalize to 0-1
        
        # 3. Face sharpness (Laplacian variance)
        face_img = image[y1:y2, x1:x2]
        if face_img.size > 0:
            gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(laplacian_var / 1000, 1.0)  # Normalize
            scores.append(sharpness_score)
        
        # 4. Pose quality (frontal faces score higher)
        if hasattr(face, 'pose'):
            pose_score = 1.0 - (abs(face.pose[0]) + abs(face.pose[1])) / 180.0
            scores.append(pose_score)
        
        return np.mean(scores)
    
    def _save_face_image(self, image, bbox, face_id) -> str:
        """
        Save cropped face image with padding
        """
        x1, y1, x2, y2 = bbox
        
        # Add padding
        padding = 20
        h, w = image.shape[:2]
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)
        
        # Crop face
        face_img = image[y1:y2, x1:x2]
        
        # Save image
        save_dir = os.path.join('./data/processed/faces', face_id[:2])
        os.makedirs(save_dir, exist_ok=True)
        
        save_path = os.path.join(save_dir, f"{face_id}.jpg")
        cv2.imwrite(save_path, face_img)
        
        return save_path
    
    def compare_faces(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate similarity between two face embeddings
        
        Args:
            embedding1: First face embedding
            embedding2: Second face embedding
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        # Convert to numpy arrays
        emb1 = np.array(embedding1)
        emb2 = np.array(embedding2)
        
        # Calculate cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        
        # Convert to 0-1 range
        return (similarity + 1) / 2
    
    def find_similar_faces(self, query_embedding: List[float], 
                          all_embeddings: List[Tuple[str, List[float]]], 
                          threshold: float = 0.6, 
                          top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Find similar faces from a collection
        
        Args:
            query_embedding: Query face embedding
            all_embeddings: List of (face_id, embedding) tuples
            threshold: Similarity threshold
            top_k: Return top k results
            
        Returns:
            List of (face_id, similarity_score) tuples
        """
        similarities = []
        
        for face_id, embedding in all_embeddings:
            similarity = self.compare_faces(query_embedding, embedding)
            if similarity >= threshold:
                similarities.append((face_id, similarity))
        
        # Sort by similarity score
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]