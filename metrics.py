# metrics.py
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, multiprocess, generate_latest
import time
import os
import functools
from typing import Dict, Any, Optional
from datetime import datetime


class MetricsCollector:
    """Centralized metrics collector for the face recognition pipeline"""
    
    def __init__(self):
        # Use multiprocess mode for production with multiple workers
        if os.getenv('PROMETHEUS_MULTIPROC_DIR'):
            self.registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(self.registry)
        else:
            self.registry = None
        
        # Application info
        self.app_info = Info(
            'face_recognition_app_info',
            'Application information',
            registry=self.registry
        )
        self.app_info.info({
            'version': os.getenv('SERVICE_VERSION', '1.0.0'),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'service': 'face-recognition-pipeline'
        })
        
        # File processing metrics
        self.files_uploaded_total = Counter(
            'face_recognition_files_uploaded_total',
            'Total number of files uploaded',
            ['file_type'],
            registry=self.registry
        )
        
        self.files_processed_total = Counter(
            'face_recognition_files_processed_total',
            'Total number of files processed',
            ['file_type', 'status'],
            registry=self.registry
        )
        
        self.file_processing_duration = Histogram(
            'face_recognition_file_processing_duration_seconds',
            'Time spent processing files',
            ['file_type'],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
            registry=self.registry
        )
        
        # Face detection metrics
        self.faces_detected_total = Counter(
            'face_recognition_faces_detected_total',
            'Total number of faces detected',
            ['source_type'],
            registry=self.registry
        )
        
        self.face_detection_duration = Histogram(
            'face_recognition_face_detection_duration_seconds',
            'Time spent detecting faces',
            ['source_type'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            registry=self.registry
        )
        
        self.face_quality_score = Histogram(
            'face_recognition_face_quality_score',
            'Quality scores of detected faces',
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self.registry
        )
        
        # Search metrics
        self.searches_total = Counter(
            'face_recognition_searches_total',
            'Total number of face searches performed',
            ['cache_status'],
            registry=self.registry
        )
        
        self.search_duration = Histogram(
            'face_recognition_search_duration_seconds',
            'Time spent on face searches',
            ['cache_status'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )
        
        self.search_results_count = Histogram(
            'face_recognition_search_results_count',
            'Number of results returned by searches',
            buckets=[0, 1, 5, 10, 20, 50, 100, 200],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_operations_total = Counter(
            'face_recognition_cache_operations_total',
            'Total cache operations',
            ['operation', 'status'],
            registry=self.registry
        )
        
        self.cache_hit_ratio = Gauge(
            'face_recognition_cache_hit_ratio',
            'Cache hit ratio as a percentage',
            registry=self.registry
        )
        
        # System metrics
        self.active_tasks = Gauge(
            'face_recognition_active_tasks',
            'Number of active Celery tasks',
            ['task_type'],
            registry=self.registry
        )
        
        self.database_connections = Gauge(
            'face_recognition_database_connections',
            'Number of active database connections',
            registry=self.registry
        )
        
        self.gpu_utilization = Gauge(
            'face_recognition_gpu_utilization_percent',
            'GPU utilization percentage',
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'face_recognition_memory_usage_bytes',
            'Memory usage in bytes',
            ['type'],
            registry=self.registry
        )
        
        # Batch processing metrics
        self.batch_size = Histogram(
            'face_recognition_batch_size',
            'Size of processing batches',
            buckets=[1, 2, 4, 8, 16, 32, 64, 128],
            registry=self.registry
        )
        
        self.batch_processing_duration = Histogram(
            'face_recognition_batch_processing_duration_seconds',
            'Time spent processing batches',
            buckets=[1, 5, 10, 30, 60, 120, 300, 600],
            registry=self.registry
        )
        
        # API metrics
        self.http_requests_total = Counter(
            'face_recognition_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'face_recognition_http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            registry=self.registry
        )
    
    def track_file_upload(self, file_type: str):
        """Track file upload"""
        self.files_uploaded_total.labels(file_type=file_type).inc()
    
    def track_file_processing(self, file_type: str, status: str, duration: float):
        """Track file processing completion"""
        self.files_processed_total.labels(file_type=file_type, status=status).inc()
        self.file_processing_duration.labels(file_type=file_type).observe(duration)
    
    def track_face_detection(self, source_type: str, num_faces: int, duration: float, quality_scores: list):
        """Track face detection results"""
        self.faces_detected_total.labels(source_type=source_type).inc(num_faces)
        self.face_detection_duration.labels(source_type=source_type).observe(duration)
        
        for score in quality_scores:
            self.face_quality_score.observe(score)
    
    def track_search(self, cache_hit: bool, duration: float, num_results: int):
        """Track face search"""
        cache_status = 'hit' if cache_hit else 'miss'
        self.searches_total.labels(cache_status=cache_status).inc()
        self.search_duration.labels(cache_status=cache_status).observe(duration)
        self.search_results_count.observe(num_results)
    
    def track_cache_operation(self, operation: str, success: bool):
        """Track cache operations"""
        status = 'success' if success else 'failure'
        self.cache_operations_total.labels(operation=operation, status=status).inc()
    
    def update_cache_hit_ratio(self, hit_ratio: float):
        """Update cache hit ratio"""
        self.cache_hit_ratio.set(hit_ratio)
    
    def track_batch_processing(self, batch_size: int, duration: float):
        """Track batch processing"""
        self.batch_size.observe(batch_size)
        self.batch_processing_duration.observe(duration)
    
    def track_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Track HTTP request"""
        self.http_requests_total.labels(
            method=method, 
            endpoint=endpoint, 
            status_code=status_code
        ).inc()
        self.http_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    def update_system_metrics(self, active_tasks: Dict[str, int], db_connections: int, 
                            gpu_util: Optional[float] = None, memory_usage: Optional[Dict[str, int]] = None):
        """Update system metrics"""
        for task_type, count in active_tasks.items():
            self.active_tasks.labels(task_type=task_type).set(count)
        
        self.database_connections.set(db_connections)
        
        if gpu_util is not None:
            self.gpu_utilization.set(gpu_util)
        
        if memory_usage:
            for mem_type, usage in memory_usage.items():
                self.memory_usage.labels(type=mem_type).set(usage)
    
    def get_metrics(self):
        """Get all metrics in Prometheus format"""
        if self.registry:
            return generate_latest(self.registry)
        else:
            from prometheus_client import generate_latest as default_generate_latest
            return default_generate_latest()


# Global metrics instance
metrics = MetricsCollector()


# Decorator for timing function execution
def timed_function(metric_name: str = None, labels: Dict[str, str] = None):
    """Decorator to time function execution and record metrics"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record successful execution
                if metric_name:
                    histogram = getattr(metrics, metric_name, None)
                    if histogram and labels:
                        histogram.labels(**labels).observe(duration)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                # Record failed execution
                if metric_name:
                    histogram = getattr(metrics, metric_name, None)
                    if histogram and labels:
                        error_labels = {**labels, 'status': 'error'}
                        histogram.labels(**error_labels).observe(duration)
                
                raise
        return wrapper
    return decorator


# Context manager for timing operations
class TimedOperation:
    """Context manager for timing operations"""
    
    def __init__(self, metric_name: str, labels: Dict[str, str] = None):
        self.metric_name = metric_name
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        # Get the metric and record the duration
        histogram = getattr(metrics, self.metric_name, None)
        if histogram:
            final_labels = self.labels.copy()
            if exc_type is not None:
                final_labels['status'] = 'error'
            else:
                final_labels['status'] = 'success'
            
            histogram.labels(**final_labels).observe(duration)


# GPU monitoring utility
def get_gpu_utilization():
    """Get GPU utilization if available"""
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        info = pynvml.nvmlDeviceGetUtilizationRates(handle)
        return info.gpu
    except:
        return None


# Memory monitoring utility
def get_memory_usage():
    """Get memory usage information"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            'rss': memory_info.rss,
            'vms': memory_info.vms
        }
    except:
        return None

