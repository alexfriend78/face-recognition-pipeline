# database_schema.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, ARRAY, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class UploadedFile(Base):
    __tablename__ = 'uploaded_files'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50))  # 'image' or 'video'
    file_path = Column(String(500))
    upload_time = Column(DateTime, server_default=func.now())
    processing_status = Column(String(50), default='pending')  # pending, processing, completed, failed
    total_faces = Column(Integer, default=0)
    
    faces = relationship("Face", back_populates="file", cascade="all, delete-orphan")

class Face(Base):
    __tablename__ = 'faces'
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('uploaded_files.id'))
    face_id = Column(String(100), unique=True)  # Unique identifier for each face
    embedding = Column(Vector(512))  # InsightFace typically uses 512-dimensional embeddings
    bbox = Column(ARRAY(Float))  # [x, y, width, height]
    confidence = Column(Float)
    quality_score = Column(Float)  # Face quality assessment
    landmark_points = Column(Text)  # JSON string of facial landmarks
    frame_number = Column(Integer)  # For videos
    timestamp = Column(Float)  # Video timestamp in seconds
    face_image_path = Column(String(500))  # Path to cropped face image
    
    file = relationship("UploadedFile", back_populates="faces")
    
    # Additional metadata
    age = Column(Integer)
    gender = Column(String(10))
    emotion = Column(String(20))

class FaceCluster(Base):
    __tablename__ = 'face_clusters'
    
    id = Column(Integer, primary_key=True)
    cluster_name = Column(String(100))
    representative_face_id = Column(String(100))
    face_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class SearchLog(Base):
    __tablename__ = 'search_logs'
    
    id = Column(Integer, primary_key=True)
    search_image_path = Column(String(500))
    search_embedding = Column(Vector(512))
    results_count = Column(Integer)
    search_time = Column(Float)  # Search duration in milliseconds
    timestamp = Column(DateTime, server_default=func.now())

# Database initialization
def init_db():
    engine = create_engine(os.getenv('DATABASE_URL'))
    
    # Create pgvector extension
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    return engine

def get_session():
    engine = init_db()
    Session = sessionmaker(bind=engine)
    return Session()

if __name__ == "__main__":
    # Initialize database when running this script directly
    init_db()
    print("Database initialized successfully!")
