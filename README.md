# Cybersecurity Simulator - محاكي الأمن السيبراني

## نظرة عامة

محاكي الأمن السيبراني هو منصة تعليمية تفاعلية لتعلم مفاهيم الأمن السيبراني من خلال التحديات العملية. يوفر التطبيق محاكاة واقعية لهجمات الأمن السيبراني وطرق الدفاع ضدها.

## الميزات الرئيسية

### 1. **التحديات المتنوعة - 26+ تحدي**

#### تحديات Red Team (الهجوم):
- SQL Injection (3 مستويات: Basic, UNION, Blind)
- Cross-Site Scripting - XSS (3 مستويات)
- Denial of Service - DoS (3 مستويات)
- Password Cracking (2 مستويات)
- CSRF Attack
- Command Injection
- Race Condition

#### تحديات Blue Team (الدفاع):
- SQL Injection Defense (2 مستويات)
- XSS Defense (2 مستويات)
- DoS Defense (2 مستويات)
- Password Security
- CSRF Defense
- Command Injection Defense

#### تحديات Co-op (التعاون):
- دفاع جماعي ضد هجمات متعددة
- اختراق أمني تعاوني
- Incident Response

### 2. **محاكاة واقعية**
- ✅ نظام تقييم ذكي يفحص الحلول بشكل تفصيلي
- ✅ محاكاة قاعدة بيانات حقيقية لاختبار SQL Injection
- ✅ تقييم متعدد المستويات (Easy, Medium, Hard)
- ✅ Feedback مفصل مع نصائح للتحسين

## التثبيت والتشغيل

```bash
# 1. استخراج المشروع
unzip cybersecurity_simulator.zip
cd cybersecurity_simulator

# 2. تثبيت المتطلبات
pip install -r requirements.txt

# 3. تشغيل التطبيق
python run.py

# 4. فتح المتصفح على
http://localhost:5000

# 5. تسجيل الدخول
Username: admin
Password: admin123
```

## المتطلبات
- Python 3.11+
- Flask 2.3+
- SQLite
- المتطلبات في requirements.txt

## بنية المشروع

```
cybersecurity_simulator/
├── app/
│   ├── challenge_simulator.py   # محرك المحاكاة الواقعية (NEW!)
│   ├── models.py                # نماذج قاعدة البيانات
│   ├── routes.py                # المسارات (UPDATED)
│   └── events.py                # WebSocket events (UPDATED)
├── templates/
│   └── attempt.html             # صفحة التحدي (NEW!)
├── init_challenges.py           # 26+ تحدي شامل (NEW!)
└── run.py                       # نقطة الدخول (UPDATED)
```

## أمثلة على الحلول

### SQL Injection (Red Team)
```sql
admin' OR '1'='1'--
' UNION SELECT username, password FROM users--
```

### XSS (Red Team)
```html
<script>alert('XSS')</script>
<img src=x onerror=alert(document.cookie)>
```

### Password Strength (Blue Team)
```
MyP@ssw0rd2024!
```

**استمتع بالتعلم! 🎓🔐**
