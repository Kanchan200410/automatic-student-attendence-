from flask import Flask, render_template, Response, request, redirect
import cv2
import os
from models.face_recognition import recognize_face
from database import get_db
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

camera = cv2.VideoCapture(0)

# =========================
# 🔹 MARK ATTENDANCE
# =========================
def mark_attendance(name):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT id FROM students WHERE name=%s", (name,))
    student = cursor.fetchone()

    if not student:
        return

    student_id = student[0]
    today = datetime.now().date()

    cursor.execute(
        "SELECT * FROM attendance WHERE student_id=%s AND date=%s",
        (student_id, today)
    )
    result = cursor.fetchone()

    if not result:
        now = datetime.now()
        cursor.execute(
            "INSERT INTO attendance (student_id, date, time) VALUES (%s, %s, %s)",
            (student_id, now.date(), now.time())
        )
        db.commit()

    cursor.close()
    db.close()

# =========================
# 🔹 CAMERA STREAM
# =========================
def generate_frames():
    while True:
        success, frame = camera.read()

        if not success:
            break

        name = recognize_face(frame)

        if name:
            mark_attendance(name)

            cv2.putText(frame, f"{name} Present", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# =========================
# 🔹 ROUTES
# =========================
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# =========================
# 🔹 REGISTER STUDENT
# =========================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
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
# 🔹 VIEW ATTENDANCE
# =========================
@app.route('/attendance')
def attendance():
    db = get_db()
    cursor = db.cursor()

    query = """
    SELECT students.name, students.roll_no, attendance.date, attendance.time
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
if __name__ == "__main__":
    app.run(debug=True)