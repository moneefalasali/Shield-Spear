#!/usr/bin/env python3
"""
Shield & Spear - Cybersecurity Training Platform
Local / Development Entrypoint
"""

import os
from app import create_app, socketio
from app.models import db, User, Challenge
from app.init_challenges import get_challenges

# إنشاء التطبيق
app = create_app()

def init_database():
    """Initialize database with admin user and demo challenges if empty"""
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

            challenges = get_challenges()
            for c in challenges:
                db.session.add(Challenge(**c))

            db.session.commit()
            print(f"✓ Database initialized with admin user and {len(challenges)} demo challenges")
        else:
            print("✓ Database already initialized — skipping")

# تهيئة قاعدة البيانات عند التشغيل المحلي
init_database()

# تشغيل محلي باستخدام socketio.run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting Shield & Spear locally on port {port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
