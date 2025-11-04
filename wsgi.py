"""WSGI entrypoint for Gunicorn with Gevent WebSocket."""

import gevent.monkey
gevent.monkey.patch_all()

from app import create_app, socketio

# Create the Flask app using the factory
app = create_app()

# Expose the Socket.IO WSGI application for Gunicorn
application = socketio.WSGIApp(app)
