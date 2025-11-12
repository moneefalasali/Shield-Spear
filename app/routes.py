from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Challenge, ChallengeAttempt, CoopSession, AdminLog
from app.challenge_engine import challenge_engine
from app.bot_ai import BotAI
from datetime import datetime
import uuid
import string
import random
import json
import traceback

# Create blueprints
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
main_bp = Blueprint('main', __name__)
challenges_bp = Blueprint('challenges', __name__, url_prefix='/challenges')
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
api_bp = Blueprint('api', __name__, url_prefix='/api')

# ==================== AUTH ROUTES ====================

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required', 'error')
            return redirect(url_for('auth.signup'))
        
        if len(username) < 3:
            flash('Username must be at least 3 characters', 'error')
            return redirect(url_for('auth.signup'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('auth.signup'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('auth.signup'))
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('auth.signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('auth.signup'))
        
        # Create new user
        user = User(username=username, email=email, full_name=full_name)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! Please log in', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        # Accept either username or email from the login form.
        identifier = (request.form.get('username') or request.form.get('email') or '').strip()
        password = request.form.get('password', '')

        # Try lookup by username first, then by email. If identifier looks like an email, normalize it.
        user = None
        if identifier:
            # If it contains an @, treat it as email and lowercase for lookup
            if '@' in identifier:
                user = User.query.filter_by(email=identifier.lower()).first()
            else:
                user = User.query.filter_by(username=identifier).first()
                if not user:
                    # fallback: try email too (user may have entered email without @ due to input error)
                    user = User.query.filter_by(email=identifier.lower()).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully', 'success')
            return redirect(url_for('main.dashboard'))

        flash('Invalid username or password', 'error')
        return redirect(url_for('auth.login'))

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """Log out the current user and redirect to the public home page."""
    try:
        logout_user()
    except Exception:
        # If logout fails for any reason, ignore and redirect
        pass
    flash('Logged out successfully', 'success')
    return redirect(url_for('main.index'))
@main_bp.route('/')
def index():
    """Public home page (accessible without login)."""
    return render_template('index.html')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard after login (shows Check Trials button)"""
    user_score = current_user.get_total_score()
    user_rank = current_user.get_rank()
    return render_template('dashboard.html', user_score=user_score, user_rank=user_rank)

@main_bp.route('/trials')
@login_required
def trials():
    """Trials selection page - Choose category (Blue/Red/Co-op)"""
    return render_template('trials.html')

@main_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    attempts = ChallengeAttempt.query.filter_by(user_id=current_user.id, is_completed=True).order_by(ChallengeAttempt.completed_at.desc()).all()
    total_score = current_user.get_total_score()
    rank = current_user.get_rank()
    
    return render_template('profile.html', 
                         attempts=attempts,
                         total_score=total_score,
                         rank=rank)

@main_bp.route('/leaderboard')
def leaderboard():
    """Leaderboard page"""
    category_filter = request.args.get('category', 'all')
    
    users = User.query.all()
    leaderboard_data = []
    
    for user in users:
        if category_filter == 'all':
            score = user.get_total_score()
        else:
            # Filter by category
            attempts = ChallengeAttempt.query.join(Challenge).filter(
                ChallengeAttempt.user_id == user.id,
                ChallengeAttempt.is_completed == True,
                Challenge.category == category_filter
            ).all()
            score = sum(a.score for a in attempts)
        
        if score > 0:
            leaderboard_data.append({
                'user': user,
                'score': score
            })
    
    leaderboard_data.sort(key=lambda x: x['score'], reverse=True)
    
    return render_template('leaderboard.html', 
                         leaderboard=leaderboard_data,
                         category=category_filter)

# ==================== CHALLENGE ROUTES ====================

@challenges_bp.route('/blue')
@login_required
def blue_challenges():
    """Blue Team (Defender) challenges"""
    challenges = Challenge.query.filter_by(category='blue', is_active=True).all()
    # Serialize Challenge objects to JSON-serializable dicts for templates that use |tojson
    challenges_serialized = [c.to_dict() for c in challenges]
    return render_template('blue.html', challenges=challenges_serialized)

@challenges_bp.route('/red')
@login_required
def red_challenges():
    """Red Team (Attacker) challenges"""
    challenges = Challenge.query.filter_by(category='red', is_active=True).all()
    challenges_serialized = [c.to_dict() for c in challenges]
    return render_template('red.html', challenges=challenges_serialized)

@challenges_bp.route('/coop')
@login_required
def coop_challenges():
    """Co-op challenges"""
    challenges = Challenge.query.filter_by(category='coop', is_active=True).all()
    challenges_serialized = [c.to_dict() for c in challenges]
    return render_template('coop.html', challenges=challenges_serialized)

@challenges_bp.route('/<challenge_id>/start', methods=['POST'])
@login_required
def start_challenge(challenge_id):
    """Start a challenge and create attempt"""
    challenge = Challenge.query.get(challenge_id)
    if not challenge:
        return jsonify({'error': 'Challenge not found'}), 404
    
    # Create attempt record
    attempt = ChallengeAttempt(
        user_id=current_user.id,
        challenge_id=challenge_id
    )
    db.session.add(attempt)
    db.session.commit()
    
    # Initialize bot for this challenge
    bot_role = 'defender' if challenge.category == 'red' else 'attacker'
    bot = BotAI(difficulty=challenge.difficulty, role=bot_role)
    
    # Store bot config in session for this attempt
    session[f'bot_{attempt.id}'] = {
        'difficulty': challenge.difficulty,
        'role': bot_role,
        'step': 0
    }
    
    return jsonify({
        'success': True,
        'attempt_id': attempt.id,
        'redirect_url': url_for('challenges.play_challenge', attempt_id=attempt.id)
    })

@challenges_bp.route('/play/<attempt_id>')
@login_required
def play_challenge(attempt_id):
    """Interactive challenge gameplay page"""
    attempt = ChallengeAttempt.query.get(attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        flash('Invalid challenge attempt', 'error')
        return redirect(url_for('main.trials'))
    
    if attempt.is_completed:
        return redirect(url_for('challenges.result', attempt_id=attempt_id))
    
    challenge = attempt.challenge
    return render_template('play.html', attempt=attempt, challenge=challenge)

@challenges_bp.route('/play/<attempt_id>/submit', methods=['POST'])
@login_required
def submit_solution(attempt_id):
    """Submit challenge solution"""
    attempt = ChallengeAttempt.query.get(attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        return jsonify({'error': 'Invalid attempt'}), 404
    
    data = request.get_json() or {}
    user_input = data.get('solution', '').strip()
    
    if not user_input:
        return jsonify({'error': 'Solution cannot be empty'}), 400
    
    challenge = attempt.challenge
    
    # Determine role
    role = 'attacker' if challenge.category == 'red' else 'defender'
    
    # Evaluate solution
    result = challenge_engine.evaluate_challenge(
        challenge.challenge_type,
        user_input,
        challenge.difficulty,
        role
    )
    
    # Calculate time taken
    time_taken = int((datetime.utcnow() - attempt.started_at).total_seconds())
    
    # Get bot actions (simulate bot playing against user)
    bot_role = 'defender' if role == 'attacker' else 'attacker'
    bot = BotAI(difficulty=challenge.difficulty, role=bot_role)
    
    bot_actions = []
    for i in range(3):  # Bot makes 3-4 actions
        bot_action = bot.get_next_action(challenge.challenge_type, {'bot_step': i})
        bot_actions.append(bot_action)
    
    # Update attempt
    attempt.user_input = user_input
    attempt.is_correct = result['success']
    attempt.score = result['score']
    attempt.feedback = result['feedback']
    attempt.mistakes = result.get('details', {})
    attempt.corrections = result.get('corrections', {})
    attempt.bot_actions = bot_actions
    attempt.time_taken = time_taken
    attempt.is_completed = True
    attempt.completed_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'result': result,
        'bot_actions': bot_actions,
        'redirect_url': url_for('challenges.result', attempt_id=attempt_id)
    })

@challenges_bp.route('/result/<attempt_id>')
@login_required
def result(attempt_id):
    """Show challenge result"""
    attempt = ChallengeAttempt.query.get(attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        flash('Invalid challenge attempt', 'error')
        return redirect(url_for('main.trials'))
    
    challenge = attempt.challenge
    return render_template('result.html', attempt=attempt, challenge=challenge)

# ==================== CO-OP ROUTES ====================

@api_bp.route('/coop/create', methods=['POST'])
@login_required
def create_coop_session():
    """Create a new co-op session"""
    try:
        data = request.get_json() or {}
        creator_team = data.get('team', 'red')  # red or blue
        challenge_id = data.get('challenge_id')

        # If a challenge_id was provided, ensure it exists; otherwise pick a default coop challenge
        if challenge_id:
            challenge = Challenge.query.get(challenge_id)
            if not challenge:
                # fallback to a default active coop challenge
                challenge = Challenge.query.filter_by(category='coop', is_active=True).first()
                if not challenge:
                    return jsonify({'error': 'No co-op challenges available'}), 404
                challenge_id = challenge.id
        else:
            # Get default coop challenge
            challenge = Challenge.query.filter_by(category='coop', is_active=True).first()
            if not challenge:
                return jsonify({'error': 'No co-op challenges available'}), 404
            challenge_id = challenge.id

        # Generate unique session code
        session_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        while CoopSession.query.filter_by(session_code=session_code).first():
            session_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Create session
        coop_session = CoopSession(
            creator_id=current_user.id,
            challenge_id=challenge_id,
            session_code=session_code,
            creator_team=creator_team,
            participants=[{'user_id': current_user.id, 'team': creator_team}],
            event_log=[]
        )

        db.session.add(coop_session)
        db.session.commit()

        # Generate shareable link
        invite_link = url_for('api.join_coop_session', session_code=session_code, _external=True)

        return jsonify({
            'success': True,
            'session_id': coop_session.id,
            'session_code': session_code,
            'invite_link': invite_link,
            'creator_team': creator_team
        })
    except Exception as e:
        # Log traceback for debugging and return JSON error in dev
        tb = traceback.format_exc()
        try:
            current_app.logger.error('Error in create_coop_session:\n%s', tb)
        except Exception:
            # if current_app isn't available, print to stderr
            print(tb)
        return jsonify({'success': False, 'error': 'Internal server error', 'details': str(e)}), 500

@api_bp.route('/coop/join/<session_code>', methods=['GET', 'POST'])
@login_required
def join_coop_session(session_code):
    """Join an existing co-op session"""
    try:
        coop_session = CoopSession.query.filter_by(session_code=session_code).first()
        
        if not coop_session:
            if request.method == 'POST':
                return jsonify({'error': 'Session not found'}), 404
            flash('Session not found', 'error')
            return redirect(url_for('main.trials'))
        
        if coop_session.status == 'completed':
            flash('This session has already ended', 'error')
            return redirect(url_for('main.trials'))
        
        # Check if user already in session
        participants = coop_session.participants or []
        user_in_session = any(p['user_id'] == current_user.id for p in participants)
        
        if not user_in_session:
            if len(participants) >= 2:
                flash('Session is full', 'error')
                return redirect(url_for('main.trials'))
            
            # Assign opposite team
            opponent_team = 'blue' if coop_session.creator_team == 'red' else 'red'
            participants.append({'user_id': current_user.id, 'team': opponent_team})
            coop_session.participants = participants
            coop_session.status = 'in_progress'
            coop_session.started_at = datetime.utcnow()
            db.session.commit()
        
        if request.method == 'POST':
            return jsonify({'success': True, 'redirect_url': url_for('challenges.play_coop', session_id=coop_session.id)})
        
        return redirect(url_for('challenges.play_coop', session_id=coop_session.id))
    except Exception as e:
        tb = traceback.format_exc()
        current_app.logger.error('Error in join_coop_session:\n%s', tb)
        if request.method == 'POST':
            return jsonify({'success': False, 'error': 'Internal server error', 'details': str(e)}), 500
        flash('Internal server error occurred while joining session.', 'error')
        return redirect(url_for('main.trials'))

@challenges_bp.route('/coop/play/<session_id>')
@login_required
def play_coop(session_id):
    """Play co-op challenge"""
    coop_session = CoopSession.query.get(session_id)
    if not coop_session:
        flash('Session not found', 'error')
        return redirect(url_for('main.trials'))
    
    # Allow access to the session page regardless of participation status.
    # The SocketIO logic in events.py will handle adding the user as a participant.
    # The original check was:
    # participants = coop_session.participants or []
    # user_participant = next((p for p in participants if p['user_id'] == current_user.id), None)
    # if not user_participant:
    #     flash('You are not a participant in this session', 'error')
    #     return redirect(url_for('main.trials'))
    pass
    
    challenge = coop_session.challenge
    is_creator = (coop_session.creator_id == current_user.id)
    return render_template('coop_play.html', 
                         session=coop_session, 
                         challenge=challenge,
                         user_team=user_participant['team'],
                         is_creator=is_creator)

# ==================== ADMIN ROUTES ====================

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    total_users = User.query.count()
    total_challenges = Challenge.query.count()
    total_attempts = ChallengeAttempt.query.count()
    total_sessions = CoopSession.query.count()
    recent_logs = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_challenges=total_challenges,
                         total_attempts=total_attempts,
                         total_sessions=total_sessions,
                         recent_logs=recent_logs)

@admin_bp.route('/challenges')
@login_required
def manage_challenges():
    """Manage challenges"""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    challenges = Challenge.query.all()
    return render_template('admin/challenges.html', challenges=challenges)

@admin_bp.route('/challenges/add', methods=['GET', 'POST'])
@login_required
def add_challenge():
    """Add new challenge"""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        challenge = Challenge(
            title=request.form.get('title'),
            description=request.form.get('description'),
            category=request.form.get('category'),
            difficulty=request.form.get('difficulty'),
            challenge_type=request.form.get('challenge_type'),
            max_score=int(request.form.get('max_score', 100)),
            time_limit=int(request.form.get('time_limit', 300)),
            solution_explanation=request.form.get('solution_explanation')
        )
        db.session.add(challenge)
        
        # Log admin action
        log = AdminLog(
            admin_id=current_user.id,
            action='Added new challenge',
            target_type='challenge',
            target_id=challenge.id,
            details={'title': challenge.title}
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Challenge added successfully', 'success')
        return redirect(url_for('admin.manage_challenges'))
    
    return render_template('admin/add_challenge.html')

@admin_bp.route('/challenges/<challenge_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_challenge(challenge_id):
    """Edit challenge"""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    challenge = Challenge.query.get(challenge_id)
    if not challenge:
        flash('Challenge not found', 'error')
        return redirect(url_for('admin.manage_challenges'))
    
    if request.method == 'POST':
        challenge.title = request.form.get('title')
        challenge.description = request.form.get('description')
        challenge.category = request.form.get('category')
        challenge.difficulty = request.form.get('difficulty')
        challenge.challenge_type = request.form.get('challenge_type')
        challenge.max_score = int(request.form.get('max_score', 100))
        challenge.time_limit = int(request.form.get('time_limit', 300))
        challenge.solution_explanation = request.form.get('solution_explanation')
        challenge.updated_at = datetime.utcnow()
        
        # Log admin action
        log = AdminLog(
            admin_id=current_user.id,
            action='Edited challenge',
            target_type='challenge',
            target_id=challenge.id,
            details={'title': challenge.title}
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Challenge updated successfully', 'success')
        return redirect(url_for('admin.manage_challenges'))
    
    return render_template('admin/edit_challenge.html', challenge=challenge)

@admin_bp.route('/challenges/<challenge_id>/delete', methods=['POST'])
@login_required
def delete_challenge(challenge_id):
    """Delete challenge"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    challenge = Challenge.query.get(challenge_id)
    if not challenge:
        return jsonify({'error': 'Challenge not found'}), 404
    
    # Log admin action
    log = AdminLog(
        admin_id=current_user.id,
        action='Deleted challenge',
        target_type='challenge',
        target_id=challenge.id,
        details={'title': challenge.title}
    )
    db.session.add(log)
    db.session.delete(challenge)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Challenge deleted'})

@admin_bp.route('/users')
@login_required
def manage_users():
    """Manage users"""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<user_id>/toggle', methods=['POST'])
@login_required
def toggle_user(user_id):
    """Toggle user active status"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.is_active = not user.is_active
    
    # Log admin action
    log = AdminLog(
        admin_id=current_user.id,
        action='Toggled user status',
        target_type='user',
        target_id=user.id,
        details={'username': user.username, 'is_active': user.is_active}
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'success': True, 'is_active': user.is_active})

@admin_bp.route('/sessions')
@login_required
def view_sessions():
    """View all co-op sessions"""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    sessions = CoopSession.query.order_by(CoopSession.created_at.desc()).all()
    return render_template('admin/sessions.html', sessions=sessions)

@admin_bp.route('/logs')
@login_required
def view_logs():
    """View admin logs"""
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    logs = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(100).all()
    return render_template('admin/logs.html', logs=logs)

@admin_bp.route('/leaderboard/reset', methods=['POST'])
@login_required
def reset_leaderboard():
    """Reset leaderboard (delete all attempts)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    # Delete all attempts
    ChallengeAttempt.query.delete()
    
    # Log admin action
    log = AdminLog(
        admin_id=current_user.id,
        action='Reset leaderboard',
        target_type='leaderboard',
        details={'message': 'All challenge attempts deleted'}
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Leaderboard reset successfully'})
