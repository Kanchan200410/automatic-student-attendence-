from deepface import DeepFace
import os
import cv2

def recognize_face(frame):
    try:
        temp_img = "temp.jpg"
        cv2.imwrite(temp_img, frame)

        db_path = "static/uploads"

        results = DeepFace.find(
            img_path=temp_img,
            db_path=db_path,
            enforce_detection=False
        )

        if len(results) > 0 and len(results[0]) > 0:
            match = results[0].iloc[0]

            identity_path = match['identity']
            name = os.path.basename(identity_path).split('.')[0]

            return name

    except Exception as e:
        print("Error:", e)

    return None