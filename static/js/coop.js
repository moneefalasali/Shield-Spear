// Co-op Mode JavaScript

let socket = null;
let currentSession = null;

// Initialize WebSocket
function initializeWebSocket() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
    });
    
    socket.on('session_created', function(data) {
        currentSession = data;
        showNotification('Session created: ' + data.session_id, 'success');
    });
    
    socket.on('player_joined', function(data) {
        showNotification(data.username + ' joined the session', 'info');
    });
    
    socket.on('challenge_completed', function(data) {
        showNotification(data.username + ' completed the challenge!', 'success');
    });
    
    socket.on('error', function(error) {
        showNotification('Error: ' + error, 'error');
    });
}

// Load co-op challenges
async function loadCoopChallenges() {
    const grid = document.getElementById('challenges-grid');
    grid.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading challenges...</p></div>';
    
    try {
        const response = await fetch('/api/challenges?category=coop');
        const challenges = await response.json();
        displayCoopChallenges(challenges);
    } catch (error) {
        grid.innerHTML = '<p>Failed to load challenges</p>';
        console.error('Error:', error);
    }
}

// Display co-op challenges
function displayCoopChallenges(challenges) {
    const grid = document.getElementById('challenges-grid');
    grid.innerHTML = '';

    if (!challenges || challenges.length === 0) {
        grid.innerHTML = '<p>No co-op challenges available yet</p>';
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

// Show create session modal
function showCreateSessionModal(mode) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <h2>Create ${mode === 'cooperative' ? 'Cooperative' : 'Competitive'} Session</h2>
            <p>Session Mode: ${mode}</p>
            <button class="btn btn-primary" onclick="createSession('${mode}')">Create</button>
            <button class="btn btn-outline" onclick="this.parentElement.parentElement.remove()">Cancel</button>
        </div>
    `;
    document.body.appendChild(modal);
}

// Create session
async function createSession(mode) {
    try {
        const response = await fetchAPI('/coop/session', {
            method: 'POST',
            body: JSON.stringify({ mode })
        });
        if (response.success) {
            currentSession = response.data;
            showNotification('Session created successfully!', 'success');
            if (socket) socket.emit('join_session', { session_id: response.data.session_id });
        }
    } catch (error) {
        showNotification('Failed to create session', 'error');
    }
}

// Start challenge (same as challenges.js)
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

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeWebSocket();
});

console.log('Coop.js loaded');
