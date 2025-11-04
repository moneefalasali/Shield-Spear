"""
Realistic Challenge Simulator
Provides a realistic simulation of cybersecurity attacks and defenses for challenges.
"""

import re
import time
import hashlib
import sqlite3
from datetime import datetime
import random
import string


class ChallengeSimulator:
    """محاكي شامل للتحديات الأمنية"""
    
    def __init__(self):
        self.simulation_results = []
        
    def evaluate_challenge(self, challenge_type, user_input, difficulty='medium'):
        """
        تقييم حل التحدي بناءً على نوعه
        
        Args:
            challenge_type: نوع التحدي (sql_injection, xss, dos, password_check, etc.)
            user_input: الحل المقدم من المستخدم
            difficulty: مستوى الصعوبة (easy, medium, hard)
            
        Returns:
            dict: نتيجة التقييم مع التفاصيل
        """
        
        evaluators = {
            'sql_injection': self.evaluate_sql_injection,
            'sql_injection_defense': self.evaluate_sql_defense,
            'xss': self.evaluate_xss,
            'xss_defense': self.evaluate_xss_defense,
            'dos': self.evaluate_dos,
            'dos_defense': self.evaluate_dos_defense,
            'password_check': self.evaluate_password_strength,
            'password_cracking': self.evaluate_password_cracking,
            'csrf': self.evaluate_csrf,
            'csrf_defense': self.evaluate_csrf_defense,
            'command_injection': self.evaluate_command_injection,
            'command_injection_defense': self.evaluate_command_injection_defense,
        }
        
        evaluator = evaluators.get(challenge_type)
        if not evaluator:
            return {
                'success': False,
                'score': 0,
                'feedback': 'Unknown challenge type',
                'errors': ['Challenge type not recognized']
            }
        
        return evaluator(user_input, difficulty)
    
    # ==================== SQL INJECTION ====================
    
    def evaluate_sql_injection(self, user_input, difficulty='medium'):
        """تقييم هجوم SQL Injection (Red Team)"""
        
        score = 0
        max_score = 100
        feedback = []
        errors = []
        is_correct = False
        
        # تحقق من العناصر الأساسية لهجوم SQL Injection
        sql_keywords = {
            'basic': ['UNION', 'SELECT', 'OR', '1=1'],
            'intermediate': ['DROP', 'INSERT', 'UPDATE', 'DELETE', '--', '#'],
            'advanced': ['WAITFOR', 'DELAY', 'BENCHMARK', 'SLEEP', 'LOAD_FILE']
        }
        
        user_input_upper = user_input.upper()
        
        # Basic SQL Injection
        if any(keyword in user_input_upper for keyword in sql_keywords['basic']):
            score += 30
            feedback.append('✓ Basic SQL keywords detected')
            is_correct = True
        else:
            errors.append('No basic SQL keywords detected')
        
        # UNION-based injection
        if 'UNION' in user_input_upper and 'SELECT' in user_input_upper:
            score += 25
            feedback.append('✓ Proper UNION SELECT usage detected')
        
        # Boolean-based blind injection
        if "OR" in user_input_upper and ("1=1" in user_input or "TRUE" in user_input_upper):
            score += 20
            feedback.append('✓ Boolean-based injection used')
        
        # Comment injection
        if '--' in user_input or '#' in user_input or '/*' in user_input:
            score += 15
            feedback.append('✓ Comments used to bypass checks')
        
        # Advanced techniques (for hard difficulty)
        if difficulty == 'hard':
            if any(keyword in user_input_upper for keyword in sql_keywords['advanced']):
                score += 10
                feedback.append('✓ Advanced SQL techniques used')
        
        # المحاكاة: تنفيذ SQL على قاعدة بيانات وهمية
        try:
            simulation_result = self._simulate_sql_injection(user_input)
            if simulation_result['vulnerable']:
                feedback.append(f'✓ Attack succeeded! Extracted: {simulation_result["data_extracted"]}')
            else:
                errors.append('Attack failed to extract data')
        except Exception as e:
            errors.append(f'Simulation error: {str(e)}')
        
        return {
            'success': is_correct,
            'score': min(score, max_score),
                'feedback': '\n'.join(feedback) if feedback else 'No valid SQL Injection attack detected',
            'errors': errors,
            'details': {
                'attack_type': 'SQL Injection',
                'techniques_used': feedback
            }
        }
    
    def _simulate_sql_injection(self, payload):
        """محاكاة تنفيذ SQL Injection على قاعدة بيانات وهمية"""
        
        # إنشاء قاعدة بيانات وهمية في الذاكرة
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        # إنشاء جدول مستخدمين وهمي
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                password TEXT,
                email TEXT,
                is_admin INTEGER
            )
        ''')
        
        # إدراج بيانات وهمية
        test_users = [
            (1, 'admin', 'admin123', 'admin@test.com', 1),
            (2, 'user1', 'pass123', 'user1@test.com', 0),
            (3, 'user2', 'secret456', 'user2@test.com', 0),
        ]
        cursor.executemany('INSERT INTO users VALUES (?,?,?,?,?)', test_users)
        conn.commit()
        
        vulnerable = False
        data_extracted = []
        
        try:
            # محاولة تنفيذ الـ payload (استعلام ضعيف)
            # في الواقع، هذا الكود ضعيف أمنياً - لأغراض المحاكاة فقط!
            query = f"SELECT * FROM users WHERE username = '{payload}' AND password = 'test'"
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            if results:
                vulnerable = True
                data_extracted = [f"User: {row[1]}, Email: {row[3]}" for row in results]
        except sqlite3.Error:
            # إذا حدث خطأ في SQL، قد يكون الـ payload صحيح ولكن بناء الجملة خاطئ
            if 'UNION' in payload.upper() or 'OR' in payload.upper():
                vulnerable = True
                data_extracted = ['SQL Error - but injection detected']
        finally:
            conn.close()
        
        return {
            'vulnerable': vulnerable,
            'data_extracted': ', '.join(data_extracted) if data_extracted else 'None'
        }
    
    def evaluate_sql_defense(self, user_input, difficulty='medium'):
        """تقييم الدفاع ضد SQL Injection (Blue Team)"""
        
        score = 0
        max_score = 100
        feedback = []
        errors = []
        is_correct = False
        
        defense_techniques = {
            'prepared_statements': ['prepare', 'bind', 'placeholder', '?', ':'],
            'input_validation': ['validate', 'sanitize', 'escape', 'filter', 'whitelist'],
            'parameterized': ['parameter', 'param', 'bind_param'],
            'orm': ['ORM', 'model', 'query builder'],
            'stored_procedures': ['procedure', 'stored', 'call']
        }
        
        user_input_lower = user_input.lower()
        
        # Prepared Statements / Parameterized Queries
        if any(keyword in user_input_lower for keyword in defense_techniques['prepared_statements']):
            score += 30
            feedback.append('✓ Used Prepared Statements')
            is_correct = True
        else:
            errors.append('Prepared Statements not detected')
        
        # Input Validation
        if any(keyword in user_input_lower for keyword in defense_techniques['input_validation']):
            score += 25
            feedback.append('✓ Applied Input Validation')
        else:
            errors.append('Input validation not applied')
        
        # Parameterized Queries
        if any(keyword in user_input_lower for keyword in defense_techniques['parameterized']):
            score += 20
            feedback.append('✓ Used Parameterized Queries')
        
        # ORM Usage
        if any(keyword in user_input_lower for keyword in defense_techniques['orm']):
            score += 15
            feedback.append('✓ Used ORM for protection')
        
        # Stored Procedures (for hard difficulty)
        if difficulty == 'hard':
            if any(keyword in user_input_lower for keyword in defense_techniques['stored_procedures']):
                score += 10
                feedback.append('✓ Used Stored Procedures')
        
        # تحقق من عدم وجود ثغرات
        vulnerable_patterns = ["'+", '"+', "OR 1=1", "OR '1'='1'", "UNION SELECT"]
        if not any(pattern.lower() in user_input_lower for pattern in vulnerable_patterns):
            score += 10
            feedback.append('✓ No vulnerable patterns detected')
        else:
            errors.append('⚠ Vulnerable patterns detected')
        
        return {
            'success': is_correct,
            'score': min(score, max_score),
                'feedback': '\n'.join(feedback) if feedback else 'Insufficient defenses against SQL Injection',
            'errors': errors,
            'details': {
                'defense_type': 'SQL Injection Protection',
                'techniques_applied': feedback
            }
        }
    
    # ==================== XSS (Cross-Site Scripting) ====================
    
    def evaluate_xss(self, user_input, difficulty='medium'):
        """تقييم هجوم XSS (Red Team)"""
        
        score = 0
        max_score = 100
        feedback = []
        errors = []
        is_correct = False
        
        # Reflected XSS
        if '<script>' in user_input.lower() or 'alert' in user_input.lower():
            score += 30
            feedback.append('✓ تم استخدام Reflected XSS')
            is_correct = True
        
        # Event handler XSS
        xss_events = ['onerror', 'onload', 'onclick', 'onmouseover', 'onfocus']
        if any(event in user_input.lower() for event in xss_events):
            score += 25
            feedback.append('✓ تم استخدام Event Handler XSS')
            is_correct = True
        
        # Image-based XSS
        if '<img' in user_input.lower() and 'src' in user_input.lower():
            score += 20
            feedback.append('✓ تم استخدام Image-based XSS')
        
        # JavaScript: protocol
        if 'javascript:' in user_input.lower():
            score += 15
            feedback.append('✓ تم استخدام JavaScript protocol')
        
        # Advanced: DOM-based or encoded XSS
        if difficulty == 'hard':
            if 'document.cookie' in user_input.lower() or 'localstorage' in user_input.lower():
                score += 10
                feedback.append('✓ تم استهداف بيانات المستخدم الحساسة')
        
        if not is_correct:
            errors.append('لم يتم اكتشاف payload XSS صحيح')
        
        return {
            'success': is_correct,
            'score': min(score, max_score),
            'feedback': '\n'.join(feedback) if feedback else 'لم يتم اكتشاف هجوم XSS صحيح',
            'errors': errors,
            'details': {
                'attack_type': 'Cross-Site Scripting (XSS)',
                'payload': user_input[:100]
            }
        }
    
    def evaluate_xss_defense(self, user_input, difficulty='medium'):
        """تقييم الدفاع ضد XSS (Blue Team)"""
        
        score = 0
        max_score = 100
        feedback = []
        errors = []
        is_correct = False
        
        defense_keywords = {
            'encoding': ['encode', 'escape', 'htmlspecialchars', 'htmlentities'],
            'csp': ['Content-Security-Policy', 'CSP', 'nonce'],
            'sanitize': ['sanitize', 'purify', 'clean', 'strip'],
            'validation': ['validate', 'whitelist', 'allowlist']
        }
        
        user_input_lower = user_input.lower()
        
        # HTML Encoding/Escaping
        if any(keyword in user_input_lower for keyword in defense_keywords['encoding']):
            score += 30
            feedback.append('✓ استخدام HTML Encoding/Escaping')
            is_correct = True
        else:
            errors.append('لم يتم استخدام HTML Encoding')
        
        # Content Security Policy
        if any(keyword in user_input for keyword in defense_keywords['csp']):
            score += 30
            feedback.append('✓ تطبيق Content Security Policy (CSP)')
        else:
            errors.append('لم يتم تطبيق CSP')
        
        # Input Sanitization
        if any(keyword in user_input_lower for keyword in defense_keywords['sanitize']):
            score += 25
            feedback.append('✓ تطبيق Input Sanitization')
        
        # Input Validation
        if any(keyword in user_input_lower for keyword in defense_keywords['validation']):
            score += 15
            feedback.append('✓ تطبيق Input Validation')
        
        return {
            'success': is_correct,
            'score': min(score, max_score),
            'feedback': '\n'.join(feedback) if feedback else 'لم يتم تطبيق دفاعات كافية ضد XSS',
            'errors': errors,
            'details': {
                'defense_type': 'XSS Protection',
                'techniques_applied': feedback
            }
        }
    
    # ==================== DoS (Denial of Service) ====================
    
    def evaluate_dos(self, user_input, difficulty='medium'):
        """تقييم هجوم DoS (Red Team)"""
        
        score = 0
        max_score = 100
        feedback = []
        errors = []
        is_correct = False
        
        dos_techniques = {
            'flood': ['flood', 'syn flood', 'udp flood', 'icmp flood'],
            'amplification': ['amplification', 'reflection', 'dns amplification'],
            'application': ['slowloris', 'slow http', 'http flood'],
            'distributed': ['botnet', 'distributed', 'ddos']
        }
        
        user_input_lower = user_input.lower()
        
        # Flood attacks
        if any(keyword in user_input_lower for keyword in dos_techniques['flood']):
            score += 30
            feedback.append('✓ تم وصف هجوم Flood')
            is_correct = True
        
        # Amplification attacks
        if any(keyword in user_input_lower for keyword in dos_techniques['amplification']):
            score += 25
            feedback.append('✓ تم وصف Amplification attack')
            is_correct = True
        
        # Application layer attacks
        if any(keyword in user_input_lower for keyword in dos_techniques['application']):
            score += 25
            feedback.append('✓ تم وصف Application layer attack')
            is_correct = True
        
        # DDoS
        if any(keyword in user_input_lower for keyword in dos_techniques['distributed']):
            score += 20
            feedback.append('✓ تم ذكر Distributed DoS')
        
        # محاكاة: عدد الطلبات
        request_count = user_input_lower.count('request') + user_input_lower.count('packet')
        if request_count > 5:
            score += 10
            feedback.append(f'✓ تم محاكاة {request_count} طلبات')
        
        if not is_correct:
            errors.append('لم يتم وصف هجوم DoS بشكل صحيح')
        
        return {
            'success': is_correct,
            'score': min(score, max_score),
            'feedback': '\n'.join(feedback) if feedback else 'لم يتم وصف هجوم DoS صحيح',
            'errors': errors,
            'details': {
                'attack_type': 'Denial of Service',
                'description': user_input[:200]
            }
        }
    
    def evaluate_dos_defense(self, user_input, difficulty='medium'):
        """تقييم الدفاع ضد DoS (Blue Team)"""
        
        score = 0
        max_score = 100
        feedback = []
        errors = []
        is_correct = False
        
        defense_techniques = {
            'rate_limiting': ['rate limit', 'throttle', 'limit requests'],
            'firewall': ['firewall', 'waf', 'iptables', 'filter'],
            'load_balancer': ['load balanc', 'distribute', 'scaling'],
            'cdn': ['cdn', 'cloudflare', 'content delivery'],
            'monitoring': ['monitor', 'detect', 'alert', 'intrusion detection']
        }
        
        user_input_lower = user_input.lower()
        
        # Rate Limiting
        if any(keyword in user_input_lower for keyword in defense_techniques['rate_limiting']):
            score += 30
            feedback.append('✓ تطبيق Rate Limiting')
            is_correct = True
        else:
            errors.append('لم يتم تطبيق Rate Limiting')
        
        # Firewall/WAF
        if any(keyword in user_input_lower for keyword in defense_techniques['firewall']):
            score += 25
            feedback.append('✓ استخدام Firewall/WAF')
        else:
            errors.append('لم يتم ذكر Firewall')
        
        # Load Balancing
        if any(keyword in user_input_lower for keyword in defense_techniques['load_balancer']):
            score += 20
            feedback.append('✓ استخدام Load Balancing')
        
        # CDN
        if any(keyword in user_input_lower for keyword in defense_techniques['cdn']):
            score += 15
            feedback.append('✓ استخدام CDN')
        
        # Monitoring
        if any(keyword in user_input_lower for keyword in defense_techniques['monitoring']):
            score += 10
            feedback.append('✓ تطبيق Monitoring & Detection')
        
        return {
            'success': is_correct,
            'score': min(score, max_score),
            'feedback': '\n'.join(feedback) if feedback else 'لم يتم تطبيق دفاعات كافية ضد DoS',
            'errors': errors,
            'details': {
                'defense_type': 'DoS Protection',
                'techniques_applied': feedback
            }
        }
    
    # ==================== PASSWORD CHECKING ====================
    
    def evaluate_password_strength(self, user_input, difficulty='medium'):
        """تقييم قوة كلمة المرور (Blue Team)"""
        
        score = 0
        max_score = 100
        feedback = []
        errors = []
        is_correct = False
        
        password = user_input.strip()
        
        # Length check
        if len(password) >= 8:
            score += 20
            feedback.append('✓ الطول مناسب (8+ أحرف)')
            is_correct = True
        else:
            errors.append('كلمة المرور قصيرة جداً (يجب أن تكون 8+ أحرف)')
        
        if difficulty in ['medium', 'hard'] and len(password) >= 12:
            score += 10
            feedback.append('✓ طول ممتاز (12+ أحرف)')
        
        # Uppercase letters
        if any(c.isupper() for c in password):
            score += 20
            feedback.append('✓ تحتوي على حروف كبيرة')
        else:
            errors.append('لا تحتوي على حروف كبيرة')
        
        # Lowercase letters
        if any(c.islower() for c in password):
            score += 20
            feedback.append('✓ تحتوي على حروف صغيرة')
        else:
            errors.append('لا تحتوي على حروف صغيرة')
        
        # Numbers
        if any(c.isdigit() for c in password):
            score += 20
            feedback.append('✓ تحتوي على أرقام')
        else:
            errors.append('لا تحتوي على أرقام')
        
        # Special characters
        special_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        if any(c in special_chars for c in password):
            score += 20
            feedback.append('✓ تحتوي على رموز خاصة')
        else:
            errors.append('لا تحتوي على رموز خاصة')
        
        # Check for common passwords
        common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein', '12345678']
        if password.lower() in common_passwords:
            score = max(0, score - 50)
            errors.append('⚠ كلمة مرور شائعة وضعيفة جداً!')
        
        return {
            'success': is_correct,
            'score': min(score, max_score),
            'feedback': '\n'.join(feedback) if feedback else 'كلمة مرور ضعيفة',
            'errors': errors,
            'details': {
                'password_length': len(password),
                'strength': 'strong' if score >= 80 else 'medium' if score >= 50 else 'weak'
            }
        }
    
    def evaluate_password_cracking(self, user_input, difficulty='medium'):
        """تقييم كسر كلمات المرور (Red Team)"""
        
        score = 0
        max_score = 100
        feedback = []
        errors = []
        is_correct = False
        
        cracking_techniques = {
            'dictionary': ['dictionary', 'wordlist', 'common passwords'],
            'brute_force': ['brute force', 'try all combinations', 'exhaustive'],
            'rainbow_table': ['rainbow table', 'precomputed', 'hash table'],
            'tools': ['hashcat', 'john', 'hydra', 'medusa']
        }
        
        user_input_lower = user_input.lower()
        
        # Dictionary attack
        if any(keyword in user_input_lower for keyword in cracking_techniques['dictionary']):
            score += 30
            feedback.append('✓ استخدام Dictionary Attack')
            is_correct = True
        
        # Brute Force
        if any(keyword in user_input_lower for keyword in cracking_techniques['brute_force']):
            score += 25
            feedback.append('✓ استخدام Brute Force')
            is_correct = True
        
        # Rainbow Tables
        if any(keyword in user_input_lower for keyword in cracking_techniques['rainbow_table']):
            score += 25
            feedback.append('✓ استخدام Rainbow Tables')
        
        # Cracking Tools
        if any(keyword in user_input_lower for keyword in cracking_techniques['tools']):
            score += 20
            feedback.append('✓ ذكر أدوات كسر كلمات المرور')
        
        if not is_correct:
            errors.append('لم يتم وصف طريقة كسر كلمات المرور بشكل صحيح')
        
        return {
            'success': is_correct,
            'score': min(score, max_score),
            'feedback': '\n'.join(feedback) if feedback else 'لم يتم وصف طريقة كسر صحيحة',
            'errors': errors,
            'details': {
                'attack_type': 'Password Cracking'
            }
        }
    
    # ==================== CSRF (Cross-Site Request Forgery) ====================
    
    def evaluate_csrf(self, user_input, difficulty='medium'):
        """تقييم هجوم CSRF (Red Team)"""
        
        score = 0
        max_score = 100
        feedback = []
        errors = []
        is_correct = False
        
        csrf_indicators = ['form', 'submit', 'post', 'request', 'cookie', 'session']
        
        user_input_lower = user_input.lower()
        
        # Basic CSRF understanding
        if 'csrf' in user_input_lower or 'cross-site request forgery' in user_input_lower:
            score += 30
            feedback.append('✓ فهم مفهوم CSRF')
            is_correct = True
        
        # Form-based attack
        if 'form' in user_input_lower and 'submit' in user_input_lower:
            score += 25
            feedback.append('✓ وصف هجوم عبر النماذج')
        
        # Session exploitation
        if 'session' in user_input_lower or 'cookie' in user_input_lower:
            score += 25
            feedback.append('✓ استغلال الجلسة/الكوكيز')
        
        # Automatic submission
        if 'automatic' in user_input_lower or 'javascript' in user_input_lower:
            score += 20
            feedback.append('✓ إرسال تلقائي للطلب')
        
        if not is_correct:
            errors.append('لم يتم وصف هجوم CSRF بشكل صحيح')
        
        return {
            'success': is_correct,
            'score': min(score, max_score),
            'feedback': '\n'.join(feedback) if feedback else 'لم يتم وصف هجوم CSRF صحيح',
            'errors': errors,
            'details': {
                'attack_type': 'CSRF'
            }
        }
    
    def evaluate_csrf_defense(self, user_input, difficulty='medium'):
        """تقييم الدفاع ضد CSRF (Blue Team)"""
        
        score = 0
        max_score = 100
        feedback = []
        errors = []
        is_correct = False
        
        defense_keywords = ['token', 'csrf token', 'synchronizer token', 'samesite', 'referer', 'origin']
        
        user_input_lower = user_input.lower()
        
        # CSRF Token
        if 'token' in user_input_lower:
            score += 40
            feedback.append('✓ استخدام CSRF Token')
            is_correct = True
        else:
            errors.append('لم يتم استخدام CSRF Token')
        
        # SameSite Cookie
        if 'samesite' in user_input_lower:
            score += 30
            feedback.append('✓ استخدام SameSite Cookie')
        
        # Referer/Origin Check
        if 'referer' in user_input_lower or 'origin' in user_input_lower:
            score += 30
            feedback.append('✓ التحقق من Referer/Origin')
        
        return {
            'success': is_correct,
            'score': min(score, max_score),
            'feedback': '\n'.join(feedback) if feedback else 'لم يتم تطبيق دفاعات كافية ضد CSRF',
            'errors': errors,
            'details': {
                'defense_type': 'CSRF Protection'
            }
        }
    
    # ==================== COMMAND INJECTION ====================
    
    def evaluate_command_injection(self, user_input, difficulty='medium'):
        """تقييم هجوم Command Injection (Red Team)"""
        
        score = 0
        max_score = 100
        feedback = []
        errors = []
        is_correct = False
        
        command_operators = [';', '|', '&', '&&', '||', '`', '$']
        dangerous_commands = ['ls', 'cat', 'rm', 'chmod', 'wget', 'curl', 'nc', 'sh', 'bash']
        
        # Check for command operators
        if any(op in user_input for op in command_operators):
            score += 30
            feedback.append('✓ استخدام command operators')
            is_correct = True
        
        # Check for dangerous commands
        if any(cmd in user_input.lower() for cmd in dangerous_commands):
            score += 40
            feedback.append('✓ استخدام أوامر نظام خطيرة')
        
        # Command chaining
        if '&&' in user_input or '||' in user_input:
            score += 30
            feedback.append('✓ ربط أوامر متعددة')
        
        if not is_correct:
            errors.append('لم يتم اكتشاف Command Injection صحيح')
        
        return {
            'success': is_correct,
            'score': min(score, max_score),
            'feedback': '\n'.join(feedback) if feedback else 'لم يتم اكتشاف Command Injection صحيح',
            'errors': errors,
            'details': {
                'attack_type': 'Command Injection'
            }
        }
    
    def evaluate_command_injection_defense(self, user_input, difficulty='medium'):
        """تقييم الدفاع ضد Command Injection (Blue Team)"""
        
        score = 0
        max_score = 100
        feedback = []
        errors = []
        is_correct = False
        
        defense_keywords = {
            'validation': ['validate', 'whitelist', 'allowlist', 'filter'],
            'escaping': ['escape', 'sanitize', 'escapeshellarg', 'escapeshellcmd'],
            'avoid_shell': ['avoid shell', 'direct execution', 'subprocess', 'exec array']
        }
        
        user_input_lower = user_input.lower()
        
        # Input Validation
        if any(keyword in user_input_lower for keyword in defense_keywords['validation']):
            score += 35
            feedback.append('✓ تطبيق Input Validation')
            is_correct = True
        else:
            errors.append('لم يتم تطبيق Input Validation')
        
        # Shell Escaping
        if any(keyword in user_input_lower for keyword in defense_keywords['escaping']):
            score += 35
            feedback.append('✓ استخدام Shell Escaping')
        
        # Avoid Shell Execution
        if any(keyword in user_input_lower for keyword in defense_keywords['avoid_shell']):
            score += 30
            feedback.append('✓ تجنب تنفيذ Shell مباشرة')
        
        return {
            'success': is_correct,
            'score': min(score, max_score),
            'feedback': '\n'.join(feedback) if feedback else 'لم يتم تطبيق دفاعات كافية ضد Command Injection',
            'errors': errors,
            'details': {
                'defense_type': 'Command Injection Protection'
            }
        }


# إنشاء instance عام
challenge_simulator = ChallengeSimulator()
