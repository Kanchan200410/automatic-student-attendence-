from flask import Flask, render_template, Response, request, redirect
import cv2
import numpy as np
import face_recognition_models
import face_recognition
from flask import session, url_for
from models.face_recognition import load_faces
from database import get_db
from datetime import datetime
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
app = Flask(__name__)
app.secret_key = "secret123"
session['role']
# =========================
# CONFIG
UPLOAD_FOLDER = "static/uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

camera = cv2.VideoCapture(0)

# Load known faces
known_encodings, known_names = load_faces()

# Cooldown tracker
last_marked = {}

# =========================
# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' not in session:
        return redirect('/login')


    if request.method == 'POST':
        role = request.form['role']
        name = request.form['name']
        roll = request.form['roll']
        age = request.form['age']
        section = request.form['section']
        year = request.form['year']
        branch = request.form['branch']
        phone = request.form['phone']
        email = request.form['email']

        file = request.files['image']
        image_data = file.read()

        filename = f"{roll}.jpg"
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        file.seek(0)
        file.save(path)

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO students 
            (name, roll, age, section, year, branch, phone, email, image, image_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, roll, age, section, year, branch, phone, email, image_data, filename))

        db.commit()

        # reload faces after adding new student
        global known_encodings, known_names
        known_encodings, known_names = load_faces()

        cursor.close()
        db.close()

        return redirect('/')

    return render_template("register.html")

# =========================
#LogIn
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            SELECT username, role FROM users 
            WHERE username=%s AND password=%s
        """, (username, password))

        user = cursor.fetchone()

        cursor.close()
        db.close()

        if user:
            session['user'] = user[0]
            session['role'] = user[1]   # 🔥 store role
            return redirect('/')
        else:
            return "Invalid Credentials"

    return render_template("login.html")
# =========================
# FACE RECOGNITION
def recognize_face_multiple(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb)
    encodings = face_recognition.face_encodings(rgb, face_locations)

    results = []

    for (top, right, bottom, left), encoding in zip(face_locations, encodings):
        matches = face_recognition.compare_faces(known_encodings, encoding)
        distances = face_recognition.face_distance(known_encodings, encoding)

        name = "Unknown"
        confidence = 0.0

        if len(distances) > 0:
            best_match_index = np.argmin(distances)
            confidence = 1 - distances[best_match_index]

            if matches[best_match_index]:
                name = known_names[best_match_index]

        results.append((name, confidence, (top, right, bottom, left)))

    return results
# =========================
# MARK ATTENDANCE
def mark_attendance(name, confidence=0.0):
    now = datetime.now()

    # Cooldown (10 sec)
    if name in last_marked:
        if (now - last_marked[name]).seconds < 10:
            return

    last_marked[name] = now

    db = get_db()
    cursor = db.cursor()

    # Get student ID
    cursor.execute("SELECT id FROM students WHERE name=%s", (name,))
    student = cursor.fetchone()

    if not student:
        cursor.close()
        db.close()
        return

    student_id = student[0]
    today = now.date()

    # Check duplicate
    cursor.execute("""
        SELECT attendance_id FROM attendance 
        WHERE student_id=%s AND date=%s
    """, (student_id, today))

    if cursor.fetchone():
        cursor.close()
        db.close()
        return

    # Insert attendance
    cursor.execute("""
        INSERT INTO attendance 
        (student_id, class_id, device_id, date, check_in, status, confidence, teacher_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        student_id,
        1,
        1,
        today,
        now,
        'Present',
        confidence,
        'Auto System'
    ))

    db.commit()
    cursor.close()
    db.close()

# =========================
# VIDEO STREAM
def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            continue

        results = recognize_face_multiple(frame)

        for name, confidence, (top, right, bottom, left) in results:

            if name != "Unknown" and confidence > 0.5:
                mark_attendance(name, confidence)

                label = f"{name} ({round(confidence,2)})"

                cv2.rectangle(frame, (left, top), (right, bottom), (0,255,0), 2)
                cv2.putText(frame, label, (left, top-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# =========================
# ROUTES
@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')

    role = session.get('role')

    if role == 'admin':
        return render_template('admin.html')
    elif role == 'teacher':
        return render_template('teacher.html')
    elif role == 'student':
        return render_template('student.html')
    elif role == 'hod':
        return render_template('hod.html')

    return "Invalid Role"

@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')
# =========================

@app.route('/student_dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return "Access Denied"

    return "Student Dashboard"

# =========================
@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if 'user' not in session:
        return redirect('/login')

    if session.get('role') not in ['admin', 'teacher', 'hod']:
        return "Access Denied"

    db = get_db()
    cursor = db.cursor()

    selected_date = request.form.get('date')

    if selected_date:
        query = """
            SELECT students.name, students.roll,
                   attendance.date,
                   TIME(attendance.check_in),
                   attendance.status,
                   attendance.teacher_name
            FROM attendance
            JOIN students ON attendance.student_id = students.id
            WHERE attendance.date = %s
            ORDER BY attendance.date DESC
        """
        cursor.execute(query, (selected_date,))
    else:
        query = """
            SELECT students.name, students.roll,
                   attendance.date,
                   TIME(attendance.check_in),
                   attendance.status,
                   attendance.teacher_name
            FROM attendance
            JOIN students ON attendance.student_id = students.id
            ORDER BY attendance.date DESC
        """
        cursor.execute(query)

    records = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("attendance.html", records=records)

# =========================

@app.route('/dashboard')
def dashboard():
    db = get_db()
    cursor = db.cursor()

    # total students
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    # today attendance
    cursor.execute("SELECT COUNT(*) FROM attendance WHERE date = CURDATE()")
    today_attendance = cursor.fetchone()[0]

    # total attendance records
    cursor.execute("SELECT COUNT(*) FROM attendance")
    total_records = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return render_template("dashboard.html",
                           total_students=total_students,
                           today_attendance=today_attendance,
                           total_records=total_records)

# =========================
if __name__ == "__main__":
    app.run(debug=True)