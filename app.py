from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import sqlite3
from functools import wraps
from datetime import datetime, timedelta
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key

# File upload settings
UPLOAD_FOLDER = 'static/images/profile_pics'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Create uploads directory if it doesn't exist
os.makedirs('static/uploads/profiles', exist_ok=True)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'student_id' not in session:
            flash('Please log in first.')
            return redirect(url_for('student_login'))
        return f(*args, **kwargs)
    return decorated_function

# Initialize database
def init_db():
    conn = sqlite3.connect('school.db')
    c = conn.cursor()
    
    # Drop existing tables to start fresh
    c.execute('DROP TABLE IF EXISTS student')
    c.execute('DROP TABLE IF EXISTS notifications')
    c.execute('DROP TABLE IF EXISTS assignments')
    c.execute('DROP TABLE IF EXISTS attendance')
    
    # Create student table if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS student (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        roll_number TEXT UNIQUE NOT NULL,
        class_name TEXT,
        section TEXT,
        email TEXT UNIQUE,
        password_hash TEXT,
        profile_pic TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Create notifications table if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        type TEXT DEFAULT 'info',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES student (id)
    )''')
    
    # Create assignments table if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        due_date DATE,
        subject TEXT,
        class_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Create attendance table if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        date DATE NOT NULL,
        subject TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('present', 'absent')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES student (id)
    )''')
    
    # Create demo student
    demo_password = 'password123'
    demo_password_hash = generate_password_hash(demo_password)
    
    c.execute('''INSERT INTO student (name, roll_number, class_name, section, email, password_hash)
                VALUES (?, ?, ?, ?, ?, ?)''',
                ('Demo Student', 'DEMO001', '10', 'A', 'demo@example.com', demo_password_hash))
    
    # Add demo notifications
    student_id = c.lastrowid
    c.execute('''INSERT INTO notifications (student_id, title, message, type)
                VALUES (?, ?, ?, ?)''',
                (student_id, 'Welcome!', 'Welcome to ST MARIAM\'S SCHOOL', 'success'))
    
    # Add demo assignments
    today = datetime.now()
    c.execute('''INSERT INTO assignments (title, description, due_date, subject, class_name)
                VALUES (?, ?, ?, ?, ?)''',
                ('Mathematics Assignment', 'Complete exercises 1-10', 
                 (today + timedelta(days=7)).strftime('%Y-%m-%d'),
                 'Mathematics', '10'))
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        roll_number = request.form.get('roll_number')
        password = request.form.get('password')
        
        conn = sqlite3.connect('school.db')
        c = conn.cursor()
        
        try:
            # Get student details
            c.execute('SELECT * FROM student WHERE roll_number = ?', (roll_number,))
            student = c.fetchone()
            
            if student:
                # Check password
                if check_password_hash(student[6], password):  # password_hash is at index 6
                    session['student_id'] = student[0]  # id is at index 0
                    session['student_name'] = student[1]  # name is at index 1
                    conn.close()
                    return redirect(url_for('student_dashboard'))
            
            flash('Invalid roll number or password. Please try again.', 'error')
        except Exception as e:
            print(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')
        finally:
            conn.close()
    
    return render_template('student_login.html')

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    # Use direct SQL query
    conn = sqlite3.connect('school.db')
    c = conn.cursor()
    
    # Get student data
    c.execute('SELECT * FROM student WHERE id = ?', (session['student_id'],))
    student_data = c.fetchone()
    
    # Get notifications
    c.execute('SELECT * FROM notifications WHERE student_id = ? ORDER BY created_at DESC LIMIT 5',
              (session['student_id'],))
    notifications = [
        {
            'title': row[2],
            'message': row[3],
            'type': row[4],
            'created_at': datetime.strptime(row[5], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y')
        }
        for row in c.fetchall()
    ]
    
    # Get upcoming assignments
    c.execute('''SELECT * FROM assignments 
                WHERE class_name = ? 
                AND due_date >= date('now')
                ORDER BY due_date ASC LIMIT 5''',
              (student_data[3],))
    assignments = [
        {
            'title': row[1],
            'description': row[2],
            'due_date': datetime.strptime(row[3], '%Y-%m-%d').strftime('%b %d, %Y'),
            'subject': row[4]
        }
        for row in c.fetchall()
    ]
    
    conn.close()
    
    if student_data:
        student = {
            'id': student_data[0],
            'name': student_data[1],
            'roll_no': student_data[2],
            'class_name': student_data[3],
            'section': student_data[4],
            'email': student_data[5],
            'profile_pic': student_data[7] or 'images/profile-placeholder.jpg',
            'attendance': 92,  # Sample attendance percentage
            'fees_paid': 45000,  # Sample fees paid
            'total_fees': 60000,  # Sample total fees
        }
        
        # Add dashboard data
        context = {
            'student': student,
            'upcoming_tests': [
                {
                    'date': datetime.now() + timedelta(days=i*3),
                    'subject': f'Subject {i+1}',
                    'topic': f'Topic {i+1}'
                }
                for i in range(3)
            ],
            'recent_activities': [
                {
                    'icon': 'fas fa-book',
                    'title': 'Assignment Submitted',
                    'description': 'Mathematics Assignment',
                    'time': '2 hours ago'
                },
                {
                    'icon': 'fas fa-trophy',
                    'title': 'Achievement Unlocked',
                    'description': 'Perfect Attendance This Week',
                    'time': '1 day ago'
                },
                {
                    'icon': 'fas fa-chart-line',
                    'title': 'Test Score',
                    'description': 'Scored 95% in Science Test',
                    'time': '2 days ago'
                }
            ]
        }
        
        return render_template('student_dashboard.html', **context)
    
    return redirect(url_for('student_login'))

@app.route('/student/logout')
def student_logout():
    session.clear()  # Clear all session data
    return redirect(url_for('index'))

@app.route('/upload_profile_pic', methods=['POST'])
@login_required
def upload_profile_pic():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Create upload folder if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Get student info from database
        conn = sqlite3.connect('school.db')
        c = conn.cursor()
        c.execute('SELECT roll_number FROM student WHERE id = ?', (session['student_id'],))
        student_data = c.fetchone()
        
        if student_data:
            # Create unique filename
            filename = f"profile_{student_data[0]}_{secure_filename(file.filename)}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # Save file
            file.save(filepath)
            
            # Update student profile pic in database
            profile_pic = f'images/profile_pics/{filename}'
            c.execute('UPDATE student SET profile_pic = ? WHERE id = ?', (profile_pic, session['student_id']))
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'image_url': url_for('static', filename=f'images/profile_pics/{filename}')
            })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    if 'profile_pic' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['profile_pic']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to filename to make it unique
        filename = f"{int(time.time())}_{filename}"
        file_path = os.path.join('static/uploads/profiles', filename)
        file.save(file_path)
        
        # Update student profile picture in database
        student_id = session.get('student_id')
        if student_id:
            conn = sqlite3.connect('school.db')
            c = conn.cursor()
            c.execute("UPDATE student SET profile_pic = ? WHERE id = ?", 
                     (f'uploads/profiles/{filename}', student_id))
            conn.commit()
            conn.close()
            
        return jsonify({'success': True, 'filename': filename}), 200
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/events')
def events():
    return render_template('events.html')

@app.route('/announcements')
def announcements():
    return render_template('announcements.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/fees')
@login_required
def fees():
    conn = sqlite3.connect('school.db')
    c = conn.cursor()
    
    # Get student data
    c.execute('SELECT * FROM student WHERE id = ?', (session['student_id'],))
    student_data = c.fetchone()
    
    # Sample fees data (in a real app, this would come from the database)
    fees_data = {
        'student': {
            'name': student_data[1],
            'class': student_data[3],
            'section': student_data[4],
            'roll_number': student_data[2]
        },
        'current_year': '2024-2025',
        'total_fees': 50000,
        'paid_fees': 30000,
        'pending_fees': 20000,
        'due_date': (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
        'payment_history': [
            {
                'date': (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
                'amount': 15000,
                'receipt_no': 'REC001',
                'mode': 'Online',
                'status': 'Paid'
            },
            {
                'date': (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d'),
                'amount': 15000,
                'receipt_no': 'REC002',
                'mode': 'Bank Transfer',
                'status': 'Paid'
            }
        ],
        'fee_structure': [
            {'type': 'Tuition Fee', 'amount': 30000},
            {'type': 'Development Fee', 'amount': 10000},
            {'type': 'Library Fee', 'amount': 5000},
            {'type': 'Computer Lab Fee', 'amount': 5000}
        ]
    }
    
    conn.close()
    return render_template('fees.html', fees=fees_data)

@app.route('/attendance')
@login_required
def attendance():
    return render_template('attendance.html')

@app.route('/results')
@login_required
def results():
    # Use direct SQL query
    conn = sqlite3.connect('school.db')
    c = conn.cursor()
    c.execute('SELECT * FROM student WHERE id = ?', (session['student_id'],))
    student_data = c.fetchone()
    conn.close()
    
    if student_data:
        student = {
            'id': student_data[0],
            'name': student_data[1],
            'roll_number': student_data[2],
            'class_name': student_data[3],
            'section': student_data[4]
        }
        
        # Add dummy results data
        context = {
            'student': student,
            'results': [
                {
                    'subject': 'Mathematics',
                    'marks_obtained': 92,
                    'total_marks': 100,
                    'grade': 'A+'
                },
                {
                    'subject': 'Science',
                    'marks_obtained': 88,
                    'total_marks': 100,
                    'grade': 'A'
                },
                {
                    'subject': 'English',
                    'marks_obtained': 90,
                    'total_marks': 100,
                    'grade': 'A+'
                },
                {
                    'subject': 'Social Studies',
                    'marks_obtained': 85,
                    'total_marks': 100,
                    'grade': 'A'
                }
            ],
            'total_marks': 355,
            'percentage': 88.75,
            'grade': 'A',
            'rank': 5
        }
        return render_template('results.html', **context)
    return redirect(url_for('student_login'))

@app.route('/analysis')
@login_required
def analysis():
    conn = sqlite3.connect('school.db')
    c = conn.cursor()
    
    # Get student data
    c.execute('SELECT * FROM student WHERE id = ?', (session['student_id'],))
    student_data = c.fetchone()
    
    # Sample analysis data (in a real app, this would come from the database)
    analysis_data = {
        'student': {
            'name': student_data[1],
            'class': student_data[3],
            'section': student_data[4]
        },
        'attendance': {
            'present': 85,
            'absent': 5,
            'leave': 10,
            'monthly_data': [
                {'month': 'Jan', 'percentage': 95},
                {'month': 'Feb', 'percentage': 88},
                {'month': 'Mar', 'percentage': 92},
                {'month': 'Apr', 'percentage': 85}
            ]
        },
        'academics': {
            'overall_grade': 'A',
            'percentage': 85.5,
            'subjects': [
                {'name': 'Mathematics', 'marks': 92, 'grade': 'A+'},
                {'name': 'Science', 'marks': 88, 'grade': 'A'},
                {'name': 'English', 'marks': 85, 'grade': 'A'},
                {'name': 'Social Studies', 'marks': 82, 'grade': 'A-'},
                {'name': 'Computer Science', 'marks': 95, 'grade': 'A+'}
            ]
        },
        'performance': {
            'class_rank': 5,
            'total_students': 50,
            'percentile': 90,
            'improvement': '+5%'
        }
    }
    
    conn.close()
    return render_template('analysis.html', analysis=analysis_data)

@app.route('/routine')
@login_required
def routine():
    return render_template('routine.html')

@app.route('/syllabus')
@login_required
def syllabus():
    return render_template('syllabus.html')

@app.route('/documents')
@login_required
def documents():
    return render_template('documents.html')

@app.route('/leadership')
def leadership():
    return render_template('leadership.html')

@app.route('/students')
def students():
    return render_template('students.html')

@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # For demo, use hardcoded teacher credentials
        if email == "teacher@example.com" and password == "teacher123":
            session['teacher_id'] = 1
            session['is_teacher'] = True
            flash('Welcome back, Teacher!', 'success')
            return redirect(url_for('teacher_dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('teacher_login.html')

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'teacher_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('teacher_login'))
    return render_template('teacher_dashboard.html')

@app.route('/teacher/logout')
def teacher_logout():
    session.pop('teacher_id', None)
    session.pop('is_teacher', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # For demo, use hardcoded admin credentials
        if email == "admin@example.com" and password == "admin123":
            session['admin_id'] = 1
            session['is_admin'] = True
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('is_admin', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/get_attendance_data')
def get_attendance_data():
    if 'student_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    student_id = session['student_id']
    conn = sqlite3.connect('school.db')
    c = conn.cursor()

    # Get monthly attendance data
    c.execute("""
        SELECT strftime('%m', date) as month,
               SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_count,
               SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent_count
        FROM attendance
        WHERE student_id = ?
        AND date >= date('now', '-1 year')
        GROUP BY month
        ORDER BY month
    """, (student_id,))
    
    monthly_data = c.fetchall()
    
    # Get subject-wise attendance
    c.execute("""
        SELECT subject,
               COUNT(*) as total_classes,
               SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_count
        FROM attendance
        WHERE student_id = ?
        GROUP BY subject
    """, (student_id,))
    
    subject_data = c.fetchall()
    
    # Get overall attendance
    c.execute("""
        SELECT COUNT(*) as total_days,
               SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_days
        FROM attendance
        WHERE student_id = ?
    """, (student_id,))
    
    overall_data = c.fetchone()
    
    conn.close()
    
    # Format the data
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_formatted = {
        'labels': months,
        'present': [0] * 12,
        'absent': [0] * 12
    }
    
    for month, present, absent in monthly_data:
        month_idx = int(month) - 1
        monthly_formatted['present'][month_idx] = present
        monthly_formatted['absent'][month_idx] = absent
    
    subject_formatted = [{
        'subject': subject,
        'percentage': round((present_count / total_classes) * 100, 1)
    } for subject, total_classes, present_count in subject_data]
    
    total_days, present_days = overall_data
    attendance_rate = round((present_days / total_days) * 100, 1) if total_days > 0 else 0
    
    return jsonify({
        'monthly': monthly_formatted,
        'subjects': subject_formatted,
        'overall': {
            'total_days': total_days,
            'present_days': present_days,
            'attendance_rate': attendance_rate
        }
    })

if __name__ == '__main__':
    app.run(debug=True)
