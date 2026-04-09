import cv2
import os
import numpy as np

# Load face detector
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

known_faces = []
known_names = []

# =========================
def load_faces():
    global known_faces, known_names

    path = "static/uploads"
    known_faces.clear()
    known_names.clear()

    for file in os.listdir(path):
        if file.endswith(('.jpg', '.png', '.jpeg')):
            img_path = os.path.join(path, file)

            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

            if img is None:
                continue

            img = cv2.resize(img, (100, 100))

            known_faces.append(img)
            known_names.append(file.split('.')[0])

# =========================
def recognize_face(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        face = gray[y:y+h, x:x+w]

        if face.size == 0:
            continue

        face = cv2.resize(face, (100, 100))

        for i, known_face in enumerate(known_faces):
            diff = np.linalg.norm(known_face - face)

            if diff < 2000:   # threshold (adjust if needed)
                return known_names[i]

    return None