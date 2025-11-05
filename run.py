#!/usr/bin/env python3
"""
Shield & Spear - Cybersecurity Training Platform
Production Entrypoint for Render
"""

import os
from app import create_app, socketio
from app.models import db, User, Challenge
from app.init_challenges import get_challenges

# إنشاء التطبيق
app = create_app()

def init_database():
    """Initialize database with admin user and pre-built challenges (only if empty)"""
    with app.app_context():
        db.create_all()

        # تأكد أن التهيئة تتم مرة واحدة فقط
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

            # أضف التحديات
            challenges_data = get_challenges()
            for c in challenges_data:
                challenge = Challenge(**c)
                db.session.add(challenge)
            db.session.commit()
            print(f"✓ Added {len(challenges_data)} challenges")
        else:
            print("✓ Database already initialized — skipping seeding")

# تهيئة قاعدة البيانات مرة واحدة
init_database()

# تشغيل التطبيق على Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Starting Shield & Spear on port {port} (Render Production Mode)")
    socketio.run(app, host="0.0.0.0", port=port)
