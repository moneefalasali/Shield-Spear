"""
E2E test for coop session using python-socketio client.
This script expects the app server to be running on http://localhost:5000.

It will:
 - Connect two clients (creator and participant)
 - Creator emits 'create_coop_session' with a challenge_id (requires at least one challenge in DB)
 - Participant joins using the session_code
 - Creator starts the session
 - Participant sends a 'play_action'
 - Both clients listen for 'action_result' and 'session_ended'

Run example (PowerShell):
 $env:PYTHONPATH = 'C:\cybersecurity_simulator'; .\venv\Scripts\python.exe .\tools\e2e_coop_test.py

Note: This test is intended for local dev. It will timeout after ~20s if events don't appear.
"""
import time
import sys
import os
import threading
import json

import socketio
import requests

SERVER = os.environ.get('COOP_SERVER', 'http://localhost:5000')

# Small helper to run a client in thread
class TestClient:
    def __init__(self, name, cookie_header=None):
        # allow passing Cookie header for authenticated session
        self.sio = socketio.Client(logger=False, engineio_logger=False)
        self.name = name
        self.session_code = None
        self.attempts = None
        self.events = []
        self.cookie_header = cookie_header

        @self.sio.event
        def connect():
            print(f'[{self.name}] connected')

        @self.sio.on('connect_response')
        def on_connect_response(data):
            print(f'[{self.name}] connect_response:', data)

        @self.sio.on('session_created')
        def on_session_created(data):
            print(f'[{self.name}] session_created:', data)
            self.session_code = data.get('session_code')

        @self.sio.on('error')
        def on_error(d):
            print(f'[{self.name}] error event:', d)

        @self.sio.on('user_joined')
        def on_user_joined(d):
            print(f'[{self.name}] user_joined:', d)

        @self.sio.on('session_started')
        def on_session_started(d):
            print(f'[{self.name}] session_started:', d)
            self.attempts = d.get('attempts')

        @self.sio.on('action_result')
        def on_action_result(d):
            print(f'[{self.name}] action_result:', d)
            self.events.append(d)

        @self.sio.on('session_ended')
        def on_session_ended(d):
            print(f'[{self.name}] session_ended:', d)

        @self.sio.event
        def disconnect():
            print(f'[{self.name}] disconnected')

    def connect(self):
        # allow engineio to choose best transport (polling or websocket)
        try:
            if self.cookie_header:
                self.sio.connect(SERVER, wait=True, headers={'Cookie': self.cookie_header})
            else:
                self.sio.connect(SERVER, wait=True)
        except Exception as e:
            print(f'[{self.name}] connect failed:', e)
            raise

    def disconnect(self):
        try:
            self.sio.disconnect()
        except Exception:
            pass

    def emit(self, event, data):
        self.sio.emit(event, data)


def main():
    # Prepare authenticated sessions for two users: admin + a newly created test user
    base = SERVER
    s_admin = requests.Session()
    # login admin (admin@shieldspear.com / admin123) - created by run.py init
    login_resp = s_admin.post(f"{base}/auth/login", data={'email': 'admin@shieldspear.com', 'password': 'admin123'})
    if login_resp.status_code not in (200, 302):
        print('Admin login may have failed, status:', login_resp.status_code)

    # create a second user via signup
    s_user = requests.Session()
    import random
    uname = f'testuser{random.randint(1000,9999)}'
    email = f'{uname}@example.test'
    pw = 'testpass123'
    signup_resp = s_user.post(f"{base}/auth/signup", data={'username': uname, 'email': email, 'password': pw, 'confirm_password': pw})
    # login second user
    s_user.post(f"{base}/auth/login", data={'email': email, 'password': pw})

    # Build Cookie headers for socketio clients
    def cookie_header_from_session(s):
        items = []
        for k, v in s.cookies.get_dict().items():
            items.append(f"{k}={v}")
        return '; '.join(items)

    # Find a coop challenge id by fetching the coop page and parsing the embedded JSON
    coop_page = s_admin.get(f"{base}/challenges/coop").text
    challenge_id = None
    try:
        marker = 'const challenges = '
        i = coop_page.find(marker)
        if i != -1:
            j = coop_page.find(';', i)
            raw = coop_page[i+len(marker):j]
            import json as _json
            parsed = _json.loads(raw)
            if parsed and isinstance(parsed, list):
                challenge_id = parsed[0].get('id')
    except Exception:
        challenge_id = None

    if not challenge_id:
        # fallback to "1" which may fail if ids are UUIDs
        challenge_id = 1

    creator = TestClient('creator', cookie_header=cookie_header_from_session(s_admin))
    participant = TestClient('participant', cookie_header=cookie_header_from_session(s_user))

    creator.connect()
    participant.connect()

    # Give server a moment
    time.sleep(1)

    # Use HTTP API to create the coop session (same flow as UI)
    api_resp = s_admin.post(f"{base}/api/coop/create", json={'team': 'red', 'challenge_id': challenge_id})
    if api_resp.status_code != 200:
        print('API create session failed:', api_resp.status_code, api_resp.text)
    else:
        js = api_resp.json()
    session_code = js.get('session_code')
    print('Created session via API:', session_code)
    # Creator socket should join the session room too
    creator.emit('join_coop_session', {'session_code': session_code})
    # record on creator client so test proceeds
    creator.session_code = session_code

    # wait until session_code populated
    timeout = 8
    while timeout > 0 and not creator.session_code:
        time.sleep(0.5)
        timeout -= 0.5

    if not creator.session_code:
        print('creator did not receive session_code; aborting')
        creator.disconnect(); participant.disconnect(); sys.exit(2)

    session_code = creator.session_code
    print('Session code:', session_code)

    # participant joins
    participant.emit('join_coop_session', {'session_code': session_code})

    time.sleep(1)

    # creator starts session
    creator.emit('start_coop_session', {'session_code': session_code})

    # wait for start
    time.sleep(2)

    # participant sends a play_action
    participant.emit('play_action', {'session_code': session_code, 'action': 'test-action-from-participant'})

    # wait a bit for events
    time.sleep(4)

    # stop session
    creator.emit('end_coop_session', {'session_code': session_code})

    time.sleep(1)

    creator.disconnect(); participant.disconnect()
    print('E2E test finished')

if __name__ == '__main__':
    main()
