// Trials Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    loadUserStats();
});

// Load user statistics
async function loadUserStats() {
    try {
        const response = await fetchAPI('/user/profile');
        if (response.success) {
            // Update user stats in UI if needed
            console.log('User stats loaded:', response.data);
        }
    } catch (error) {
        console.error('Failed to load user stats:', error);
    }
}

console.log('Trials.js loaded');
