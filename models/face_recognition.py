from deepface import DeepFace
import os
import cv2

UPLOAD_PATH = "static/uploads"

def recognize_face(frame):
    try:
        # Resize for speed
        frame = cv2.resize(frame, (320, 240))

        temp_path = "temp.jpg"
        cv2.imwrite(temp_path, frame)

        for file in os.listdir(UPLOAD_PATH):
            if file.endswith(('.jpg', '.png', '.jpeg')):
                db_img = os.path.join(UPLOAD_PATH, file)

                try:
                    result = DeepFace.verify(
                        img1_path=temp_path,
                        img2_path=db_img,
                        model_name="Facenet",
                        enforce_detection=False
                    )

                    print("Comparing with:", file, "| Result:", result)

                    # 🔥 FIX: better matching condition
                    if result["verified"] or result["distance"] < 0.6:
                        name = file.split('.')[0].lower().strip()
                        return name

                except Exception as e:
                    print("DeepFace error:", e)
                    continue

        return None

    except Exception as e:
        print("Main error:", e)
        return None