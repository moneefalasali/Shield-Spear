"""
Challenge Definitions - 5 Pre-built Challenges
Each challenge available in both attack and defense modes
"""

def get_challenges():
    """Return list of 5 pre-built challenges"""
    
    challenges = []
    
    # 1. SQL Injection Challenges
    challenges.extend([
        {
            'title': 'SQL Injection Attack',
            'description': 'Exploit SQL injection vulnerability to bypass authentication and extract sensitive data from the database.',
            'category': 'red',
            'difficulty': 'easy',
            'challenge_type': 'sql_injection',
            'max_score': 100,
            'time_limit': 300,
            'hints': [
                'Try using single quotes to break the SQL syntax',
                'Use OR conditions to create always-true statements',
                'Comment out the rest of the query with -- or #'
            ],
            'solution_explanation': 'SQL Injection allows attackers to manipulate SQL queries by injecting malicious input. Common techniques include using quotes to break syntax, OR conditions for boolean bypasses, and UNION SELECT for data extraction.'
        },
        {
            'title': 'SQL Injection Defense',
            'description': 'Implement security measures to prevent SQL injection attacks. Use parameterized queries, input validation, and proper access controls.',
            'category': 'blue',
            'difficulty': 'easy',
            'challenge_type': 'sql_injection',
            'max_score': 100,
            'time_limit': 300,
            'hints': [
                'Use parameterized queries or prepared statements',
                'Implement input validation and sanitization',
                'Apply the principle of least privilege to database accounts'
            ],
            'solution_explanation': 'Preventing SQL injection requires multiple layers of defense including parameterized queries, input validation, proper escaping, and database permission controls.'
        }
    ])
    
    # 2. XSS Attack Challenges
    challenges.extend([
        {
            'title': 'Cross-Site Scripting (XSS) Attack',
            'description': 'Inject malicious JavaScript code to steal cookies, session tokens, or manipulate the webpage.',
            'category': 'red',
            'difficulty': 'medium',
            'challenge_type': 'xss',
            'max_score': 100,
            'time_limit': 300,
            'hints': [
                'Try injecting <script> tags',
                'Use event handlers like onerror or onload',
                'Attempt to access document.cookie'
            ],
            'solution_explanation': 'XSS attacks inject client-side scripts into web pages. Common vectors include <script> tags, event handlers (onerror, onload), and javascript: protocol handlers.'
        },
        {
            'title': 'XSS Defense',
            'description': 'Protect your web application from XSS attacks using proper encoding, Content Security Policy, and input validation.',
            'category': 'blue',
            'difficulty': 'medium',
            'challenge_type': 'xss',
            'max_score': 100,
            'time_limit': 300,
            'hints': [
                'Implement HTML encoding for all user input',
                'Use Content Security Policy (CSP) headers',
                'Validate and sanitize input on both client and server'
            ],
            'solution_explanation': 'XSS prevention requires HTML encoding output, implementing CSP, using secure frameworks with auto-escaping, and validating all user input.'
        }
    ])
    
    # 3. DoS Simulation Challenges
    challenges.extend([
        {
            'title': 'Denial of Service (DoS) Attack',
            'description': 'Simulate a DoS attack to overwhelm server resources and make services unavailable to legitimate users.',
            'category': 'red',
            'difficulty': 'medium',
            'challenge_type': 'dos',
            'max_score': 100,
            'time_limit': 300,
            'hints': [
                'Consider SYN flood attacks',
                'Use DNS amplification techniques',
                'Employ distributed attacks (DDoS)'
            ],
            'solution_explanation': 'DoS attacks overwhelm systems with traffic or resource consumption. Common techniques include SYN floods, amplification attacks, and distributed botnets.'
        },
        {
            'title': 'DoS Mitigation',
            'description': 'Implement defenses against DoS attacks including rate limiting, traffic filtering, and monitoring.',
            'category': 'blue',
            'difficulty': 'medium',
            'challenge_type': 'dos',
            'max_score': 100,
            'time_limit': 300,
            'hints': [
                'Implement rate limiting per IP address',
                'Use firewall rules to filter malicious traffic',
                'Consider using CDN services for DDoS protection'
            ],
            'solution_explanation': 'DoS mitigation requires rate limiting, traffic analysis, firewall rules, CDN services, and real-time monitoring to detect and respond to attacks.'
        }
    ])
    
    # 4. Password Strength Challenges
    challenges.extend([
        {
            'title': 'Password Cracking',
            'description': 'Attempt to crack weak passwords using dictionary attacks, brute force, or rainbow tables.',
            'category': 'red',
            'difficulty': 'easy',
            'challenge_type': 'password_strength',
            'max_score': 100,
            'time_limit': 300,
            'hints': [
                'Start with common dictionary words',
                'Try brute force with password cracking tools',
                'Use rainbow tables for hash attacks'
            ],
            'solution_explanation': 'Weak passwords can be cracked using dictionary attacks, brute force methods, and rainbow tables that pre-compute password hashes.'
        },
        {
            'title': 'Strong Password Policy',
            'description': 'Create a strong password that meets security requirements: minimum 12 characters, mixed case, numbers, and special characters.',
            'category': 'blue',
            'difficulty': 'easy',
            'challenge_type': 'password_strength',
            'max_score': 100,
            'time_limit': 300,
            'hints': [
                'Use at least 12 characters',
                'Mix uppercase, lowercase, numbers, and symbols',
                'Avoid common words and patterns'
            ],
            'solution_explanation': 'Strong passwords should be at least 12 characters long, contain mixed case letters, numbers, special characters, and avoid common patterns or dictionary words.'
        }
    ])
    
    # 5. Server Misconfiguration Challenges
    challenges.extend([
        {
            'title': 'Server Misconfiguration Exploitation',
            'description': 'Identify and exploit server misconfigurations such as exposed admin panels, open ports, and default credentials.',
            'category': 'red',
            'difficulty': 'hard',
            'challenge_type': 'server_config',
            'max_score': 100,
            'time_limit': 300,
            'hints': [
                'Scan for open ports and services',
                'Look for exposed admin interfaces',
                'Try default credentials'
            ],
            'solution_explanation': 'Server misconfigurations include exposed services, open unnecessary ports, default credentials, unpatched software, and publicly accessible admin panels.'
        },
        {
            'title': 'Server Hardening',
            'description': 'Secure the server by closing unnecessary ports, updating software, enabling authentication, and implementing encryption.',
            'category': 'blue',
            'difficulty': 'hard',
            'challenge_type': 'server_config',
            'max_score': 100,
            'time_limit': 300,
            'hints': [
                'Close all unnecessary open ports',
                'Secure admin interfaces with strong authentication',
                'Enable HTTPS/TLS encryption',
                'Keep software updated with latest patches'
            ],
            'solution_explanation': 'Server hardening requires closing unnecessary ports, implementing strong authentication, enabling encryption, keeping software updated, and following security best practices.'
        }
    ])
    
    # Add Co-op challenge that can be played with either role
    challenges.append({
        'title': 'Co-op Security Challenge',
        'description': 'Team up with a friend to attack or defend together in real-time. One player acts as attacker, the other as defender.',
        'category': 'coop',
        'difficulty': 'medium',
        'challenge_type': 'sql_injection',  # Can be any type, will be selected during session creation
        'max_score': 150,
        'time_limit': 600,
        'hints': [
            'Coordinate with your partner',
            'Use the live event log to track actions',
            'Adapt your strategy based on opponent moves'
        ],
        'solution_explanation': 'Co-op mode requires teamwork and real-time coordination. Communicate effectively and adapt your strategy based on your partner and opponent actions.'
    })
    
    return challenges
