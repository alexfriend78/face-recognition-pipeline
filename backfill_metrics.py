#!/usr/bin/env python3
"""
Script to backfill face detection metrics from existing database data
"""

import os
import sys
sys.path.append('.')

from database_schema import get_session, UploadedFile, Face
from metrics import metrics

def main():
    """Backfill metrics from existing database data"""
    session = get_session()
    
    try:
        # Get all completed files grouped by type
        files = session.query(UploadedFile).filter_by(processing_status='completed').all()
        
        total_faces_backfilled = 0
        total_files_backfilled = 0
        
        for file_record in files:
            # Count faces for this file
            face_count = session.query(Face).filter_by(file_id=file_record.id).count()
            
            # Estimate processing duration based on file type and face count
            if file_record.file_type == 'image':
                # Images typically take 0.5-2 seconds
                estimated_duration = max(0.5, min(2.0, 0.5 + (face_count * 0.1)))
            else:  # video
                # Videos take longer, estimate based on face count
                estimated_duration = max(5.0, min(120.0, 10.0 + (face_count * 0.2)))
            
            # Track file processing metrics
            metrics.track_file_processing(
                file_type=file_record.file_type,
                status='completed',
                duration=estimated_duration
            )
            
            # Track face detection metrics if faces were found
            if face_count > 0:
                metrics.track_face_detection(
                    source_type=file_record.file_type,
                    num_faces=face_count,
                    duration=estimated_duration * 0.8,  # Face detection is part of total processing
                    quality_scores=[0.8] * face_count  # Default quality scores
                )
                total_faces_backfilled += face_count
            
            total_files_backfilled += 1
            print(f"Backfilled {face_count} faces, {estimated_duration:.1f}s duration for {file_record.file_type} file: {file_record.filename}")
        
        print(f"\nBackfilled metrics for {total_files_backfilled} files, {total_faces_backfilled} faces")
        
    except Exception as e:
        print(f"Error backfilling metrics: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
