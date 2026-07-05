import cv2
import requests
from ultralytics import YOLO
from collections import deque
import time
import os
import torch
from torchvision import transforms, models
from PIL import Image

# =========================
# CONFIG
# =========================

video_source = 0
ZONE_NAME = "Main Gate"
BACKEND_URL = "http://localhost:5000/api/live-crowd-data"
CLASSIFIER_PATH = "models/violence_classifier.pt"

SNAPSHOT_DIR = "snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# =========================
# LOAD YOLO
# =========================

yolo_model = YOLO("yolov8n.pt")

# =========================
# LOAD RISK MODEL
# =========================

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
risk_model = None
class_names = []

risk_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

if os.path.exists(CLASSIFIER_PATH):
    try:
        checkpoint = torch.load(CLASSIFIER_PATH, map_location=DEVICE)
        class_names = checkpoint["class_names"]

        risk_model = models.resnet18(weights=None)
        risk_model.fc = torch.nn.Linear(risk_model.fc.in_features, len(class_names))
        risk_model.load_state_dict(checkpoint["model_state_dict"])
        risk_model = risk_model.to(DEVICE)
        risk_model.eval()

        print("Violence classifier loaded successfully.")
        print("Classes:", class_names)

    except Exception as e:
        print("Failed to load violence classifier:", repr(e))
        risk_model = None
else:
    print("No trained violence classifier found. Using crowd-count risk only.")

# =========================
# HELPERS
# =========================

recent_counts = deque(maxlen=20)

def get_density_risk(count):
    if count >= 20:
        return "HIGH"
    elif count >= 10:
        return "MEDIUM"
    else:
        return "LOW"

def predict_scene_risk(frame):
    if risk_model is None:
        return None

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    tensor = risk_transform(pil_img).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        outputs = risk_model(tensor)
        pred_idx = torch.argmax(outputs, dim=1).item()

    return class_names[pred_idx]

def connect_camera():
    print("Connecting to camera...")
    cap = cv2.VideoCapture(video_source)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cap

# =========================
# MAIN
# =========================

cap = connect_camera()
last_sent_time = 0
last_snapshot_time = 0
frame_skip = 3
frame_count = 0
last_results = []
last_person_count = 0
last_scene_label = "unknown"

while True:
    try:
        ret, frame = cap.read()

        if not ret or frame is None:
            print("Camera disconnected. Reconnecting...")
            cap.release()
            time.sleep(2)
            cap = connect_camera()
            continue

        frame = cv2.resize(frame, (640, 360))
        frame_count += 1

        if frame_count % frame_skip == 0 or not last_results:
            results = yolo_model(frame, verbose=False)
            last_results = results

            scene_label = predict_scene_risk(frame)
            if scene_label is not None:
                last_scene_label = scene_label
        else:
            results = last_results

        person_count = 0

        for result in results:
            boxes = result.boxes

            for box in boxes:
                cls = int(box.cls[0])
                label = yolo_model.names[cls]

                # PERSON ONLY
                if label == "person":
                    person_count += 1
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        frame,
                        "Person",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2
                    )

        if frame_count % frame_skip != 0 and person_count == 0:
            person_count = last_person_count

        last_person_count = person_count
        recent_counts.append(person_count)

        density_risk = get_density_risk(person_count)

        if last_scene_label and last_scene_label.lower() == "violence":
            risk_level = "HIGH"
            prediction = "Violence detected"
        else:
            risk_level = density_risk
            prediction = "Normal crowd flow"

            if len(recent_counts) >= 5:
                if recent_counts[-1] > recent_counts[0] + 5:
                    prediction = "Crowd increasing quickly"

        current_time = time.time()

        if risk_level == "HIGH" and (current_time - last_snapshot_time >= 5):
            filename = os.path.join(
                SNAPSHOT_DIR,
                f"{ZONE_NAME}_{int(current_time)}.jpg"
            )
            cv2.imwrite(filename, frame)
            last_snapshot_time = current_time

        cv2.putText(
            frame,
            f"Zone: {ZONE_NAME}",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )
        cv2.putText(
            frame,
            f"People: {person_count}",
            (20, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )
        cv2.putText(
            frame,
            f"Risk: {risk_level}",
            (20, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )
        cv2.putText(
            frame,
            f"Scene: {last_scene_label}",
            (20, 135),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )
        cv2.putText(
            frame,
            prediction,
            (20, 170),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2
        )

        if current_time - last_sent_time >= 2:
            try:
                payload = {
                    "zone": ZONE_NAME,
                    "person_count": person_count,
                    "risk_level": risk_level,
                    "prediction": prediction
                }
                requests.post(BACKEND_URL, json=payload, timeout=3)
                last_sent_time = current_time
            except Exception as e:
                print("Failed to send data:", e)

        cv2.imshow("SikSikSafe AI Monitor", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    except Exception as e:
        print("Runtime error:", e)
        time.sleep(2)

cap.release()
cv2.destroyAllWindows()