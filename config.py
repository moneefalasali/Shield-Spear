"""
Configuration file for Cybersecurity Simulator
"""
import os
from datetime import timedelta
# Use NullPool under eventlet/gevent workers to avoid threading/Condition notify
# errors with SQLAlchemy's QueuePool when the runtime is monkey-patched.
from sqlalchemy.pool import NullPool

class Config:
    """Base configuration"""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    # Database (use DATABASE_URL env var in production e.g. Render Postgres)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///cybersecurity_simulator.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Upload
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # WebSocket / Socket.IO message queue (use REDIS_URL or SOCKETIO_MESSAGE_QUEUE)
    SOCKETIO_MESSAGE_QUEUE = os.environ.get('SOCKETIO_MESSAGE_QUEUE') or os.environ.get('REDIS_URL')

    # SQLAlchemy engine options: use NullPool in this app to avoid
    # threading/Condition errors when running under eventlet (Gunicorn
    # eventlet worker). NullPool disables connection pooling and is a
    # safe default for single-instance deployments like Render. If you
    # scale to multiple workers or need pooling, consider changing this
    # to a pooled strategy and provisioning Redis/other queueing.
    SQLALCHEMY_ENGINE_OPTIONS = {
        'poolclass': NullPool,
        # 'pool_pre_ping': True,  # uncomment if you want pre-ping connection checks
    }
    
    # Docker settings
    DOCKER_ENABLED = False
    DOCKER_IMAGE = 'cybersec-simulator:latest'
    DOCKER_TIMEOUT = 30

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
