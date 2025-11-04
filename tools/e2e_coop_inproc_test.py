"""
In-process E2E test using Flask-SocketIO test_client and Flask test_client.
This avoids network/socket transport issues and exercises the socket handlers directly.
Run with:
 $env:PYTHONPATH = 'C:\cybersecurity_simulator'; .\venv\Scripts\python.exe .\tools\e2e_coop_inproc_test.py
"""
from app import create_app, socketio
from app.models import db
import time

app = create_app()

def make_user_and_login(test_client, username, email, password):
    # try to signup; if exists, ignore
    test_client.post('/auth/signup', data={'username': username, 'email': email, 'password': password, 'confirm_password': password})
    resp = test_client.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=True)
    return resp.status_code


def main():
    with app.app_context():
        # create two flask test clients and login
        admin_client = app.test_client()
        user_client = app.test_client()

        # admin exists (created by run.py init), ensure admin password
        make_user_and_login(admin_client, 'admin', 'admin@shieldspear.com', 'admin123')

        import random
        uname = f'testuser{random.randint(1000,9999)}'
        email = f'{uname}@example.test'
        pw = 'testpass123'
        # create user directly in DB to avoid signup redirect complexities
        from app.models import User
        new_user = User(username=uname, email=email)
        new_user.set_password(pw)
        db.session.add(new_user)
        db.session.commit()
        # login via user_client
        user_client.post('/auth/login', data={'email': email, 'password': pw}, follow_redirects=True)

        # create socketio test clients that reuse the flask test clients (so session/cookie flows work)
        sio_creator = socketio.test_client(app, flask_test_client=admin_client)
        sio_participant = socketio.test_client(app, flask_test_client=user_client)

        print('Creator connected:', sio_creator.is_connected())
        print('Participant connected:', sio_participant.is_connected())

        # Create a coop session via HTTP API (ensures DB entry exists)
        resp = admin_client.post('/api/coop/create', json={'challenge_id': 1})
        print('Create session resp status:', resp.status_code, 'data:', resp.get_data(as_text=True))
        if resp.status_code != 200:
            print('Failed to create session via API')
            return
        data = resp.get_json()
        session_code = data.get('session_code')
        print('session_code (from API):', session_code)

        # Both clients join via socket so they join the session room
        sio_creator.emit('join_coop_session', {'session_code': session_code})
        sio_participant.emit('join_coop_session', {'session_code': session_code})
        time.sleep(0.3)
        print('Creator received after join:', sio_creator.get_received())
        print('Participant received after join:', sio_participant.get_received())
        # inspect DB to confirm participants were added
        from app.models import CoopSession as CoopModel
        cs = CoopModel.query.filter_by(session_code=session_code).first()
        print('DB coop_session participants:', cs.participants if cs else None)

        # Creator starts the session
        sio_creator.emit('start_coop_session', {'session_code': session_code})
        time.sleep(0.5)
        print('Creator received after start:', sio_creator.get_received())
        print('Participant received after start:', sio_participant.get_received())

        # Participant sends play_action
        sio_participant.emit('play_action', {'session_code': session_code, 'action': 'inproc-action-1'})
        time.sleep(0.5)
        print('Participant events:', sio_participant.get_received())
        print('Creator events:', sio_creator.get_received())

        # End session
        sio_creator.emit('end_coop_session', {'session_code': session_code})
        time.sleep(0.3)
        print('After end, creator:', sio_creator.get_received())
        print('After end, participant:', sio_participant.get_received())

        sio_creator.disconnect()
        sio_participant.disconnect()

if __name__ == '__main__':
    main()
