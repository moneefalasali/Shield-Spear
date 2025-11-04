// Challenges Page JavaScript

// Load challenges
async function loadChallenges(teamType) {
    const grid = document.getElementById('challenges-grid');
    grid.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading challenges...</p></div>';

    try {
        // use 'category' instead of 'team'
        const response = await fetch(`/api/challenges?category=${teamType}`);
        const challenges = await response.json();

        displayChallenges(challenges, teamType);
    } catch (error) {
        grid.innerHTML = '<p>Failed to load challenges</p>';
        console.error('Error loading challenges:', error);
    }
}

// Display challenges
function displayChallenges(challenges, teamType) {
    const grid = document.getElementById('challenges-grid');
    grid.innerHTML = '';

    if (!challenges || challenges.length === 0) {
        grid.innerHTML = '<p>No challenges available</p>';
        return;
    }

    challenges.forEach(challenge => {
        const card = document.createElement('div');
        card.className = 'challenge-card';
        card.innerHTML = `
            <div class="challenge-header">
                <div>
                    <div class="challenge-title">${challenge.title}</div>
                    <span class="challenge-difficulty difficulty-${challenge.difficulty}">${challenge.difficulty}</span>
                </div>
            </div>
            <p class="challenge-description">${challenge.description}</p>
            <div class="challenge-meta">
                <span class="challenge-points">${challenge.max_score} points</span>
                <button class="btn btn-primary btn-small" onclick="startChallenge('${challenge.id}')">Start</button>
            </div>
        `;
        grid.appendChild(card);
    });
}

// Start challenge
async function startChallenge(challengeId) {
    try {
        const response = await fetch(`/challenges/${challengeId}/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();

        if (data.success && data.attempt_id) {
            // redirect to the new attempt page
            window.location.href = `/challenges/attempt/${data.attempt_id}`;
        } else if (data.error) {
            alert(data.error);
        } else {
            alert('Unexpected error');
        }
    } catch (error) {
        alert('Failed to start challenge. Please try again.');
        console.error('Error starting challenge:', error);
    }
}

console.log('Challenges.js loaded');
