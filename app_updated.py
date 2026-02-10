from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps
import json
from datetime import datetime, timedelta
from notifications import notification_manager

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production

def get_db_connection():
    conn = sqlite3.connect('data/timetable.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Schedule table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            day TEXT NOT NULL,
            time TEXT NOT NULL,
            datetime TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Tasks table with priority
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            deadline TIMESTAMP,
            priority INTEGER DEFAULT 0,  # 0=low, 1=medium, 2=high, 3=urgent
            completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Initialize database
init_db()

# ===== AUTH ROUTES =====

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        hashed_password = generate_password_hash(password)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                         (username, email, hashed_password))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            session['user_id'] = user_id
            session['username'] = username
            session['email'] = email
            
            flash('Registration successful!', 'success')
            return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'error')
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

# ===== DASHBOARD & SCHEDULE ROUTES =====

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    user_id = session.get('user_id')
    
    # Get today's schedule
    cursor.execute('''
        SELECT * FROM schedule 
        WHERE user_id = ? AND date(datetime) = date('now')
        ORDER BY datetime
    ''', (user_id,))
    today_schedule = cursor.fetchall()
    
    # Get upcoming tasks
    cursor.execute('''
        SELECT * FROM tasks 
        WHERE user_id = ? AND completed = 0 AND deadline > datetime('now')
        ORDER BY deadline LIMIT 5
    ''', (user_id,))
    upcoming_tasks = cursor.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         today_schedule=today_schedule,
                         upcoming_tasks=upcoming_tasks)

@app.route('/schedule')
@login_required
def schedule():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    user_id = session.get('user_id')
    cursor.execute('SELECT * FROM schedule WHERE user_id = ? ORDER BY datetime', (user_id,))
    schedule_items = cursor.fetchall()
    
    conn.close()
    return render_template('schedule.html', schedule=schedule_items)

@app.route('/add_schedule', methods=['POST'])
@login_required
def add_schedule():
    title = request.form.get('title')
    description = request.form.get('description')
    day = request.form.get('day')
    time = request.form.get('time')
    
    # Combine day and time into datetime
    datetime_str = f"{day} {time}:00"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO schedule (user_id, title, description, day, time, datetime)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session.get('user_id'), title, description, day, time, datetime_str))
    
    conn.commit()
    conn.close()
    
    flash('Schedule item added successfully!', 'success')
    return redirect(url_for('schedule'))

@app.route('/delete_schedule/<int:id>')
@login_required
def delete_schedule(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM schedule WHERE id = ? AND user_id = ?', 
                  (id, session.get('user_id')))
    conn.commit()
    conn.close()
    
    flash('Schedule item deleted successfully!', 'success')
    return redirect(url_for('schedule'))

# ===== TASKS ROUTES =====

@app.route('/tasks')
@login_required
def tasks():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    user_id = session.get('user_id')
    cursor.execute('SELECT * FROM tasks WHERE user_id = ? ORDER BY deadline', (user_id,))
    tasks_list = cursor.fetchall()
    
    conn.close()
    return render_template('tasks.html', tasks=tasks_list)

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    title = request.form.get('title')
    description = request.form.get('description')
    deadline = request.form.get('deadline')
    priority = request.form.get('priority', 0)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks (user_id, title, description, deadline, priority, completed)
        VALUES (?, ?, ?, ?, ?, 0)
    ''', (session.get('user_id'), title, description, deadline, priority))
    
    conn.commit()
    conn.close()
    
    flash('Task added successfully!', 'success')
    return redirect(url_for('tasks'))

@app.route('/complete_task/<int:id>')
@login_required
def complete_task(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET completed = 1 WHERE id = ? AND user_id = ?', 
                  (id, session.get('user_id')))
    conn.commit()
    conn.close()
    
    flash('Task marked as completed!', 'success')
    return redirect(url_for('tasks'))

@app.route('/delete_task/<int:id>')
@login_required
def delete_task(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', 
                  (id, session.get('user_id')))
    conn.commit()
    conn.close()
    
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('tasks'))

# ===== NOTIFICATION ROUTES =====

@app.route('/notification_settings', methods=['GET', 'POST'])
@login_required
def notification_settings():
    """Notification configuration page"""
    if request.method == 'POST':
        smtp_server = request.form.get('smtp_server')
        smtp_port = int(request.form.get('smtp_port', 587))
        sender_email = request.form.get('sender_email')
        sender_password = request.form.get('sender_password')
        enabled = 'notification_enabled' in request.form
        
        notification_manager.update_config(
            smtp_server, smtp_port, sender_email, sender_password, enabled
        )
        flash('Notification settings updated successfully!', 'success')
        return redirect(url_for('notification_settings'))
    
    return render_template('notification_settings.html', config=notification_manager.config)

@app.route('/send_test_email')
@login_required
def send_test_email():
    """Send test email to current user"""
    user_email = session.get('email', '')
    if user_email:
        subject = "Test Notification - Smart Timetable App"
        message = """
        <html>
        <body>
            <h2>Test Notification Successful!</h2>
            <p>This is a test email from your Smart Timetable App.</p>
            <p>Your notification system is working correctly.</p>
            <p>You will receive reminders for:</p>
            <ul>
                <li>Upcoming classes</li>
                <li>Assignment deadlines</li>
                <li>Exam schedules</li>
            </ul>
        </body>
        </html>
        """
        
        if notification_manager.send_email_notification(user_email, subject, message):
            flash('Test email sent successfully!', 'success')
        else:
            flash('Failed to send test email. Check your email settings.', 'error')
    else:
        flash('No email found in session. Please login again.', 'error')
    
    return redirect(url_for('notification_settings'))

@app.route('/check_upcoming')
@login_required
def check_upcoming():
    """Check and send notifications for upcoming items"""
    user_email = session.get('email', '')
    if not user_email:
        return jsonify({'error': 'No user email found'}), 400
    
    # Get user's schedule from database
    user_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get upcoming classes (next 24 hours)
    cursor.execute('''
        SELECT * FROM schedule 
        WHERE user_id = ? AND datetime > datetime('now') 
        AND datetime <= datetime('now', '+24 hours')
        ORDER BY datetime
    ''', (user_id,))
    schedule_items = cursor.fetchall()
    
    # Get upcoming tasks (next 24 hours)
    cursor.execute('''
        SELECT * FROM tasks 
        WHERE user_id = ? AND completed = 0 
        AND deadline > datetime('now') 
        AND deadline <= datetime('now', '+24 hours')
        ORDER BY deadline
    ''', (user_id,))
    task_items = cursor.fetchall()
    
    conn.close()
    
    # Convert schedule items
    schedule_data = []
    for item in schedule_items:
        schedule_data.append({
            'title': item['title'],
            'time': item['datetime'],
            'details': item.get('description', ''),
            'email': user_email
        })
    
    # Convert task items
    for item in task_items:
        schedule_data.append({
            'title': f"Task Due: {item['title']}",
            'time': item['deadline'],
            'details': item.get('description', ''),
            'email': user_email
        })
    
    # Check for upcoming items
    notifications = notification_manager.check_upcoming_schedule(schedule_data, hours_before=24)
    
    # Send notifications
    sent_count = notification_manager.send_bulk_notifications(notifications)
    
    return jsonify({
        'checked_items': len(schedule_data),
        'upcoming_notifications': len(notifications),
        'sent_count': sent_count,
        'message': f'Sent {sent_count} notification(s)'
    })

# ===== TASK PRIORITY ROUTES =====

@app.route('/task_priority')
@login_required
def task_priority():
    """Task priority management page"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    user_id = session.get('user_id')
    
    # Get tasks with priority information
    cursor.execute('''
        SELECT * FROM tasks 
        WHERE user_id = ? AND completed = 0
        ORDER BY priority DESC, deadline ASC
    ''', (user_id,))
    
    tasks = cursor.fetchall()
    conn.close()
    
    # Categorize tasks by priority
    urgent_important = [t for t in tasks if t.get('priority', 0) >= 3]
    important_not_urgent = [t for t in tasks if t.get('priority', 0) == 2]
    urgent_not_important = [t for t in tasks if t.get('priority', 0) == 1]
    not_urgent_not_important = [t for t in tasks if t.get('priority', 0) == 0]
    
    return render_template('task_priority.html',
                         urgent_important=urgent_important,
                         important_not_urgent=important_not_urgent,
                         urgent_not_important=urgent_not_important,
                         not_urgent_not_important=not_urgent_not_important)

@app.route('/update_task_priority/<int:task_id>', methods=['POST'])
@login_required
def update_task_priority(task_id):
    """Update task priority"""
    new_priority = request.form.get('priority', 0)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tasks SET priority = ? 
            WHERE id = ? AND user_id = ?
        ''', (new_priority, task_id, session.get('user_id')))
        
        conn.commit()
        conn.close()
        
        flash('Task priority updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating task: {str(e)}', 'error')
    
    return redirect(url_for('task_priority'))

# ===== CALENDAR ROUTES =====

@app.route('/calendar')
@login_required
def calendar():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    user_id = session.get('user_id')
    cursor.execute('SELECT * FROM schedule WHERE user_id = ?', (user_id,))
    events = cursor.fetchall()
    
    # Format events for FullCalendar
    calendar_events = []
    for event in events:
        calendar_events.append({
            'id': event['id'],
            'title': event['title'],
            'start': event['datetime'],
            'description': event.get('description', '')
        })
    
    conn.close()
    return render_template('calendar.html', events=json.dumps(calendar_events))

# ===== PROFILE ROUTES =====

@app.route('/profile')
@login_required
def profile():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (session.get('user_id'),))
    user = cursor.fetchone()
    conn.close()
    
    return render_template('profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (session.get('user_id'),))
    user = cursor.fetchone()
    
    # Verify current password if changing password
    if new_password and not check_password_hash(user['password'], current_password):
        flash('Current password is incorrect.', 'error')
        conn.close()
        return redirect(url_for('profile'))
    
    # Update user information
    if new_password:
        hashed_password = generate_password_hash(new_password)
        cursor.execute('''
            UPDATE users SET username = ?, email = ?, password = ?
            WHERE id = ?
        ''', (username, email, hashed_password, session.get('user_id')))
    else:
        cursor.execute('''
            UPDATE users SET username = ?, email = ?
            WHERE id = ?
        ''', (username, email, session.get('user_id')))
    
    conn.commit()
    conn.close()
    
    # Update session
    session['username'] = username
    session['email'] = email
    
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run(debug=True)