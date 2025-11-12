from flask_socketio import emit, join_room, leave_room, rooms
from flask_login import current_user
from app.models import db, CoopSession, Challenge, ChallengeAttempt
from app.challenge_simulator import challenge_simulator
from app.bot_ai import BotAI
from datetime import datetime
import string
import random
import time

def register_socketio_events(socketio):
    """Register all SocketIO events"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        if current_user.is_authenticated:
            emit('connect_response', {
                'data': 'Connected successfully',
                'user': current_user.username
            })

    # In-memory lightweight session state for live gameplay (kept per-process)
    # structure: { session_code: { 'scores': {user_id: score}, 'log': [], 'running': True, 'bot_threads': [] } }
    if not hasattr(socketio, 'sessions_state'):
        socketio.sessions_state = {}
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        pass
    
    @socketio.on('create_coop_session')
    def handle_create_coop_session(data):
        """Create a new cooperative session"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        challenge_id = data.get('challenge_id')
        mode = data.get('mode', 'cooperative')  # cooperative or competitive
        
        challenge = Challenge.query.get(challenge_id)
        if not challenge:
            emit('error', {'message': 'Challenge not found'})
            return
        
        # Generate session code
        session_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Create session
        coop_session = CoopSession(
            creator_id=current_user.id,
            challenge_id=challenge_id,
            session_code=session_code,
            creator_team=mode if mode in ('red','blue') else 'red',
            participants=[{'user_id': current_user.id, 'team': mode if mode in ('red','blue') else None}]
        )
        
        db.session.add(coop_session)
        db.session.commit()
        
        # Join room
        join_room(session_code)
        
        emit('session_created', {
            'session_code': session_code,
            'session_id': coop_session.id,
            'challenge_title': challenge.title,
            'mode': mode,
            'participants': [current_user.username]
        })

    def _start_session(coop_session):
        """Internal helper to start a session (extracted from handler)."""
        if not coop_session:
            return

        try:
            coop_session.status = 'in_progress'
            coop_session.started_at = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error starting session: {e}")
            return

        # Create a ChallengeAttempt for each participant and map them
        attempts_map = {}
        participants_user_map = {}
        participants = coop_session.participants or []
        for p in participants:
            if isinstance(p, dict):
                uid = p.get('user_id')
            else:
                uid = p
            try:
                attempt = ChallengeAttempt(
                    user_id=str(uid),
                    challenge_id=coop_session.challenge_id,
                    is_completed=False
                )
                db.session.add(attempt)
                db.session.flush()
                attempts_map[str(uid)] = attempt.id
                try:
                    user = __import__('app.models', fromlist=['User']).User.query.get(uid)
                    participants_user_map[str(uid)] = user.username if user else str(uid)
                except Exception as e:
                    print(f"Error getting username for {uid}: {e}")
                    participants_user_map[str(uid)] = str(uid)
            except Exception as e:
                print(f"Error creating attempt for {uid}: {e}")
                continue

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Notify all participants with mapping user_id -> attempt_id so each client can redirect
        emit('session_started', {
            'session_code': coop_session.session_code,
            'challenge_id': coop_session.challenge_id,
            'mode': getattr(coop_session, 'mode', coop_session.creator_team if hasattr(coop_session, 'creator_team') else 'cooperative'),
            'attempts': attempts_map,
            'participants': participants_user_map
        }, room=coop_session.session_code)

        # Initialize in-process session state (scores, log, hp, cooldowns)
        state = socketio.sessions_state.setdefault(coop_session.session_code, {})
        state.setdefault('scores', {})
        state.setdefault('log', [])
        state['running'] = True
        state.setdefault('hp_map', {})
        state.setdefault('cooldowns', {})

        def _extract_user_id(p):
            if isinstance(p, dict):
                return p.get('user_id')
            return p

        for p in (coop_session.participants or []):
            uid = _extract_user_id(p)
            state['scores'].setdefault(str(uid), 0)
            # init hp to full (100)
            state['hp_map'].setdefault(str(uid), 100)

        # persist initial hp_map and cooldowns on coop_session
        try:
            coop_session.hp_map = state.get('hp_map', {})
            coop_session.cooldowns = state.get('cooldowns', {})
            db.session.commit()
        except Exception:
            db.session.rollback()

        # If there are fewer than 2 human participants, spawn a simple bot to participate
        human_count = 0
        for p in (coop_session.participants or []):
            uid = _extract_user_id(p)
            if isinstance(uid, str) and uid.startswith('bot-'):
                continue
            human_count += 1

        if human_count < 2:
            bot_id = f"bot-{coop_session.session_code[:6]}"
            bot_name = f"Bot-{coop_session.session_code[:4]}"
            state['scores'].setdefault(bot_id, 0)
            state['hp_map'].setdefault(bot_id, 100)
            attempts_map[bot_id] = f"bot-attempt-{bot_id}"
            participants_user_map[bot_id] = bot_name

            def bot_loop():
                bot = BotAI(difficulty='medium', role='attacker')
                bot_state = {'bot_step': 0}
                while state.get('running'):
                    try:
                        challenge = coop_session.challenge
                        action = bot.get_next_action(challenge.challenge_type, bot_state)
                        payload = action.get('description', '')
                        try:
                            evaluate_and_record(coop_session.session_code, bot_id, bot_name, payload)
                        except Exception:
                            pass
                        bot_state['bot_step'] = bot_state.get('bot_step', 0) + 1
                        time.sleep(bot.get_reaction_delay())
                    except Exception:
                        break

            t = socketio.start_background_task(bot_loop)
            state.setdefault('bot_threads', []).append(t)
            # persist changes caused by bot addition
            try:
                coop_session.hp_map = state.get('hp_map', {})
                coop_session.cooldowns = state.get('cooldowns', {})
                db.session.commit()
            except Exception:
                db.session.rollback()
    
    @socketio.on('join_coop_session')
    def handle_join_coop_session(data):
        """Join an existing cooperative session"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        
        session_code = data.get('session_code')
        
        coop_session = CoopSession.query.filter_by(session_code=session_code).first()
        if not coop_session:
            emit('error', {'message': 'Session not found'})
            return
        
        if coop_session.status != 'waiting':
            emit('error', {'message': 'Session already started'})
            return
        
        # Add participant (use dict structure consistently and reassign so JSON change is detected)
        existing = coop_session.participants or []
        found = False
        for p in existing:
            if isinstance(p, dict) and p.get('user_id') == current_user.id:
                found = True
                break
        if not found:
            # append as dict with optional team
            new_part = {'user_id': current_user.id, 'team': None}
            coop_session.participants = existing + [new_part]
            db.session.commit()
        
        # Join room
        join_room(session_code)
        
        # Build participants list of usernames for readability
        def _extract_user_id(p):
            # participants may be stored as dicts like {'user_id':..., 'team':...} or raw ids
            if isinstance(p, dict):
                return p.get('user_id')
            return p

        participants_usernames = []
        for p in (coop_session.participants or []):
            uid = _extract_user_id(p)
            try:
                user = __import__('app.models', fromlist=['User']).User.query.get(uid)
                participants_usernames.append(user.username if user else str(uid))
            except Exception:
                participants_usernames.append(str(uid))

        # Notify all participants
        emit('user_joined', {
            'username': current_user.username,
            'participants': participants_usernames
        }, room=session_code)

        # If this session was created as competitive (creator_team 'red' or 'blue'), auto-assign teams
        try:
            if getattr(coop_session, 'creator_team', None) in ('red', 'blue') and coop_session.status == 'waiting':
                # ensure the joiner is assigned the opposite team
                for p in coop_session.participants:
                    if isinstance(p, dict) and p.get('user_id') == current_user.id:
                        p['team'] = 'blue' if coop_session.creator_team == 'red' else 'red'
                # persist
                coop_session.participants = coop_session.participants
                db.session.commit()
                # if we have 2 or more participants, auto-start PvP
                if len(coop_session.participants or []) >= 2:
                    _start_session(coop_session)
        except Exception:
            db.session.rollback()

    
    @socketio.on('start_coop_session')
    def handle_start_coop_session(data):
        """Start a cooperative session"""
        session_code = data.get('session_code')
        coop_session = CoopSession.query.filter_by(session_code=session_code).first()
        if not coop_session or coop_session.creator_id != current_user.id:
            emit('error', {'message': 'You do not have permission to start this session'})
            return
        # delegate to internal starter
        _start_session(coop_session)
    
    @socketio.on('submit_coop_solution')
    def handle_submit_coop_solution(data):
        """Submit solution in cooperative session"""
        session_code = data.get('session_code')
        solution = data.get('solution')
        
        coop_session = CoopSession.query.filter_by(session_code=session_code).first()
        if not coop_session:
            emit('error', {'message': 'Session not found'})
            return
        
        # coop_session.challenge may be None if an invalid challenge_id was stored (e.g. fallback 1)
        challenge = coop_session.challenge
        if challenge is None:
            try:
                # attempt to resolve the challenge explicitly
                challenge = __import__('app.models', fromlist=['Challenge']).Challenge.query.get(coop_session.challenge_id)
            except Exception:
                challenge = None

        if challenge is None:
            # nothing to evaluate against; record a no-op and return
            emit('error', {'message': 'The challenge associated with the session is missing — cannot perform action'}, room=session_code)
            return
        
        # Use realistic challenge simulator
        result = challenge_simulator.evaluate_challenge(
            challenge.challenge_type,
            solution,
            challenge.difficulty
        )
        
        # Create attempt record
        attempt = ChallengeAttempt(
            user_id=current_user.id,
            challenge_id=coop_session.challenge_id,
            user_input=solution,
            is_completed=True,
            completed_at=datetime.utcnow(),
            is_correct=result['success'],
            score=result['score'],
            feedback=result['feedback'],
            errors=result.get('errors', [])
        )
        
        db.session.add(attempt)
        db.session.commit()
        
        # Store result in session
        if not coop_session.results:
            coop_session.results = {}
        
        coop_session.results[current_user.id] = {
            'username': current_user.username,
            'is_correct': result['success'],
            'score': result['score'],
            'feedback': result['feedback'],
            'submitted_at': datetime.utcnow().isoformat()
        }
        
        db.session.commit()
        
        # Notify all participants
        emit('solution_submitted', {
            'username': current_user.username,
            'is_correct': result['success'],
            'score': result['score'],
            'feedback': result['feedback'],
            'results': coop_session.results
        }, room=session_code)

    def evaluate_and_record(session_code, actor_id, actor_name, payload, target_id=None):
        """Helper to evaluate a submitted action/payload and broadcast results."""
        coop_session = CoopSession.query.filter_by(session_code=session_code).first()
        if not coop_session:
            return

        # Resolve challenge object (guard against invalid challenge_id)
        challenge = coop_session.challenge
        if challenge is None:
            try:
                challenge = __import__('app.models', fromlist=['Challenge']).Challenge.query.get(coop_session.challenge_id)
            except Exception:
                challenge = None

        if challenge is None:
            # nothing to evaluate against; notify room and stop
            emit('error', {'message': 'The challenge associated with the session is missing — cannot perform action'}, room=session_code)
            return

        result = challenge_simulator.evaluate_challenge(
            challenge.challenge_type,
            payload,
            challenge.difficulty
        )

        # Build a lightweight record for in-memory state and optional DB logging
        record = {
            'actor_id': str(actor_id),
            'actor_name': actor_name,
            'payload': payload,
            'target_id': str(target_id) if target_id is not None else None,
            'is_correct': result['success'],
            'score': result['score'],
            'feedback': result['feedback'],
            'timestamp': datetime.utcnow().isoformat()
        }

        # Persist attempt record for both humans and bots (bots have ids like 'bot-...')
        try:
            attempt = ChallengeAttempt(
                user_id=str(actor_id),
                challenge_id=coop_session.challenge_id,
                user_input=payload,
                is_completed=True,
                completed_at=datetime.utcnow(),
                is_correct=result['success'],
                score=result['score'],
                feedback=result['feedback']
            )
            db.session.add(attempt)
            db.session.commit()
        except Exception:
            # don't fail the live flow on DB write issues
            db.session.rollback()

        # Update in-memory session state
        state = socketio.sessions_state.setdefault(session_code, {})
        scores = state.setdefault('scores', {})
        scores.setdefault(str(actor_id), 0)
        scores[str(actor_id)] += result.get('score', 0)
        state.setdefault('log', []).append(record)
        # ensure hp_map and cooldowns exist
        hp_map = state.setdefault('hp_map', {})
        cooldowns = state.setdefault('cooldowns', {})

        # Initialize actor hp if missing
        hp_map.setdefault(str(actor_id), 100)

        # Simple PvP mechanics: if session was competitive, apply damage to opponents on successful attack
        try:
            competitive = getattr(coop_session, 'creator_team', None) in ('red', 'blue')
        except Exception:
            competitive = False

        if competitive:
            # determine actor team
            actor_team = None
            for p in (coop_session.participants or []):
                if isinstance(p, dict) and str(p.get('user_id')) == str(actor_id):
                    actor_team = p.get('team')
                    break

            # choose targets: if explicit target_id provided use that, otherwise default to participants not on actor_team
            targets = []
            if target_id:
                # only target if present in participants and not self
                for p in (coop_session.participants or []):
                    uid = p.get('user_id') if isinstance(p, dict) else p
                    if str(uid) == str(target_id) and str(uid) != str(actor_id):
                        targets.append(str(uid))
                        break
            else:
                for p in (coop_session.participants or []):
                    uid = p.get('user_id') if isinstance(p, dict) else p
                    if str(uid) == str(actor_id):
                        continue
                    if actor_team and isinstance(p, dict) and p.get('team') and p.get('team') == actor_team:
                        continue
                    targets.append(str(uid))

            # damage amount based on score (fallback 10)
            dmg = int(result.get('score') or 10)
            if result.get('success'):
                for tid in targets:
                    hp_map.setdefault(tid, 100)
                    # remove up to min(20, dmg)
                    hp_map[tid] = max(0, hp_map[tid] - min(20, dmg))
            else:
                # failed action penalizes attacker a bit
                hp_map[str(actor_id)] = max(0, hp_map.get(str(actor_id), 100) - 8)

        # Set cooldown for actor (expiry timestamp)
        try:
            cooldown_seconds = 3
            cooldowns[str(actor_id)] = int(time.time()) + cooldown_seconds
        except Exception:
            pass

        # persist hp_map and cooldowns back to the CoopSession DB record so state survives process restarts
        try:
            coop_session.hp_map = hp_map
            coop_session.cooldowns = cooldowns
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Persist summary into coop_session.results for later retrieval
        if not coop_session.results:
            coop_session.results = {}
        coop_session.results[str(actor_id)] = {
            'username': actor_name,
            'is_correct': result['success'],
            'score': scores[str(actor_id)],
            'feedback': result['feedback'],
            'last_seen': datetime.utcnow().isoformat()
        }
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Broadcast action result and summary update
        emit('action_result', {
            'record': record,
            'scores': scores,
            'results': coop_session.results,
            'hp_map': hp_map,
            'cooldowns': cooldowns
        }, room=session_code)

        # Also send a compact session update for UI
        emit('session_update', {
            'scores': scores,
            'recent': record,
            'hp_map': hp_map,
            'cooldowns': cooldowns
        }, room=session_code)

        # If any player reached 0 HP, end the session and declare winner(s)
        try:
            losers = [k for k,v in (hp_map or {}).items() if v <= 0]
            if losers:
                coop_session.status = 'completed'
                coop_session.completed_at = datetime.utcnow()
                try:
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                # prepare results and emit session_ended
                emit('session_ended', {
                    'results': coop_session.results,
                    'hp_map': hp_map,
                    'losers': losers,
                    'mode': getattr(coop_session, 'mode', coop_session.creator_team if hasattr(coop_session, 'creator_team') else None)
                }, room=session_code)
                # mark running false so bots/loops exit
                state['running'] = False
        except Exception:
            pass

    @socketio.on('play_action')
    def handle_play_action(data):
        """Receive an in-game action from a connected client."""
        if not current_user.is_authenticated:
            emit('error', {'message': 'يجب تسجيل الدخول أولاً'})
            return

        session_code = data.get('session_code')
        action_payload = data.get('action')
        if not session_code or action_payload is None:
            emit('error', {'message': 'Invalid action data'})
            return

        # parse optional target id from payload if present
        target_id = None
        try:
            # expected payload format: actionType|actorId|targetId|timestamp
            parts = (action_payload or '').split('|')
            if len(parts) >= 4:
                maybe_target = parts[2]
                if maybe_target and maybe_target.strip() != '':
                    target_id = maybe_target
        except Exception:
            target_id = None

        # Call helper to evaluate and broadcast (pass target_id when available)
        try:
            evaluate_and_record(session_code, current_user.id, current_user.username, action_payload, target_id=target_id)
        except Exception as e:
            # log exception for debugging and return a more informative error to the client
            import traceback
            traceback.print_exc()
            emit('error', {'message': f'Failed to execute action: {str(e)}'})
            return
    
    @socketio.on('end_coop_session')
    def handle_end_coop_session(data):
        """End a cooperative session"""
        session_code = data.get('session_code')
        
        coop_session = CoopSession.query.filter_by(session_code=session_code).first()
        if not coop_session:
            emit('error', {'message': 'Session not found'})
            return
        
        coop_session.status = 'completed'
        coop_session.completed_at = datetime.utcnow()
        db.session.commit()
        # mark session state as stopped so threads can exit
        state = getattr(socketio, 'sessions_state', {}).get(session_code)
        if state:
            state['running'] = False

        # Notify all participants
        emit('session_ended', {
            'results': coop_session.results,
            'mode': getattr(coop_session, 'mode', coop_session.creator_team if hasattr(coop_session, 'creator_team') else None)
        }, room=session_code)
        
        leave_room(session_code)

