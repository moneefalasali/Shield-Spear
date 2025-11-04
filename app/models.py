from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and profile management"""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attempts = db.relationship('ChallengeAttempt', backref='user', lazy=True, cascade='all, delete-orphan')
    coop_sessions = db.relationship('CoopSession', backref='creator', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_total_score(self):
        """Calculate total score from all attempts"""
        attempts = ChallengeAttempt.query.filter_by(user_id=self.id, is_completed=True).all()
        return sum(attempt.score for attempt in attempts)
    
    def get_rank(self):
        """Get user rank in leaderboard"""
        users = db.session.query(User).all()
        sorted_users = sorted(users, key=lambda u: u.get_total_score(), reverse=True)
        for rank, user in enumerate(sorted_users, 1):
            if user.id == self.id:
                return rank
        return len(sorted_users)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Challenge(db.Model):
    """Challenge model for storing challenge definitions"""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # blue, red, coop
    difficulty = db.Column(db.String(20), nullable=False)  # easy, medium, hard
    challenge_type = db.Column(db.String(50), nullable=False)  # sql_injection, xss, dos, password_strength, server_config
    max_score = db.Column(db.Integer, default=100)
    time_limit = db.Column(db.Integer, default=300)  # seconds
    hints = db.Column(db.JSON)  # JSON array of hints
    solution_explanation = db.Column(db.Text)  # Solution explanation
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attempts = db.relationship('ChallengeAttempt', backref='challenge', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Return a JSON-serializable representation of the challenge."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'difficulty': self.difficulty,
            'challenge_type': self.challenge_type,
            'max_score': self.max_score,
            'time_limit': self.time_limit,
            'hints': self.hints,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<Challenge {self.title}>'

class ChallengeAttempt(db.Model):
    """Model for tracking user attempts on challenges"""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False, index=True)
    challenge_id = db.Column(db.String(36), db.ForeignKey('challenge.id'), nullable=False, index=True)
    
    # Attempt details
    user_input = db.Column(db.Text)  # User's solution/input
    is_correct = db.Column(db.Boolean, default=False)
    score = db.Column(db.Integer, default=0)
    time_taken = db.Column(db.Integer)  # seconds
    feedback = db.Column(db.Text)  # Feedback for user
    mistakes = db.Column(db.JSON)  # JSON array of mistakes
    corrections = db.Column(db.JSON)  # JSON object with corrections
    bot_actions = db.Column(db.JSON)  # JSON array of bot actions
    is_completed = db.Column(db.Boolean, default=False)
    
    # Timestamps
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<ChallengeAttempt {self.user_id} - {self.challenge_id}>'

class CoopSession(db.Model):
    """Model for cooperative play sessions"""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    creator_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.String(36), db.ForeignKey('challenge.id'), nullable=False)
    
    # Session details
    session_code = db.Column(db.String(8), unique=True, nullable=False)  # Code to join session
    creator_team = db.Column(db.String(20), nullable=False)  # 'red' or 'blue' - team chosen by creator
    status = db.Column(db.String(20), default='waiting')  # waiting, in_progress, completed
    
    # Participants (JSON array of user IDs with their teams)
    participants = db.Column(db.JSON, default=list)
    
    # Real-time event log
    event_log = db.Column(db.JSON, default=list)
    
    # Results
    results = db.Column(db.JSON)  # JSON object with results for each participant
    # Persistent HP and cooldown maps (optional) to record session state
    hp_map = db.Column(db.JSON, default=dict)
    cooldowns = db.Column(db.JSON, default=dict)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    challenge = db.relationship('Challenge', backref='coop_sessions')
    
    def __repr__(self):
        return f'<CoopSession {self.session_code}>'

class AdminLog(db.Model):
    """Model for logging admin actions"""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    admin_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    target_type = db.Column(db.String(50))  # user, challenge, session, leaderboard
    target_id = db.Column(db.String(36))
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    admin = db.relationship('User', foreign_keys=[admin_id])
    
    def __repr__(self):
        return f'<AdminLog {self.action}>'
