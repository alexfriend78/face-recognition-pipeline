# app.py
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime
import json
from database_schema import get_session, UploadedFile, Face
from celery_tasks import celery_app, process_uploaded_file, search_similar_faces
from sqlalchemy import desc
import logging

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', './data/raw')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_UPLOAD_SIZE', 104857600))  # 100MB

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*", message_queue=os.getenv('REDIS_URL'))
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv'}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return 'image'
    elif ext in ALLOWED_VIDEO_EXTENSIONS:
        return 'video'
    return None

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        
        # Save file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(file_path)
        
        # Determine file type
        file_type = get_file_type(original_filename)
        
        # Save to database
        session = get_session()
        try:
            uploaded_file = UploadedFile(
                filename=unique_filename,
                original_filename=original_filename,
                file_type=file_type,
                file_path=file_path,
                processing_status='pending'
            )
            session.add(uploaded_file)
            session.commit()
            file_id = uploaded_file.id
            
            # Start background processing
            task = process_uploaded_file.apply_async(
                args=[file_id, file_path, file_type]
            )
            
            return jsonify({
                'success': True,
                'file_id': file_id,
                'task_id': task.id,
                'filename': original_filename,
                'file_type': file_type
            })
            
        except Exception as e:
            logger.error(f"Error saving file record: {str(e)}")
            return jsonify({'error': 'Database error'}), 500
        finally:
            session.close()
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/task-status/<task_id>')
def task_status(task_id):
    """Check background task status"""
    task = celery_app.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 100,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 100),
            'status': task.info.get('status', '')
        }
        if task.state == 'SUCCESS':
            response['result'] = task.info
    else:
        response = {
            'state': task.state,
            'current': 0,
            'total': 100,
            'status': str(task.info)
        }
    
    return jsonify(response)

@app.route('/search', methods=['POST'])
def search_faces():
    """Search for similar faces"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    threshold = float(request.form.get('threshold', 0.6))
    top_k = int(request.form.get('top_k', 20))
    
    if file and allowed_file(file.filename):
        # Save query image temporarily
        query_filename = f"query_{uuid.uuid4()}.jpg"
        query_path = os.path.join(app.config['UPLOAD_FOLDER'], 'queries', query_filename)
        os.makedirs(os.path.dirname(query_path), exist_ok=True)
        file.save(query_path)
        
        # Start search task
        task = search_similar_faces.apply_async(
            args=[query_path, threshold, top_k]
        )
        
        # Wait for result (with timeout)
        try:
            result = task.get(timeout=30)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return jsonify({'error': 'Search failed'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/files')
def list_files():
    """List all uploaded files"""
    session = get_session()
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Query files
        query = session.query(UploadedFile).order_by(desc(UploadedFile.upload_time))
        total = query.count()
        files = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Format response
        result = {
            'files': [
                {
                    'id': f.id,
                    'filename': f.original_filename,
                    'file_type': f.file_type,
                    'upload_time': f.upload_time.isoformat(),
                    'processing_status': f.processing_status,
                    'total_faces': f.total_faces
                }
                for f in files
            ],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        session.close()

@app.route('/faces/<file_id>')
def get_file_faces(file_id):
    """Get all faces from a specific file"""
    session = get_session()
    try:
        faces = session.query(Face).filter_by(file_id=file_id).all()
        
        result = {
            'faces': [
                {
                    'face_id': f.face_id,
                    'bbox': f.bbox,
                    'confidence': f.confidence,
                    'quality_score': f.quality_score,
                    'face_image_path': f.face_image_path,
                    'frame_number': f.frame_number,
                    'timestamp': f.timestamp,
                    'age': f.age,
                    'gender': f.gender
                }
                for f in faces
            ],
            'total': len(faces)
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting faces: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        session.close()

@app.route('/face-image/<face_id>')
def get_face_image(face_id):
    """Serve face image"""
    session = get_session()
    try:
        face = session.query(Face).filter_by(face_id=face_id).first()
        if face and face.face_image_path and os.path.exists(face.face_image_path):
            return send_file(face.face_image_path, mimetype='image/jpeg')
        return jsonify({'error': 'Face image not found'}), 404
    finally:
        session.close()

@app.route('/stats')
def get_stats():
    """Get system statistics"""
    session = get_session()
    try:
        stats = {
            'total_files': session.query(UploadedFile).count(),
            'total_faces': session.query(Face).count(),
            'pending_files': session.query(UploadedFile).filter_by(processing_status='pending').count(),
            'processing_files': session.query(UploadedFile).filter_by(processing_status='processing').count(),
            'completed_files': session.query(UploadedFile).filter_by(processing_status='completed').count(),
            'failed_files': session.query(UploadedFile).filter_by(processing_status='failed').count()
        }
        return jsonify(stats)
    finally:
        session.close()

# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
