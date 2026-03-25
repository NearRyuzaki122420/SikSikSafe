import cv2
import requests
from ultralytics import YOLO
from collections import deque
import time
import os
import numpy as np

# More stable RTSP connection for DVR streams
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

# Load YOLO model
model = YOLO("yolov8n.pt")

# DVR credentials and IP
DVR_USER = "adminr2"
DVR_PASS = "adminr2!!"
DVR_IP = "192.168.1.3"

# Camera channels and zone names
CAMERAS = [
    {
        "zone": "Main Gate",
        "url": f"rtsp://{DVR_USER}:{DVR_PASS}@{DVR_IP}:554/cam/realmonitor?channel=1&subtype=1",
        "recent_counts": deque(maxlen=20),
        "last_results": [],
        "last_person_count": 0,
        "last_snapshot_time": 0,
        "last_sent_time": 0,
    },
    {
        "zone": "Hallway",
        "url": f"rtsp://{DVR_USER}:{DVR_PASS}@{DVR_IP}:554/cam/realmonitor?channel=2&subtype=1",
        "recent_counts": deque(maxlen=20),
        "last_results": [],
        "last_person_count": 0,
        "last_snapshot_time": 0,
        "last_sent_time": 0,
    },
    {
        "zone": "Exit Area",
        "url": f"rtsp://{DVR_USER}:{DVR_PASS}@{DVR_IP}:554/cam/realmonitor?channel=3&subtype=1",
        "recent_counts": deque(maxlen=20),
        "last_results": [],
        "last_person_count": 0,
        "last_snapshot_time": 0,
        "last_sent_time": 0,
    },
]

# Backend URL
BACKEND_URL = "http://localhost:5000/api/live-crowd-data"

# Snapshot folder
SNAPSHOT_DIR = "snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# Performance settings
frame_skip = 3
frame_count = 0

def get_risk_level(count: int) -> str:
    if count >= 20:
        return "HIGH"
    elif count >= 10:
        return "MEDIUM"
    else:
        return "LOW"

def connect_camera(url: str):
    print(f"Connecting to DVR stream: {url}")
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap

# Open all camera streams
for cam in CAMERAS:
    cam["cap"] = connect_camera(cam["url"])

def process_camera(cam: dict, frame, current_time: float):
    frame = cv2.resize(frame, (320, 240))

    if frame_count % frame_skip == 0 or not cam["last_results"]:
        results = model(frame, verbose=False)
        cam["last_results"] = results
    else:
        results = cam["last_results"]

    person_count = 0

    for result in results:
        boxes = result.boxes
        for box in boxes:
            cls = int(box.cls[0])
            label = model.names[cls]

            if label == "person":
                person_count += 1
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    "Person",
                    (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (0, 255, 0),
                    1
                )

    if frame_count % frame_skip != 0 and cam["last_results"]:
        if person_count == 0:
            person_count = cam["last_person_count"]

    cam["last_person_count"] = person_count
    cam["recent_counts"].append(person_count)

    risk_level = get_risk_level(person_count)

    prediction = "Normal crowd flow"
    if len(cam["recent_counts"]) >= 5:
        if cam["recent_counts"][-1] > cam["recent_counts"][0] + 5:
            prediction = "Crowd increasing quickly"

    if risk_level == "HIGH" and (current_time - cam["last_snapshot_time"] >= 5):
        filename = os.path.join(
            SNAPSHOT_DIR,
            f"{cam['zone']}_{int(current_time)}.jpg"
        )
        cv2.imwrite(filename, frame)
        cam["last_snapshot_time"] = current_time

    if current_time - cam["last_sent_time"] >= 3:
        try:
            payload = {
                "zone": cam["zone"],
                "person_count": person_count,
                "risk_level": risk_level,
                "prediction": prediction
            }
            requests.post(BACKEND_URL, json=payload, timeout=3)
            cam["last_sent_time"] = current_time
        except Exception as e:
            print(f"Failed to send data for {cam['zone']}: {e}")

    cv2.putText(
        frame,
        f"Zone: {cam['zone']}",
        (8, 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        2
    )
    cv2.putText(
        frame,
        f"People: {person_count}",
        (8, 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 255),
        2
    )
    cv2.putText(
        frame,
        f"Risk: {risk_level}",
        (8, 64),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 0, 255),
        2
    )
    cv2.putText(
        frame,
        prediction,
        (8, 86),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.42,
        (255, 255, 0),
        1
    )

    return frame

while True:
    try:
        frame_count += 1
        current_time = time.time()
        processed_frames = []

        for cam in CAMERAS:
            ret, frame = cam["cap"].read()

            if not ret or frame is None:
                print(f"{cam['zone']} disconnected. Reconnecting...")
                cam["cap"].release()
                time.sleep(1)
                cam["cap"] = connect_camera(cam["url"])

                blank = np.zeros((240, 320, 3), dtype=np.uint8)
                cv2.putText(
                    blank,
                    f"{cam['zone']} - No Signal",
                    (20, 120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )
                processed_frames.append(blank)
                continue

            processed = process_camera(cam, frame, current_time)
            processed_frames.append(processed)

        while len(processed_frames) < 4:
            processed_frames.append(np.zeros((240, 320, 3), dtype=np.uint8))

        top_row = np.hstack((processed_frames[0], processed_frames[1]))
        bottom_row = np.hstack((processed_frames[2], processed_frames[3]))
        grid = np.vstack((top_row, bottom_row))

        cv2.imshow("SikSikSafe Multi-Camera Monitor", grid)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    except Exception as e:
        print("Runtime error:", e)
        time.sleep(2)

for cam in CAMERAS:
    cam["cap"].release()

cv2.destroyAllWindows()