"""
Attack test harness for Shield & Spear

Safe test script to simulate common attack payloads (SQLi, XSS, DoS, weak password)
against the local `challenge_engine` and to observe `BotAI` defender responses.

RUN ONLY IN YOUR LOCAL/TEST ENVIRONMENT. Do NOT use against systems you do not own.
"""

from app.challenge_engine import challenge_engine
from app.bot_ai import BotAI

TEST_PAYLOADS = {
    'sql_injection': [
        "admin' OR '1'='1'--",
        "' UNION SELECT username, password FROM users--",
        "' OR 1=1#",
    ],
    'xss': [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert(document.cookie)>",
        "<svg/onload=alert(1)>",
    ],
    'dos': [
        "flood 10000 requests",
        "SYN flood",
        "amplification reflection botnet",
    ],
    'password_strength': [
        "password123",
        "admin",
        "P@ssw0rd!",
    ],
    'server_config': [
        "nmap scan open ports 1-65535",
        "default credentials admin:admin",
        "exposed admin panel on /admin",
    ]
}


def run_attack_tests(difficulty='medium'):
    print("Running attack tests (difficulty=%s)" % difficulty)
    print("=" * 60)

    for challenge_type, payloads in TEST_PAYLOADS.items():
        print(f"\n== {challenge_type.upper()} ==")
        bot = BotAI(difficulty=difficulty, role='defender')

        for p_idx, payload in enumerate(payloads):
            print(f"\nPayload #{p_idx+1}: {payload}")

            # Evaluate with challenge engine as attacker
            result = challenge_engine.evaluate_challenge(challenge_type, payload, difficulty, role='attacker')
            print("Engine result:")
            print("  success:", result.get('success'))
            print("  score:", result.get('score'))
            print("  feedback:")
            for line in str(result.get('feedback', '')).split('\n'):
                print("    ", line)

            # Simulate defender bot responses for a few steps
            print("Bot defender actions:")
            for step in range(3):
                state = {'bot_step': step}
                action = bot.get_next_action(challenge_type, state)
                print(f"  step {step+1}: action={action.get('action')}, description={action.get('description')}, success={action.get('success')}")

    print("\nAll tests completed.")


if __name__ == '__main__':
    run_attack_tests(difficulty='medium')
