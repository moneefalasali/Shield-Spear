"""WSGI entrypoint for Gunicorn with eventlet.

This module applies eventlet monkey patching before importing the
application so that sockets and threading are patched correctly.
It exposes the variable `application` which is the WSGI app that
Gunicorn should serve.
"""

try:
    import eventlet
    eventlet.monkey_patch()
except Exception:
    # If eventlet isn't available in some environments, continue anyway.
    pass

from app import create_app, socketio

# Create the Flask app using the factory
app = create_app()

# Expose the Socket.IO WSGI application for Gunicorn
application = socketio.WSGIApp(app)
