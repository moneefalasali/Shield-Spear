
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
    time_taken = (datetime.utcnow() - attempt.started_at).total_seconds()
    
    # Calculate score
    score = challenge_engine.calculate_score(
        result['success'],
        time_taken,
        challenge.difficulty
    )
    
    # Update attempt
    attempt.is_completed = True
    attempt.completed_at = datetime.utcnow()
    attempt.score = score
    attempt.is_successful = result['success']
    
    db.session.commit()
    
    # Return result to user
    return jsonify({
        'success': True,
        'result': result,
        'score': score,
        'redirect_url': url_for('challenges.result', attempt_id=attempt.id)
    })

@challenges_bp.route('/result/<attempt_id>')
@login_required
def result(attempt_id):
    """Show challenge result"""
    attempt = ChallengeAttempt.query.get(attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        flash('Invalid challenge attempt', 'error')
        return redirect(url_for('main.trials'))
    
    return render_template('result.html', attempt=attempt)


# ==================== CO-OP ROUTES ====================

@challenges_bp.route('/coop/create', methods=['POST'])
@login_required
def create_coop_session():
    """Create a new co-op session"""
    data = request.get_json() or {}
    challenge_id = data.get('challenge_id')
    
    if not challenge_id:
        return jsonify({'error': 'Challenge ID is required'}), 400
    
    challenge = Challenge.query.get(challenge_id)
    if not challenge or challenge.category != 'coop':
        return jsonify({'error': 'Invalid co-op challenge'}), 404
    
    # Create a unique session ID
    session_id = str(uuid.uuid4())[:8]
    
    # Create the session
    coop_session = CoopSession(
        session_id=session_id,
        challenge_id=challenge_id,
        creator_id=current_user.id,
        participants=[{'user_id': current_user.id, 'username': current_user.username, 'team': 'blue'}] # Creator starts in blue team
    )
    
    db.session.add(coop_session)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'redirect_url': url_for('challenges.play_coop', session_id=session_id)
    })

@challenges_bp.route('/coop/join', methods=['POST'])
@login_required
def join_coop_session():
    """Join an existing co-op session"""
    data = request.get_json() or {}
    session_id = data.get('session_id', '').strip()
    
    if not session_id:
        return jsonify({'error': 'Session ID is required'}), 400
    
    coop_session = CoopSession.query.filter_by(session_id=session_id).first()
    if not coop_session:
        return jsonify({'error': 'Session not found'}), 404
    
    # Check if user is already in the session
    participants = coop_session.participants or []
    if any(p['user_id'] == current_user.id for p in participants):
        # User is already in, just redirect
        return jsonify({
            'success': True,
            'redirect_url': url_for('challenges.play_coop', session_id=session_id)
        })
    
    # Add user to the session (default to red team if blue is taken)
    blue_team_count = sum(1 for p in participants if p['team'] == 'blue')
    team = 'blue' if blue_team_count == 0 else 'red'
    
    new_participant = {'user_id': current_user.id, 'username': current_user.username, 'team': team}
    
    # Use mutable_json_type to handle JSON updates
    coop_session.participants.append(new_participant)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'redirect_url': url_for('challenges.play_coop', session_id=session_id)
    })

@challenges_bp.route('/coop/play/<session_id>')
@login_required
def play_coop(session_id):
    """Co-op gameplay page"""
    coop_session = CoopSession.query.filter_by(session_id=session_id).first()
    if not coop_session:
        flash('Co-op session not found', 'error')
        return redirect(url_for('main.trials'))
    # Allow access to the session page regardless of participation status.
    # The SocketIO logic in events.py will handle adding the user as a participant.
    # The original check was:
    participants = coop_session.participants or []
    user_participant = next((p for p in participants if p['user_id'] == current_user.id), None)
    if not user_participant:
        flash('You are not a participant in this session', 'error')
        return redirect(url_for('main.trials'))
    
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
        flash('Admin access required', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Fetch stats
    total_users = User.query.count()
    total_challenges = Challenge.query.count()
    total_attempts = ChallengeAttempt.query.count()
    
    # Fetch recent logs
    logs = AdminLog.query.order_by(AdminLog.timestamp.desc()).limit(20).all()
    
    return render_template('admin/dashboard.html', 
                         total_users=total_users,
                         total_challenges=total_challenges,
                         total_attempts=total_attempts,
                         logs=logs)

@admin_bp.route('/users')
@login_required
def manage_users():
    """Manage users"""
    if not current_user.is_admin:
        return redirect(url_for('main.dashboard'))
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/challenges')
@login_required
def manage_challenges():
    """Manage challenges"""
    if not current_user.is_admin:
        return redirect(url_for('main.dashboard'))
    
    challenges = Challenge.query.all()
    return render_template('admin/challenges.html', challenges=challenges)

@admin_bp.route('/challenges/create', methods=['GET', 'POST'])
@login_required
def create_challenge():
    """Create a new challenge"""
    if not current_user.is_admin:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        difficulty = request.form.get('difficulty')
        challenge_type = request.form.get('challenge_type')
        
        # Create challenge
        challenge = Challenge(
            title=title,
            description=description,
            category=category,
            difficulty=difficulty,
            challenge_type=challenge_type
        )
        db.session.add(challenge)
        db.session.commit()
        
        # Log action
        log_admin_action(f'Created challenge: {title}')
        
        flash('Challenge created successfully', 'success')
        return redirect(url_for('admin.manage_challenges'))
    
    return render_template('admin/create_challenge.html')

@admin_bp.route('/challenges/edit/<challenge_id>', methods=['GET', 'POST'])
@login_required
def edit_challenge(challenge_id):
    """Edit an existing challenge"""
    if not current_user.is_admin:
        return redirect(url_for('main.dashboard'))
    
    challenge = Challenge.query.get(challenge_id)
    if not challenge:
        flash('Challenge not found', 'error')
        return redirect(url_for('admin.manage_challenges'))
    
    if request.method == 'POST':
        # Update challenge data
        challenge.title = request.form.get('title')
        challenge.description = request.form.get('description')
        challenge.category = request.form.get('category')
        challenge.difficulty = request.form.get('difficulty')
        challenge.challenge_type = request.form.get('challenge_type')
        challenge.is_active = 'is_active' in request.form
        
        db.session.commit()
        
        # Log action
        log_admin_action(f'Edited challenge: {challenge.title}')
        
        flash('Challenge updated successfully', 'success')
        return redirect(url_for('admin.manage_challenges'))
    
    return render_template('admin/edit_challenge.html', challenge=challenge)

@admin_bp.route('/challenges/delete/<challenge_id>', methods=['POST'])
@login_required
def delete_challenge(challenge_id):
    """Delete a challenge"""
    if not current_user.is_admin:
        return redirect(url_for('main.dashboard'))
    
    challenge = Challenge.query.get(challenge_id)
    if challenge:
        # Log action before deleting
        log_admin_action(f'Deleted challenge: {challenge.title}')
        
        db.session.delete(challenge)
        db.session.commit()
        flash('Challenge deleted successfully', 'success')
    else:
        flash('Challenge not found', 'error')
        
    return redirect(url_for('admin.manage_challenges'))

# ==================== API ROUTES ====================

@api_bp.route('/bot/interact', methods=['POST'])
@login_required
def bot_interact():
    """Handle interaction with the bot AI"""
    data = request.get_json() or {}
    attempt_id = data.get('attempt_id')
    user_message = data.get('message', '').strip()
    
    if not attempt_id or not user_message:
        return jsonify({'error': 'Missing data'}), 400
    
    # Retrieve bot state from session
    bot_config = session.get(f'bot_{attempt_id}')
    if not bot_config:
        return jsonify({'error': 'Bot session not found'}), 404
    
    # Initialize bot with stored state
    bot = BotAI(difficulty=bot_config['difficulty'], role=bot_config['role'])
    bot.conversation_step = bot_config.get('step', 0)
    
    # Get bot response
    try:
        bot_response = bot.get_response(user_message)
    except Exception as e:
        current_app.logger.error(f"Bot AI error: {e}\n{traceback.format_exc()}")
        return jsonify({'error': 'An error occurred with the AI bot.'}), 500
    
    # Update bot step in session
    bot_config['step'] = bot.conversation_step
    session[f'bot_{attempt_id}'] = bot_config
    
    return jsonify({'response': bot_response})

# ==================== HELPER FUNCTIONS ====================

def log_admin_action(action):
    """Log an admin action"""
    log = AdminLog(user_id=current_user.id, action=action)
    db.session.add(log)
    db.session.commit()


# ==================== ERROR HANDLERS ====================

@main_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@main_bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback() # Rollback in case of DB error
    return render_template('500.html'), 500


# ==================== UTILITY ROUTES ====================

@main_bp.route('/generate-sitemap')
def generate_sitemap():
    """Generate a simple sitemap for SEO and testing"""
    links = []
    for rule in current_app.url_map.iter_rules():
        # Filter out rules with arguments and internal/static routes
        if "GET" in rule.methods and len(rule.arguments) == 0 and \
           rule.endpoint not in ('static', 'admin.static'):
            links.append(url_for(rule.endpoint, _external=True))
    
    return "<br>".join(links)

@main_bp.route('/reset-password-for-user/<username>', methods=['GET'])
@login_required
def reset_password_for_user(username):
    """A utility route for admins to reset a user's password. Should be protected and logged."""
    if not current_user.is_admin:
        flash('Admin access required', 'error')
        return redirect(url_for('main.dashboard'))

    user = User.query.filter_by(username=username).first()
    if not user:
        flash(f'User {username} not found.', 'error')
        return redirect(url_for('admin.manage_users'))

    # Generate a random temporary password
    temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    user.set_password(temp_password)
    db.session.commit()

    # Log the action
    log_admin_action(f'Reset password for user: {username}')

    flash(f'Password for {username} has been reset to: {temp_password}', 'success')
    return redirect(url_for('admin.manage_users'))
