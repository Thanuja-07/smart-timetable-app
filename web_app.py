# SMART TIMETABLE WEB APP - ADD EXAM FIXED
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, flash
import json
import os
import csv
from datetime import datetime, timedelta
from io import StringIO

app = Flask(__name__)
app.secret_key = 'smart-timetable-2024'

EXAMS_FILE = 'data/exams.json'
PROGRESS_FILE = 'data/progress.json'

def init_files():
    os.makedirs('data', exist_ok=True)
    if not os.path.exists(EXAMS_FILE):
        with open(EXAMS_FILE, 'w') as f:
            json.dump([], f, indent=2)

def get_exams():
    try:
        with open(EXAMS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_exams(exams):
    with open(EXAMS_FILE, 'w') as f:
        json.dump(exams, f, indent=2)

# ===== ROUTES =====
@app.route('/')
def home():
    init_files()
    exams = get_exams()
    return render_template('index.html', exams=exams, github_stars=40)

@app.route('/add_exam', methods=['GET', 'POST'])
def add_exam():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        date = request.form.get('date', '').strip()
        subject = request.form.get('subject', '').strip()
        priority = request.form.get('priority', 'medium')
        
        # Validate
        if not name or not date or not subject:
            flash('❌ Please fill in all required fields', 'danger')
            return redirect('/add_exam')
        
        # Load existing exams
        exams = get_exams()
        
        # Check for duplicates
        if any(exam['name'].lower() == name.lower() for exam in exams):
            flash(f'❌ Exam "{name}" already exists!', 'warning')
            return redirect('/add_exam')
        
        # Add new exam
        new_exam = {
            'name': name,
            'date': date,
            'subject': subject,
            'priority': priority,
            'added': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        
        exams.append(new_exam)
        save_exams(exams)
        
        flash(f'✅ Exam "{name}" added successfully!', 'success')
        return redirect('/')
    
    # GET request - show the form
    return render_template('add_exam.html')

@app.route('/countdown')
def countdown():
    exams = get_exams()
    return render_template('countdown.html', exams=exams)

@app.route('/export_csv')
def export_csv():
    exams = get_exams()
    
    if not exams:
        flash('No exams to export. Load demo data first.', 'warning')
        return redirect('/')
    
    # Create CSV content
    csv_data = "Exam Name,Date,Subject,Priority,Added,Status\n"
    
    for exam in exams:
        # Calculate status
        try:
            exam_date = datetime.strptime(exam['date'], '%Y-%m-%d')
            days_until = (exam_date - datetime.now()).days
            
            if days_until < 0:
                status = "Completed"
            elif days_until == 0:
                status = "Today"
            elif days_until <= 7:
                status = "Urgent"
            else:
                status = "Upcoming"
        except:
            status = "Unknown"
        
        # Add row
        csv_data += f"{exam.get('name', '')},{exam.get('date', '')},{exam.get('subject', '')},{exam.get('priority', '')},{exam.get('added', '')},{status}\n"
    
    # Create response
    response = app.response_class(
        response=csv_data,
        status=200,
        mimetype='text/csv'
    )
    response.headers['Content-Disposition'] = 'attachment; filename=smart_timetable_export.csv'
    
    return response

@app.route('/demo')
def demo():
    # Create sample exams
    sample_exams = [
        {
            'name': 'Mathematics Final Exam',
            'date': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
            'subject': 'Mathematics',
            'priority': 'high',
            'added': datetime.now().strftime('%Y-%m-%d %H:%M')
        },
        {
            'name': 'Physics Midterm',
            'date': (datetime.now() + timedelta(days=12)).strftime('%Y-%m-%d'),
            'subject': 'Physics',
            'priority': 'medium',
            'added': datetime.now().strftime('%Y-%m-%d %H:%M')
        },
        {
            'name': 'Chemistry Lab Test',
            'date': (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d'),
            'subject': 'Chemistry',
            'priority': 'low',
            'added': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
    ]
    
    save_exams(sample_exams)
    flash('✅ Demo data loaded successfully! 3 sample exams added.', 'success')
    return redirect('/')

@app.route('/clear')
def clear_data():
    save_exams([])
    flash('🗑️ All data cleared successfully.', 'info')
    return redirect('/')

@app.route('/delete/<exam_name>')
def delete_exam(exam_name):
    exams = get_exams()
    exams = [e for e in exams if e['name'] != exam_name]
    save_exams(exams)
    flash(f'✅ Exam "{exam_name}" deleted.', 'success')
    return redirect('/')

if __name__ == '__main__':
    print("="*60)
    print("🚀 SMART TIMETABLE WEB APP - FULLY WORKING")
    print("="*60)
    print("✓ Add Exam: Form with validation")
    print("✓ Countdown: Visual timer")
    print("✓ Export CSV: Downloads working")
    print("✓ Demo Data: Pre-loaded samples")
    print("✓ GitHub Stars: 40+ displayed")
    print("="*60)
    print("Test Add Exam:")
    print("1. Go to /add_exam")
    print("2. Fill the form")
    print("3. Submit - should show success message")
    print("4. See new exam on dashboard")
    print("="*60)
    print("🌐 Open: http://localhost:5000")
    print("="*60)
    
    app.run(debug=True, port=5000)