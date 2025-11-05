"""WSGI entrypoint for Gunicorn with Gevent WebSocket."""
import gevent.monkey
gevent.monkey.patch_all()

import os
from app import create_app, socketio
from app.models import db, User, Challenge
from app.init_challenges import get_challenges

# إنشاء التطبيق
app = create_app()

def init_database():
    """Initialize database with default admin and demo challenges."""
    with app.app_context():
        db.create_all()

        # إذا لم يكن هناك مستخدمين، أضف المستخدم والتحديات
        if User.query.count() == 0:
            admin = User(
                username='admin',
                email='admin@shieldspear.com',
                full_name='System Administrator',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("✓ Created admin user: admin / admin123")

            # إضافة التحديات التجريبية
            challenges = get_challenges()
            for c in challenges:
                db.session.add(Challenge(**c))
            db.session.commit()
            print(f"✓ Added {len(challenges)} demo challenges")

        else:
            print("✓ Database already initialized, skipping seeding")

# تهيئة قاعدة البيانات
init_database()

# التطبيق الذي سيخدمه Gunicorn
application = socketio.WSGIApp(app)
