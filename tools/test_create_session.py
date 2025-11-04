from app import create_app
from app.models import db, User
import json

app = create_app()
with app.app_context():
    client = app.test_client()
    # initialize db if needed
    db.create_all()
    # Ensure admin exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@shieldspear.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

    # Log in
    login_resp = client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    print('Login status code:', login_resp.status_code)

    # Create coop session
    resp = client.post('/api/coop/create', json={'team': 'red'})
    print('Create session status:', resp.status_code)
    try:
        print('Response JSON:', resp.get_json())
    except Exception:
        print('Response data:', resp.data)
