from flask import Flask, render_template, Response, request, redirect
import cv2
import os
import time
from datetime import datetime
from database import get_db
from models.face_recognition import recognize_face

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ KEEP YOUR CAMERA SAME
camera = cv2.VideoCapture(0)   # 👈 NOT CHANGED

# =========================
# 🧠 MEMORY (avoid duplicate)
# =========================
last_marked = {}

# =========================
# ✅ FIXED ATTENDANCE FUNCTION
# =========================
def mark_attendance(name):
    db = get_db()
    cursor = db.cursor(buffered=True)

    today = datetime.now().date()

    print("Searching in DB for:", name)

    # Prevent duplicate marking
    if name in last_marked and last_marked[name] == today:
        cursor.close()
        db.close()
        return

    cursor.execute("SELECT id FROM students WHERE name=%s", (name,))
    student = cursor.fetchone()

    if not student:
        print("❌ Student NOT FOUND in DB:", name)
        cursor.close()
        db.close()
        return

    student_id = student[0]

    cursor.execute(
        "SELECT * FROM attendance WHERE student_id=%s AND date=%s",
        (student_id, today)
    )

    if cursor.fetchone() is None:
        now = datetime.now()

        cursor.execute(
            "INSERT INTO attendance (student_id, date, time) VALUES (%s, %s, %s)",
            (student_id, now.date(), now.time())
        )

        db.commit()
        print("✅ Attendance Marked:", name)

        last_marked[name] = today

    cursor.close()
    db.close()

# =========================
# 🎥 STREAM (UNCHANGED CAMERA LOGIC)
# =========================
def generate_frames():
    last_check = 0
    name = None

    while True:
        success, frame = camera.read()

        if not success or frame is None:
            continue

        frame = cv2.resize(frame, (640, 480))

        # Run DeepFace every 5 sec
        if time.time() - last_check > 5:
            try:
                temp_frame = frame.copy()
                detected_name = recognize_face(temp_frame)

                if detected_name:
                    print("Detected:", detected_name)
                    name = detected_name
                    mark_attendance(name)

                last_check = time.time()

            except Exception as e:
                print("Recognition error:", e)

        if name:
            cv2.putText(frame, f"{name} Present", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        ret, buffer = cv2.imencode('.jpg', frame)

        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# =========================
# ROUTES
# =========================
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# =========================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 🔥 FIX: normalize name
        name = request.form['name'].strip().lower()
        roll = request.form['roll']
        file = request.files['image']

        filename = f"{name}.jpg"
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO students (name, roll_no, image_path) VALUES (%s, %s, %s)",
            (name, roll, filename)
        )

        db.commit()
        cursor.close()
        db.close()

        return redirect('/')

    return render_template("register.html")

# =========================
@app.route('/attendance')
def attendance():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
    SELECT students.name, students.roll_no, attendance.date, attendance.time
    FROM attendance
    JOIN students ON attendance.student_id = students.id
    ORDER BY attendance.date DESC
    """)

    records = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("attendance.html", records=records)

# =========================
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)