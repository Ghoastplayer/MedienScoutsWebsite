console.log('base.js loaded');

// Hide flash messages after 4 seconds
setTimeout(function() {
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        alert.style.display = 'none';
    });
}, 5000);

// Auto Logout after 3min in background
let logoutTimer;

const isAuthenticated = JSON.parse('{{ current_user.is_authenticated | tojson | safe }}');

function resetLogoutTimer() {
    clearTimeout(logoutTimer);
    logoutTimer = setTimeout(logoutUser, 180000); // 180000 ms = 3 minutes
}

function logoutUser() {
    if (isAuthenticated) {
        window.location.href = "{{ url_for('logout') }}";
    }
}

// Reset the timer on any of these events
window.onload = resetLogoutTimer;
document.onmousemove = resetLogoutTimer;
document.onkeypress = resetLogoutTimer;
document.onscroll = resetLogoutTimer;
document.onclick = resetLogoutTimer;

window.onload = console.log('base_scripts.js loaded');