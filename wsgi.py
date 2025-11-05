"""WSGI entrypoint for Gunicorn with Gevent WebSocket and auto DB init."""

import os
import gevent.monkey
gevent.monkey.patch_all()

from app import create_app, socketio
from app.models import db, User, Challenge
from app.init_challenges import get_challenges

# إنشاء تطبيق Flask
app = create_app()

def init_database():
    """Initialize database with default admin and demo challenges."""
    with app.app_context():
        db.create_all()

        if User.query.count() == 0:
            admin = User(
                username='admin',
                email='admin@shieldspear.com',
                full_name='System Administrator',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)

            # إضافة التحديات التجريبية
            challenges = get_challenges()
            for c in challenges:
                db.session.add(Challenge(**c))

            db.session.commit()
            print(f"✓ Database initialized with admin user and {len(challenges)} demo challenges")
        else:
            print("✓ Database already initialized — skipping")

# تهيئة قاعدة البيانات عند التشغيل الأول
init_database()

# نقطة الدخول الرسمية لـ Gunicorn
# لا تستخدم socketio.WSGIApp بعد تحديث Flask-SocketIO
application = app

# لتشغيل محلي بدون Gunicorn
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
