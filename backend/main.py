from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import cv2
import json
import numpy as np
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KNOWN_FACES_DIR = "known_faces"
STUDENTS_FILE = "students.json"
IMG_SIZE = 160

face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


@app.get("/")
def home():
    return {"message": "Pixel Based Smart Attendance Backend Running"}


def load_students():
    with open(STUDENTS_FILE, "r") as file:
        return json.load(file)


def get_student(folder_name):
    students = load_students()

    for student in students:
        if student["name"].lower() == folder_name.lower():
            return student

    return None


def extract_face(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(60, 60),
    )

    if len(faces) == 0:
        return None

    x, y, w, h = max(faces, key=lambda box: box[2] * box[3])

    face = gray[y:y + h, x:x + w]
    face = cv2.resize(face, (IMG_SIZE, IMG_SIZE))

    # Pixel normalization
    face = cv2.equalizeHist(face)
    face = face.astype("float32") / 255.0

    return face


def pixel_difference(face1, face2):
    # Lower score means better match
    mse = np.mean((face1 - face2) ** 2)
    return mse


@app.post("/mark-attendance")
async def mark_attendance(image: UploadFile = File(...)):
    image_bytes = await image.read()

    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        return {"status": "Failed", "message": "Invalid image received"}

    captured_face = extract_face(img)

    if captured_face is None:
        return {"status": "Failed", "message": "No face detected"}

    results = {}

    for person in os.listdir(KNOWN_FACES_DIR):
        person_path = os.path.join(KNOWN_FACES_DIR, person)

        if not os.path.isdir(person_path):
            continue

        scores = []

        for image_name in os.listdir(person_path):
            image_path = os.path.join(person_path, image_name)

            known_img = cv2.imread(image_path)

            if known_img is None:
                continue

            known_face = extract_face(known_img)

            if known_face is None:
                continue

            score = pixel_difference(captured_face, known_face)
            scores.append(score)

        if scores:
            # Take best 3 images only, not average of all bad images
            best_scores = sorted(scores)[:3]
            final_score = float(np.mean(best_scores))
            results[person] = final_score

    if not results:
        return {
            "status": "Failed",
            "message": "No valid training faces found"
        }

    sorted_results = sorted(results.items(), key=lambda x: x[1])

    best_name, best_score = sorted_results[0]

    second_score = sorted_results[1][1] if len(sorted_results) > 1 else 1

    # Pixel confidence
    confidence = max(0, 100 - (best_score * 1000))

    print("ALL PIXEL SCORES:", results)
    print("BEST MATCH:", best_name)
    print("BEST SCORE:", best_score)
    print("SECOND SCORE:", second_score)
    print("CONFIDENCE:", confidence)

    student = get_student(best_name)

    if student is None:
        return {
            "status": "Failed",
            "message": f"Student data not found for {best_name}"
        }

    return {
        "name": student.get("displayName", student["name"]),
        "rollNo": student["rollNo"],
        "confidence": f"{confidence:.2f}%",
        "status": "Present"
    }