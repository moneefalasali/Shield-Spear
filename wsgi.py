"""WSGI entrypoint for Gunicorn with Gevent WebSocket and auto DB init."""

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

        # إنشاء مستخدم admin عند أول تشغيل
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

# تهيئة قاعدة البيانات
init_database()

# هذا هو التطبيق الذي سيخدمه Gunicorn
application = app
