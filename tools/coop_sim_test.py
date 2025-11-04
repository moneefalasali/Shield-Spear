"""
Simple test harness to simulate a coop session with one human and one bot using BotAI + challenge_simulator.
Run with:
    $env:PYTHONPATH = 'C:\cybersecurity_simulator'; .\venv\Scripts\python.exe .\tools\coop_sim_test.py
"""
from app.bot_ai import BotAI
from app.challenge_simulator import challenge_simulator


def run_sim():
    bot = BotAI(difficulty='medium', role='attacker')
    challenge_type = 'sql_injection'
    state = {'bot_step': 0}

    print('Starting simulated duel (human vs bot)')
    human_score = 0
    bot_score = 0

    for tick in range(4):
        # human does a sample action
        human_payload = "probe with ' OR '1'='1' --"
        result_h = challenge_simulator.evaluate_challenge(challenge_type, human_payload, 'medium')
        human_score += result_h.get('score', 0)
        print(f'[Human] payload="{human_payload}" -> success={result_h["success"]} score={result_h["score"]} msg={result_h.get("feedback")}')

        # bot decides
        action = bot.get_next_action(challenge_type, state)
        bot_payload = action.get('description', 'bot action')
        result_b = challenge_simulator.evaluate_challenge(challenge_type, bot_payload, 'medium')
        bot_score += result_b.get('score', 0)
        print(f'[Bot] action="{action["action"]}" desc="{bot_payload}" -> success={result_b["success"]} score={result_b["score"]}')

        state['bot_step'] = state.get('bot_step', 0) + 1

    print('Simulation complete')
    print('Scores: Human=', human_score, ' Bot=', bot_score)

if __name__ == '__main__':
    run_sim()
