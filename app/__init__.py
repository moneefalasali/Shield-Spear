from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO
from config import config
from app.models import db, User
import os

login_manager = LoginManager()
socketio = SocketIO(async_mode='gevent')

def create_app(config_name='development'):
    """Application factory function"""
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # Load configuration
    if isinstance(config_name, str):
        config_obj = config.get(config_name, config['default'])
    else:
        config_obj = config_name
    
    app.config.from_object(config_obj)

    # Secret key for sessions
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.urandom(24)

    # Database configuration fallback
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shield_spear.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    # If a Redis URL is provided, use it as the message queue for Socket.IO
    message_queue = None
    if app.config.get('REDIS_URL'):
        message_queue = app.config.get('REDIS_URL')
    socketio.init_app(app, cors_allowed_origins="*", message_queue=message_queue)

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page'
    login_manager.login_message_category = 'error'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Register blueprints
    from app.routes import auth_bp, main_bp, challenges_bp, admin_bp, api_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(challenges_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Register Socket.IO event handlers (if available)
    try:
        from app.events import register_socketio_events
        register_socketio_events(socketio)
    except Exception:
        # If events module fails to load, continue without real-time handlers
        pass
    return app
