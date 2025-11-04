"""
Challenge Engine - Interactive Challenge System
Handles challenge execution, validation, and scoring
"""
import re
import hashlib
import random
from datetime import datetime

class ChallengeEngine:
    """Engine for executing and validating challenges"""
    
    def __init__(self):
        self.sandbox_db = self._create_sandbox_db()
    
    def _create_sandbox_db(self):
        """Create simulated database for SQL injection challenges"""
        return {
            'users': [
                {'id': 1, 'username': 'admin', 'password': 'admin123', 'role': 'admin'},
                {'id': 2, 'username': 'user1', 'password': 'password123', 'role': 'user'},
                {'id': 3, 'username': 'john', 'password': 'john2024', 'role': 'user'},
            ],
            'secrets': [
                {'id': 1, 'data': 'flag{sql_injection_master}'},
                {'id': 2, 'data': 'secret_api_key_12345'},
            ]
        }
    
    def evaluate_challenge(self, challenge_type, user_input, difficulty, role='attacker'):
        """Main evaluation function for all challenge types"""
        
        if challenge_type == 'sql_injection':
            return self._evaluate_sql_injection(user_input, difficulty, role)
        elif challenge_type == 'xss':
            return self._evaluate_xss(user_input, difficulty, role)
        elif challenge_type == 'dos':
            return self._evaluate_dos(user_input, difficulty, role)
        elif challenge_type == 'password_strength':
            return self._evaluate_password_strength(user_input, difficulty, role)
        elif challenge_type == 'server_config':
            return self._evaluate_server_config(user_input, difficulty, role)
        else:
            return {
                'success': False,
                'score': 0,
                'feedback': 'Unknown challenge type',
                'details': {}
            }
    
    def _evaluate_sql_injection(self, user_input, difficulty, role):
        """Evaluate SQL Injection challenge"""
        score = 0
        feedback_parts = []
        success = False
        details = {'extracted_data': [], 'techniques_used': []}
        
        if role == 'attacker':
            # Check for SQL injection techniques
            if "'" in user_input or '"' in user_input:
                score += 20
                feedback_parts.append("✓ Used quote character to break SQL syntax")
                details['techniques_used'].append('quote_injection')
            
            if re.search(r"(OR|or)\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?", user_input):
                score += 30
                feedback_parts.append("✓ Implemented boolean-based SQL injection")
                details['techniques_used'].append('boolean_injection')
                success = True
            
            if re.search(r"(UNION|union)\s+(SELECT|select)", user_input, re.IGNORECASE):
                score += 40
                feedback_parts.append("✓ Used UNION SELECT for data extraction")
                details['techniques_used'].append('union_injection')
                details['extracted_data'] = self.sandbox_db['users']
                success = True
            
            if re.search(r"--", user_input) or re.search(r"#", user_input):
                score += 10
                feedback_parts.append("✓ Commented out remaining query")
                details['techniques_used'].append('comment_injection')
            
            if difficulty == 'hard' and score < 80:
                feedback_parts.append("⚠ For hard difficulty, try combining multiple techniques")
            
            if not success:
                feedback_parts.append("✗ No valid SQL injection detected. Try: admin' OR '1'='1'--")
        
        else:  # defender
            # Check for defensive measures
            if re.search(r"(parameterized|prepared|bind)", user_input, re.IGNORECASE):
                score += 40
                feedback_parts.append("✓ Implemented parameterized queries")
                success = True
            
            if re.search(r"(escape|sanitize|filter)", user_input, re.IGNORECASE):
                score += 30
                feedback_parts.append("✓ Added input sanitization")
                success = True
            
            if re.search(r"(whitelist|validation)", user_input, re.IGNORECASE):
                score += 20
                feedback_parts.append("✓ Implemented input validation")
            
            if re.search(r"(least privilege|permissions)", user_input, re.IGNORECASE):
                score += 10
                feedback_parts.append("✓ Applied least privilege principle")
            
            if not success:
                feedback_parts.append("✗ No strong defenses detected. Consider using parameterized queries")
        
        return {
            'success': success,
            'score': min(score, 100),
            'feedback': '\n'.join(feedback_parts),
            'details': details,
            'corrections': self._get_sql_corrections(role)
        }
    
    def _evaluate_xss(self, user_input, difficulty, role):
        """Evaluate XSS challenge"""
        score = 0
        feedback_parts = []
        success = False
        details = {'payloads_detected': [], 'vulnerabilities': []}
        
        if role == 'attacker':
            # Check for XSS payloads
            if re.search(r"<script", user_input, re.IGNORECASE):
                score += 30
                feedback_parts.append("✓ Used <script> tag injection")
                details['payloads_detected'].append('script_tag')
                success = True
            
            if re.search(r"onerror|onload|onclick", user_input, re.IGNORECASE):
                score += 35
                feedback_parts.append("✓ Used event handler injection")
                details['payloads_detected'].append('event_handler')
                success = True
            
            if re.search(r"alert|prompt|confirm", user_input, re.IGNORECASE):
                score += 20
                feedback_parts.append("✓ Included JavaScript execution")
            
            if re.search(r"document\.cookie|localStorage", user_input, re.IGNORECASE):
                score += 15
                feedback_parts.append("✓ Attempted data exfiltration")
                details['payloads_detected'].append('data_theft')
            
            if not success:
                feedback_parts.append("✗ No XSS payload detected. Try: <script>alert('XSS')</script>")
        
        else:  # defender
            if re.search(r"(encode|escape|htmlspecialchars)", user_input, re.IGNORECASE):
                score += 40
                feedback_parts.append("✓ Implemented HTML encoding")
                success = True
            
            if re.search(r"(CSP|Content-Security-Policy)", user_input, re.IGNORECASE):
                score += 35
                feedback_parts.append("✓ Enabled Content Security Policy")
                success = True
            
            if re.search(r"(whitelist|sanitize)", user_input, re.IGNORECASE):
                score += 25
                feedback_parts.append("✓ Applied input sanitization")
            
            if not success:
                feedback_parts.append("✗ Insufficient XSS protection. Implement HTML encoding and CSP")
        
        return {
            'success': success,
            'score': min(score, 100),
            'feedback': '\n'.join(feedback_parts),
            'details': details,
            'corrections': self._get_xss_corrections(role)
        }
    
    def _evaluate_dos(self, user_input, difficulty, role):
        """Evaluate DoS Simulation challenge"""
        score = 0
        feedback_parts = []
        success = False
        details = {'attack_vectors': [], 'mitigation_applied': []}
        
        if role == 'attacker':
            if re.search(r"(flood|syn|ddos)", user_input, re.IGNORECASE):
                score += 30
                feedback_parts.append("✓ Initiated flood attack")
                details['attack_vectors'].append('flood')
                success = True
            
            if re.search(r"(amplification|reflection)", user_input, re.IGNORECASE):
                score += 35
                feedback_parts.append("✓ Used amplification technique")
                details['attack_vectors'].append('amplification')
                success = True
            
            if re.search(r"(botnet|distributed)", user_input, re.IGNORECASE):
                score += 25
                feedback_parts.append("✓ Employed distributed attack")
            
            if re.search(r"\d+\s*(requests|packets)", user_input, re.IGNORECASE):
                score += 10
                feedback_parts.append("✓ Specified attack volume")
            
            if not success:
                feedback_parts.append("✗ No effective DoS attack detected")
        
        else:  # defender
            if re.search(r"(rate.limit|throttle)", user_input, re.IGNORECASE):
                score += 40
                feedback_parts.append("✓ Implemented rate limiting")
                details['mitigation_applied'].append('rate_limiting')
                success = True
            
            if re.search(r"(firewall|filter|block)", user_input, re.IGNORECASE):
                score += 30
                feedback_parts.append("✓ Applied traffic filtering")
                details['mitigation_applied'].append('filtering')
                success = True
            
            if re.search(r"(cdn|cloudflare|akamai)", user_input, re.IGNORECASE):
                score += 20
                feedback_parts.append("✓ Using CDN for DDoS mitigation")
            
            if re.search(r"(monitor|detect)", user_input, re.IGNORECASE):
                score += 10
                feedback_parts.append("✓ Monitoring traffic patterns")
            
            if not success:
                feedback_parts.append("✗ Insufficient DoS protection. Apply rate limiting and filtering")
        
        return {
            'success': success,
            'score': min(score, 100),
            'feedback': '\n'.join(feedback_parts),
            'details': details,
            'corrections': self._get_dos_corrections(role)
        }
    
    def _evaluate_password_strength(self, user_input, difficulty, role):
        """Evaluate Password Strength challenge"""
        score = 0
        feedback_parts = []
        success = False
        details = {'strength_factors': []}
        
        if role == 'attacker':
            # For attacker: check if they can crack weak passwords
            if re.search(r"(dictionary|common|weak)", user_input, re.IGNORECASE):
                score += 30
                feedback_parts.append("✓ Identified weak password patterns")
                success = True
            
            if re.search(r"(brute.force|hashcat|john)", user_input, re.IGNORECASE):
                score += 35
                feedback_parts.append("✓ Using password cracking tools")
                success = True
            
            if re.search(r"(rainbow|hash)", user_input, re.IGNORECASE):
                score += 25
                feedback_parts.append("✓ Attempting hash-based attack")
            
            if not success:
                feedback_parts.append("✗ Attack strategy unclear")
        
        else:  # defender - check password strength
            password = user_input.strip()
            
            if len(password) >= 12:
                score += 25
                feedback_parts.append("✓ Password length is adequate (12+ chars)")
                details['strength_factors'].append('length')
            else:
                feedback_parts.append("✗ Password too short (minimum 12 characters)")
            
            if re.search(r"[A-Z]", password) and re.search(r"[a-z]", password):
                score += 20
                feedback_parts.append("✓ Contains mixed case letters")
                details['strength_factors'].append('mixed_case')
            
            if re.search(r"\d", password):
                score += 20
                feedback_parts.append("✓ Contains numbers")
                details['strength_factors'].append('numbers')
            
            if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
                score += 25
                feedback_parts.append("✓ Contains special characters")
                details['strength_factors'].append('special_chars')
            
            if not re.search(r"(password|123|admin|qwerty)", password, re.IGNORECASE):
                score += 10
                feedback_parts.append("✓ No common patterns detected")
                details['strength_factors'].append('no_common_patterns')
            else:
                feedback_parts.append("⚠ Contains common password patterns")
            
            if score >= 70:
                success = True
            else:
                feedback_parts.append("✗ Password strength insufficient")
        
        return {
            'success': success,
            'score': min(score, 100),
            'feedback': '\n'.join(feedback_parts),
            'details': details,
            'corrections': self._get_password_corrections(role)
        }
    
    def _evaluate_server_config(self, user_input, difficulty, role):
        """Evaluate Server Misconfiguration challenge"""
        score = 0
        feedback_parts = []
        success = False
        details = {'issues_found': [], 'fixes_applied': []}
        
        if role == 'attacker':
            if re.search(r"(scan|nmap|enumerate)", user_input, re.IGNORECASE):
                score += 25
                feedback_parts.append("✓ Performed reconnaissance")
                details['issues_found'].append('enumeration')
                success = True
            
            if re.search(r"(exposed|open|public)", user_input, re.IGNORECASE):
                score += 30
                feedback_parts.append("✓ Identified exposed services")
                details['issues_found'].append('exposed_services')
                success = True
            
            if re.search(r"(admin|panel|dashboard)", user_input, re.IGNORECASE):
                score += 25
                feedback_parts.append("✓ Found admin interface")
            
            if re.search(r"(default|credentials|password)", user_input, re.IGNORECASE):
                score += 20
                feedback_parts.append("✓ Attempted default credentials")
            
            if not success:
                feedback_parts.append("✗ No significant findings")
        
        else:  # defender
            if re.search(r"(close|disable|port)", user_input, re.IGNORECASE):
                score += 30
                feedback_parts.append("✓ Closed unnecessary ports")
                details['fixes_applied'].append('port_closure')
                success = True
            
            if re.search(r"(authentication|password|2fa)", user_input, re.IGNORECASE):
                score += 30
                feedback_parts.append("✓ Secured admin access")
                details['fixes_applied'].append('auth_hardening')
                success = True
            
            if re.search(r"(update|patch|version)", user_input, re.IGNORECASE):
                score += 20
                feedback_parts.append("✓ Updated software versions")
            
            if re.search(r"(encrypt|ssl|tls|https)", user_input, re.IGNORECASE):
                score += 20
                feedback_parts.append("✓ Enabled encryption")
            
            if not success:
                feedback_parts.append("✗ Critical misconfigurations remain")
        
        return {
            'success': success,
            'score': min(score, 100),
            'feedback': '\n'.join(feedback_parts),
            'details': details,
            'corrections': self._get_server_config_corrections(role)
        }
    
    # Correction methods
    def _get_sql_corrections(self, role):
        if role == 'attacker':
            return {
                'title': 'SQL Injection Techniques',
                'examples': [
                    "admin' OR '1'='1'--",
                    "' UNION SELECT username, password FROM users--",
                    "' OR 1=1--"
                ]
            }
        else:
            return {
                'title': 'SQL Injection Defense',
                'examples': [
                    "Use parameterized queries/prepared statements",
                    "Implement input validation and sanitization",
                    "Apply least privilege database permissions"
                ]
            }
    
    def _get_xss_corrections(self, role):
        if role == 'attacker':
            return {
                'title': 'XSS Attack Techniques',
                'examples': [
                    "<script>alert('XSS')</script>",
                    "<img src=x onerror=alert(document.cookie)>",
                    "<iframe src='javascript:alert(1)'>"
                ]
            }
        else:
            return {
                'title': 'XSS Defense',
                'examples': [
                    "HTML encode all user input",
                    "Implement Content Security Policy (CSP)",
                    "Use secure frameworks with auto-escaping"
                ]
            }
    
    def _get_dos_corrections(self, role):
        if role == 'attacker':
            return {
                'title': 'DoS Attack Methods',
                'examples': [
                    "SYN flood attack",
                    "DNS amplification",
                    "Distributed botnet attack"
                ]
            }
        else:
            return {
                'title': 'DoS Mitigation',
                'examples': [
                    "Implement rate limiting",
                    "Use CDN and DDoS protection services",
                    "Configure firewall rules"
                ]
            }
    
    def _get_password_corrections(self, role):
        if role == 'attacker':
            return {
                'title': 'Password Attack Methods',
                'examples': [
                    "Dictionary attack with common passwords",
                    "Brute force with tools like hashcat",
                    "Rainbow table attacks"
                ]
            }
        else:
            return {
                'title': 'Strong Password Requirements',
                'examples': [
                    "Minimum 12 characters",
                    "Mix of uppercase, lowercase, numbers, and symbols",
                    "No common words or patterns"
                ]
            }
    
    def _get_server_config_corrections(self, role):
        if role == 'attacker':
            return {
                'title': 'Server Exploitation Methods',
                'examples': [
                    "Scan for exposed services with nmap",
                    "Check for default credentials",
                    "Look for unpatched vulnerabilities"
                ]
            }
        else:
            return {
                'title': 'Server Hardening',
                'examples': [
                    "Close unnecessary ports",
                    "Use strong authentication",
                    "Keep software updated",
                    "Enable encryption (HTTPS/TLS)"
                ]
            }

# Global instance
challenge_engine = ChallengeEngine()
