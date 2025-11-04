"""
Bot AI System - State Machine Based Opponent
Handles bot behavior for Red Team and Blue Team challenges
"""
import random
import time
from datetime import datetime

class BotAI:
    """Intelligent bot opponent with state machine logic"""
    
    def __init__(self, difficulty='medium', role='defender'):
        self.difficulty = difficulty
        self.role = role  # 'attacker' or 'defender'
        self.state = 'idle'
        self.action_history = []
        self.skill_level = self._get_skill_level()
        
    def _get_skill_level(self):
        """Get bot skill parameters based on difficulty"""
        skills = {
            'easy': {
                'reaction_time': (3, 6),
                'success_rate': 0.3,
                'mistake_rate': 0.4,
                'thinking_time': (2, 5)
            },
            'medium': {
                'reaction_time': (2, 4),
                'success_rate': 0.6,
                'mistake_rate': 0.2,
                'thinking_time': (1, 3)
            },
            'hard': {
                'reaction_time': (1, 2),
                'success_rate': 0.85,
                'mistake_rate': 0.05,
                'thinking_time': (0.5, 2)
            }
        }
        return skills.get(self.difficulty, skills['medium'])
    
    def get_next_action(self, challenge_type, current_state):
        """Determine bot's next action based on challenge type and state"""
        # Simulate thinking time
        thinking_time = random.uniform(*self.skill_level['thinking_time'])
        
        action = {
            'timestamp': datetime.utcnow().isoformat(),
            'thinking_time': thinking_time,
            'action': None,
            'description': None,
            'success': False
        }
        
        # Route to appropriate challenge handler
        if challenge_type == 'sql_injection':
            action.update(self._handle_sql_injection(current_state))
        elif challenge_type == 'xss':
            action.update(self._handle_xss(current_state))
        elif challenge_type == 'dos':
            action.update(self._handle_dos(current_state))
        elif challenge_type == 'password_strength':
            action.update(self._handle_password(current_state))
        elif challenge_type == 'server_config':
            action.update(self._handle_server_config(current_state))
        
        # Apply difficulty-based success rate
        if random.random() > self.skill_level['success_rate']:
            action['success'] = False
            action['description'] += ' (Failed)'
        
        self.action_history.append(action)
        return action
    
    def _handle_sql_injection(self, state):
        """Handle SQL Injection challenge logic"""
        if self.role == 'attacker':
            attacks = [
                {"action": "probe", "description": "Testing for SQL injection vulnerability with ' OR '1'='1"},
                {"action": "enumerate", "description": "Attempting UNION SELECT to enumerate columns"},
                {"action": "extract", "description": "Extracting data with UNION SELECT username, password FROM users"},
                {"action": "exploit", "description": "Attempting to bypass authentication"}
            ]
        else:  # defender
            defenses = [
                {"action": "detect", "description": "Scanning for suspicious SQL patterns in input"},
                {"action": "sanitize", "description": "Applying input sanitization and parameterized queries"},
                {"action": "block", "description": "Blocking malicious SQL injection attempt"},
                {"action": "log", "description": "Logging attack attempt for analysis"}
            ]
            attacks = defenses
        
        step = min(state.get('bot_step', 0), len(attacks) - 1)
        selected = attacks[step]
        selected['success'] = random.random() < self.skill_level['success_rate']
        return selected
    
    def _handle_xss(self, state):
        """Handle XSS challenge logic"""
        if self.role == 'attacker':
            attacks = [
                {"action": "probe", "description": "Testing for XSS vulnerability with <script>alert('test')</script>"},
                {"action": "craft", "description": "Crafting payload: <img src=x onerror=alert(document.cookie)>"},
                {"action": "inject", "description": "Injecting XSS payload into input field"},
                {"action": "steal", "description": "Attempting to steal session cookies"}
            ]
        else:  # defender
            defenses = [
                {"action": "detect", "description": "Scanning for XSS patterns in user input"},
                {"action": "encode", "description": "HTML encoding user input to prevent execution"},
                {"action": "validate", "description": "Validating input against whitelist"},
                {"action": "protect", "description": "Enabling Content Security Policy (CSP)"}
            ]
            attacks = defenses
        
        step = min(state.get('bot_step', 0), len(attacks) - 1)
        selected = attacks[step]
        selected['success'] = random.random() < self.skill_level['success_rate']
        return selected
    
    def _handle_dos(self, state):
        """Handle DoS challenge logic"""
        if self.role == 'attacker':
            attacks = [
                {"action": "scan", "description": "Scanning target server for vulnerabilities"},
                {"action": "flood", "description": "Initiating SYN flood attack"},
                {"action": "amplify", "description": "Performing DNS amplification attack"},
                {"action": "overwhelm", "description": "Overwhelming server with requests"}
            ]
        else:  # defender
            defenses = [
                {"action": "monitor", "description": "Monitoring network traffic for anomalies"},
                {"action": "rate_limit", "description": "Applying rate limiting to suspicious IPs"},
                {"action": "filter", "description": "Filtering malicious traffic with firewall rules"},
                {"action": "mitigate", "description": "Activating DDoS mitigation service"}
            ]
            attacks = defenses
        
        step = min(state.get('bot_step', 0), len(attacks) - 1)
        selected = attacks[step]
        selected['success'] = random.random() < self.skill_level['success_rate']
        return selected
    
    def _handle_password(self, state):
        """Handle Password Strength challenge logic"""
        if self.role == 'attacker':
            attacks = [
                {"action": "dictionary", "description": "Attempting dictionary attack with common passwords"},
                {"action": "brute_force", "description": "Running brute force attack on password"},
                {"action": "rainbow", "description": "Using rainbow tables to crack hash"},
                {"action": "crack", "description": "Successfully cracking weak password"}
            ]
        else:  # defender
            defenses = [
                {"action": "analyze", "description": "Analyzing password strength requirements"},
                {"action": "enforce", "description": "Enforcing strong password policy"},
                {"action": "hash", "description": "Implementing bcrypt hashing with salt"},
                {"action": "protect", "description": "Adding account lockout after failed attempts"}
            ]
            attacks = defenses
        
        step = min(state.get('bot_step', 0), len(attacks) - 1)
        selected = attacks[step]
        selected['success'] = random.random() < self.skill_level['success_rate']
        return selected
    
    def _handle_server_config(self, state):
        """Handle Server Misconfiguration challenge logic"""
        if self.role == 'attacker':
            attacks = [
                {"action": "enumerate", "description": "Enumerating server services and versions"},
                {"action": "scan", "description": "Scanning for open ports and misconfigurations"},
                {"action": "exploit", "description": "Exploiting exposed admin panel"},
                {"action": "access", "description": "Gaining unauthorized access via misconfiguration"}
            ]
        else:  # defender
            defenses = [
                {"action": "audit", "description": "Auditing server configuration"},
                {"action": "harden", "description": "Hardening server security settings"},
                {"action": "close", "description": "Closing unnecessary open ports"},
                {"action": "secure", "description": "Securing admin interfaces with authentication"}
            ]
            attacks = defenses
        
        step = min(state.get('bot_step', 0), len(attacks) - 1)
        selected = attacks[step]
        selected['success'] = random.random() < self.skill_level['success_rate']
        return selected
    
    def get_reaction_delay(self):
        """Get bot's reaction delay based on difficulty"""
        return random.uniform(*self.skill_level['reaction_time'])
    
    def should_make_mistake(self):
        """Determine if bot should make a mistake"""
        return random.random() < self.skill_level['mistake_rate']
    
    def get_hint_response(self, challenge_type):
        """Get bot's response to seeing player's action"""
        responses = [
            "Analyzing your move...",
            "Adapting strategy...",
            "Preparing countermeasure...",
            "Interesting approach..."
        ]
        return random.choice(responses)
