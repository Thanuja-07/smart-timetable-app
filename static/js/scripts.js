// Smart Timetable Web App - JavaScript Functions
// Replicates CLI functionality in web interface

document.addEventListener('DOMContentLoaded', function() {
    console.log('Smart Timetable Web App loaded');
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Update current date and time
    updateDateTime();
    setInterval(updateDateTime, 60000); // Update every minute
    
    // Initialize charts if any
    initializeProgressCharts();
    
    // Add keyboard shortcuts
    setupKeyboardShortcuts();
    
    // Setup auto-refresh for countdown page
    if (window.location.pathname === '/countdown') {
        setupCountdownAutoRefresh();
    }
});

// Update current date and time in the navbar
function updateDateTime() {
    const now = new Date();
    const dateTimeStr = now.toLocaleDateString('en-US', { 
        weekday: 'short', 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    // Update all datetime elements
    document.querySelectorAll('.current-datetime').forEach(el => {
        el.textContent = dateTimeStr;
    });
}

// Initialize progress charts (simple visualization)
function initializeProgressCharts() {
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const width = bar.style.width || bar.getAttribute('aria-valuenow') + '%';
        bar.style.width = '0%';
        
        // Animate progress bar
        setTimeout(() => {
            bar.style.width = width;
        }, 300);
    });
}

// Setup keyboard shortcuts for power users
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl+N or Cmd+N: Add new exam
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            window.location.href = '/add_exam';
        }
        
        // Ctrl+E or Cmd+E: Export CSV
        if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
            e.preventDefault();
            window.location.href = '/export_csv';
        }
        
        // Ctrl+R or Cmd+R: Refresh dashboard
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            if (!e.shiftKey) {
                // Allow normal refresh with Ctrl+R
                return;
            }
        }
        
        // Escape: Go back to dashboard
        if (e.key === 'Escape' && window.location.pathname !== '/') {
            window.location.href = '/';
        }
    });
}

// Setup auto-refresh for countdown timer
function setupCountdownAutoRefresh() {
    // Refresh page every 30 seconds to update countdown
    setInterval(() => {
        if (document.visibilityState === 'visible') {
            // Only update if page is visible
            updateStudySuggestion();
        }
    }, 30000);
}

// Update study suggestion via AJAX
function updateSuggestion() {
    fetch('/api/study_suggestion')
        .then(response => response.json())
        .then(data => {
            const suggestionElement = document.querySelector('.study-suggestion-text');
            if (suggestionElement) {
                // Add animation
                suggestionElement.style.opacity = '0';
                setTimeout(() => {
                    suggestionElement.textContent = data.suggestion;
                    suggestionElement.style.opacity = '1';
                    
                    // Show notification
                    showNotification('Study suggestion updated!', 'info');
                }, 300);
            }
        })
        .catch(error => {
            console.error('Error updating suggestion:', error);
            showNotification('Failed to update suggestion', 'danger');
        });
}

// Show notification toast
function showNotification(message, type = 'info') {
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    // Add to toast container
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 3000
    });
    toast.show();
    
    // Remove after hiding
    toastElement.addEventListener('hidden.bs.toast', function () {
        toastElement.remove();
    });
}

// Calculate study hours recommendation
function calculateStudyHours(daysUntil) {
    if (daysUntil <= 1) return '4-6 hours (High Intensity)';
    if (daysUntil <= 3) return '3-4 hours (Moderate Intensity)';
    if (daysUntil <= 7) return '2-3 hours (Regular)';
    if (daysUntil <= 14) return '1-2 hours (Light)';
    return '30-60 minutes (Maintenance)';
}

// Export current view as image (for presentations)
function exportAsImage() {
    showNotification('Export feature would capture the current view as an image.', 'info');
    // In a real implementation, you would use html2canvas library
    // html2canvas(document.body).then(canvas => {
    //     const link = document.createElement('a');
    //     link.download = 'timetable-dashboard.png';
    //     link.href = canvas.toDataURL();
    //     link.click();
    // });
}

// Simulate CLI commands for demonstration
function simulateCLI(command) {
    const cliOutput = document.getElementById('cli-output');
    if (!cliOutput) return;
    
    let response = '';
    
    switch(command) {
        case 'add_exam':
            response = 'Adding exam: Math Final\nDate: 2024-12-15\nSuccess: Exam added to timetable!';
            break;
        case 'show_exams':
            response = '1. Math Final (2024-12-15) - 15 days left\n2. Physics Midterm (2024-12-10) - 10 days left';
            break;
        case 'progress':
            response = 'Overall Progress: 65%\nMath: 80%\nPhysics: 50%';
            break;
        default:
            response = 'Command not recognized. Type "help" for available commands.';
    }
    
    cliOutput.innerHTML = `<pre class="text-success">$ smart-timetable ${command}\n${response}</pre>`;
}

// Quick add exam from dashboard
function quickAddExam(subject, daysFromNow = 7) {
    const date = new Date();
    date.setDate(date.getDate() + daysFromNow);
    const dateStr = date.toISOString().split('T')[0];
    
    // Show confirmation
    if (confirm(`Quick add ${subject} exam for ${dateStr}?`)) {
        // In a real implementation, you would submit a form
        showNotification(`Quick add: ${subject} exam scheduled for ${dateStr}`, 'success');
    }
}

// Start pomodoro timer
function startPomodoroTimer(minutes = 25) {
    let timeLeft = minutes * 60;
    const timerDisplay = document.getElementById('pomodoro-timer');
    
    if (!timerDisplay) {
        showNotification('Pomodoro timer started! Focus for ' + minutes + ' minutes.', 'info');
        return;
    }
    
    const timerInterval = setInterval(() => {
        const mins = Math.floor(timeLeft / 60);
        const secs = timeLeft % 60;
        
        timerDisplay.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        
        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            timerDisplay.textContent = 'Time\'s up!';
            showNotification('Pomodoro session complete! Take a 5-minute break.', 'success');
        }
        
        timeLeft--;
    }, 1000);
}

// Generate study schedule
function generateStudySchedule() {
    const subjects = ['Mathematics', 'Physics', 'Chemistry', 'Biology', 'Computer Science'];
    const schedule = [];
    
    const today = new Date();
    for (let i = 0; i < 7; i++) {
        const date = new Date(today);
        date.setDate(date.getDate() + i);
        const subject = subjects[i % subjects.length];
        const hours = i < 3 ? '2 hours' : '1.5 hours';
        
        schedule.push({
            date: date.toDateString(),
            subject: subject,
            duration: hours,
            focus: i < 2 ? 'New concepts' : 'Revision'
        });
    }
    
    // Display schedule
    let scheduleHTML = '<h5>Generated Weekly Study Schedule</h5><ul class="list-group">';
    schedule.forEach(item => {
        scheduleHTML += `
            <li class="list-group-item bg-dark text-light">
                <strong>${item.date}:</strong> ${item.subject} (${item.duration}) - ${item.focus}
            </li>
        `;
    });
    scheduleHTML += '</ul>';
    
    document.getElementById('schedule-output').innerHTML = scheduleHTML;
    showNotification('Weekly study schedule generated!', 'success');
}

// Share timetable
function shareTimetable() {
    const url = window.location.href;
    const text = 'Check out my Smart Timetable!';
    
    if (navigator.share) {
        navigator.share({
            title: 'Smart Timetable',
            text: text,
            url: url
        });
    } else {
        // Fallback: Copy to clipboard
        navigator.clipboard.writeText(url).then(() => {
            showNotification('Link copied to clipboard!', 'success');
        });
    }
}

// Dark/Light mode toggle
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    html.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    showNotification(`Switched to ${newTheme} mode`, 'info');
}

// Initialize theme from localStorage
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
}

// Call init theme
initTheme();