// Authentication JavaScript

// ✅ Password strength checker (optional visual enhancement)
function checkPasswordStrength(password) {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;
    return strength;
}

// ✅ Update password strength indicator (optional)
document.addEventListener('DOMContentLoaded', function() {
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const strength = checkPasswordStrength(this.value);
            const strengthText = document.getElementById('strength');
            if (strengthText) {
                const levels = ['Weak', 'Fair', 'Good', 'Strong', 'Very Strong'];
                strengthText.textContent = levels[strength] || 'Weak';
            }
        });
    }

    // ✅ KEEP signup handling if you use AJAX for signup
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }

    console.log("✅ Auth.js loaded successfully");
});

// ✅ We REMOVED the JS-based login handler completely
//    so that the form submits normally to Flask.

// ⚙️ Optional: keep this for AJAX-based signup only
async function handleSignup(e) {
    e.preventDefault();
    const formData = {
        full_name: document.getElementById('full_name').value,
        email: document.getElementById('email').value,
        username: document.getElementById('username').value,
        password: document.getElementById('password').value,
        confirm_password: document.getElementById('confirm_password').value
    };
    
    if (formData.password !== formData.confirm_password) {
        showNotification('Passwords do not match', 'error');
        return;
    }
    
    try {
        const response = await fetch('/auth/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            showNotification('Account created successfully!', 'success');
            setTimeout(() => window.location.href = '/auth/login', 1000);
        } else {
            const error = await response.json();
            showNotification(error.message || 'Signup failed', 'error');
        }
    } catch (error) {
        showNotification('Signup failed: ' + error.message, 'error');
    }
}

// ✅ Optional small notification helper (for alerts)
function showNotification(message, type = 'info') {
    alert(`${type.toUpperCase()}: ${message}`);
}
