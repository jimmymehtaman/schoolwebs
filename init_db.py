import sqlite3
from datetime import datetime, timedelta
import random
import os

def init_db():
    # Create database directory if it doesn't exist
    os.makedirs('instance', exist_ok=True)
    
    conn = sqlite3.connect('instance/school.db')
    c = conn.cursor()

    # Drop existing tables
    c.execute('DROP TABLE IF EXISTS student')
    c.execute('DROP TABLE IF EXISTS attendance')
    
    # Create student table
    c.execute('''CREATE TABLE IF NOT EXISTS student (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Create attendance table
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        subject TEXT NOT NULL,
        date DATE NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('present', 'absent')),
        FOREIGN KEY (student_id) REFERENCES student (id)
    )''')

    # Insert demo student
    c.execute("""INSERT INTO student (name, email, password) 
                VALUES (?, ?, ?)""", 
                ('John Doe', 'john@example.com', 'password123'))
    
    student_id = c.lastrowid

    # Generate attendance data for the past year
    subjects = ['Mathematics', 'Science', 'English', 'History']
    
    # Generate data for the past 12 months
    current_date = datetime.now()
    start_date = current_date - timedelta(days=365)
    
    while start_date <= current_date:
        # Skip weekends
        if start_date.weekday() < 5:  # Monday = 0, Sunday = 6
            for subject in subjects:
                # Generate attendance with 95% probability of being present
                status = 'present' if random.random() < 0.95 else 'absent'
                
                c.execute("""INSERT INTO attendance 
                            (student_id, subject, date, status) 
                            VALUES (?, ?, ?, ?)""",
                         (student_id, subject, start_date.strftime('%Y-%m-%d'), status))
        
        start_date += timedelta(days=1)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
