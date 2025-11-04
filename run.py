#!/usr/bin/env python3
"""
Shield & Spear - Cybersecurity Training Platform
Database Initialization Script for Hosting
"""

import os
from app import create_app
from app.models import db, User, Challenge
from app.init_challenges import get_challenges

# Create Flask app
app = create_app()

def init_database():
    """Initialize database with admin user and pre-built challenges"""
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        
        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@shieldspear.com',
                full_name='System Administrator',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("✓ Created admin user: admin / admin123")
        else:
            print("✓ Admin user already exists")
        
        # Add pre-built challenges
        challenges_data = get_challenges()
        added_count = 0
        for challenge_data in challenges_data:
            existing = Challenge.query.filter_by(title=challenge_data['title']).first()
            if not existing:
                challenge = Challenge(**challenge_data)
                db.session.add(challenge)
                added_count += 1
        
        db.session.commit()
        print(f"✓ Database initialized with {added_count} new challenges")
        print(f"✓ Total challenges in database: {Challenge.query.count()}")

if __name__ == '__main__':
    print("🔹 Initializing database for hosting...")
    init_database()
    print("✅ Database initialization completed. Ready for deployment.")
