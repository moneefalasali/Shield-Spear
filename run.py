#!/usr/bin/env python3
"""
Shield & Spear - Cybersecurity Training Platform
Main Application Entry Point
"""

import os
import sys
from app import create_app, socketio
from app.models import db, User, Challenge
from app.init_challenges import get_challenges

# Create Flask app
app = create_app()

def init_database():
    """Initialize database with admin user and challenges"""
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if admin user exists
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
    # Initialize database
    init_database()
    
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║       Shield & Spear - Cybersecurity Training Platform        ║
    ║                                                                ║
    ║   Server running on: http://localhost:{port}                    ║
    ║   Admin credentials: admin / admin123                         ║
    ║                                                                ║
    ║   Features:                                                   ║
    ║   ✓ 5 Pre-built Challenges (Attack & Defense)               ║
    ║   ✓ AI Bot Opponent with 3 Difficulty Levels               ║
    ║   ✓ Co-op Mode with Invite Codes                            ║
    ║   ✓ Real-time Event Logs                                    ║
    ║   ✓ Full Admin Panel                                        ║
    ║                                                                ║
    ║   Press Ctrl+C to stop the server                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)
