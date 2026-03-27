import json
import os
import time
from collections import deque
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np
import requests
from ultralytics import YOLO

# More stable RTSP connection for DVR streams.
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

PERSON_CLASS_ID = 0
FRAME_SIZE = (320, 240)
TRACK_MATCH_DISTANCE = 45.0
TRACK_STALE_SECONDS = 1.25
SPEED_NORMALIZER = 60.0
MAX_DENSITY_PEOPLE = 20

MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
PERSON_CONF_THRESHOLD = float(os.getenv("PERSON_CONF_THRESHOLD", "0.35"))
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000/api/live-crowd-data")
SEND_INTERVAL_SECONDS = float(os.getenv("SEND_INTERVAL_SECONDS", "3"))
INPUT_MODE = os.getenv("INPUT_MODE", "live").strip().lower()
DATASET_DIR = os.getenv("DATASET_VIDEO_DIR", "ViolenceDetectioDataset")
DATASET_FRAME_STRIDE = max(1, int(os.getenv("DATASET_FRAME_STRIDE", "2")))
DATASET_MAX_VIDEOS = max(1, int(os.getenv("DATASET_MAX_VIDEOS", "10")))
DATASET_SUMMARY_PATH = os.getenv("DATASET_SUMMARY_PATH", "")
SNAPSHOT_DIR = os.getenv("SNAPSHOT_DIR", "snapshots")


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


SHOW_WINDOW = env_flag("SHOW_WINDOW", True)
ENABLE_BACKEND_POST = env_flag("ENABLE_BACKEND_POST", True)
DATASET_SEND_BACKEND = env_flag("DATASET_SEND_BACKEND", False)

os.makedirs(SNAPSHOT_DIR, exist_ok=True)
model = YOLO(MODEL_PATH)

# DVR credentials and IP.
DVR_USER = os.getenv("DVR_USER", "adminr2")
DVR_PASS = os.getenv("DVR_PASS", "adminr2!!")
DVR_IP = os.getenv("DVR_IP", "192.168.1.3")

DEFAULT_CAMERA_CONFIG = [
    ("Main Gate", 1),
    ("Hallway", 2),
    ("Exit Area", 3),
]


def create_source_state(zone: str, url: str = "") -> Dict:
    return {
        "zone": zone,
        "url": url,
        "cap": None,
        "recent_counts": deque(maxlen=20),
        "tracks": {},
        "next_track_id": 1,
        "last_track_update": None,
        "last_snapshot_time": 0.0,
        "last_sent_time": 0.0,
    }


def build_default_cameras() -> List[Dict]:
    cameras = []
    for zone, channel in DEFAULT_CAMERA_CONFIG:
        url = (
            f"rtsp://{DVR_USER}:{DVR_PASS}@{DVR_IP}:554/"
            f"cam/realmonitor?channel={channel}&subtype=1"
        )
        cameras.append(create_source_state(zone=zone, url=url))
    return cameras


def connect_camera(url: str):
    print(f"Connecting to DVR stream: {url}")
    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def detect_person_boxes(frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
    # classes=[0] means the model only detects persons.
    results = model(
        frame,
        classes=[PERSON_CLASS_ID],
        conf=PERSON_CONF_THRESHOLD,
        verbose=False,
    )
    boxes: List[Tuple[int, int, int, int]] = []

    for result in results:
        if result.boxes is None:
            continue
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            boxes.append((x1, y1, x2, y2))
    return boxes


def update_person_tracking(source: Dict, boxes: List[Tuple[int, int, int, int]], now: float):
    centroids = [((x1 + x2) / 2.0, (y1 + y2) / 2.0) for x1, y1, x2, y2 in boxes]
    tracks = source["tracks"]
    prev_time = source["last_track_update"]
    dt = max(1.0 / 30.0, now - prev_time) if prev_time else 1.0 / 30.0
    source["last_track_update"] = now

    used_detection_indexes = set()
    movement_vectors = []
    speed_samples = []

    for track_id in list(tracks.keys()):
        track = tracks[track_id]
        best_idx = None
        best_dist = TRACK_MATCH_DISTANCE

        for idx, centroid in enumerate(centroids):
            if idx in used_detection_indexes:
                continue
            dist = float(np.linalg.norm(np.array(track["centroid"]) - np.array(centroid)))
            if dist < best_dist:
                best_dist = dist
                best_idx = idx

        if best_idx is not None:
            new_centroid = centroids[best_idx]
            old_centroid = track["centroid"]
            vector = (
                new_centroid[0] - old_centroid[0],
                new_centroid[1] - old_centroid[1],
            )
            speed = float(np.linalg.norm(np.array(vector)) / dt)
            speed_ema = 0.6 * track.get("speed_ema", speed) + 0.4 * speed
            speed_samples.append(speed_ema)
            if np.linalg.norm(np.array(vector)) >= 2.0:
                movement_vectors.append(vector)

            track["centroid"] = new_centroid
            track["last_seen"] = now
            track["speed_ema"] = speed_ema
            used_detection_indexes.add(best_idx)
        elif now - track["last_seen"] > TRACK_STALE_SECONDS:
            del tracks[track_id]

    for idx, centroid in enumerate(centroids):
        if idx in used_detection_indexes:
            continue
        tracks[source["next_track_id"]] = {
            "centroid": centroid,
            "last_seen": now,
            "speed_ema": 0.0,
        }
        source["next_track_id"] += 1

    speed_norm = float(np.clip((np.mean(speed_samples) if speed_samples else 0.0) / SPEED_NORMALIZER, 0.0, 1.0))

    direction_chaos = 0.0
    if len(movement_vectors) >= 2:
        vectors = np.array(movement_vectors, dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-6
        unit_vectors = vectors / norms
        resultant = np.linalg.norm(np.mean(unit_vectors, axis=0))
        direction_chaos = float(np.clip(1.0 - resultant, 0.0, 1.0))

    return speed_norm, direction_chaos


def compute_surge_score(recent_counts: deque) -> float:
    if len(recent_counts) < 5:
        return 0.0
    count_delta = recent_counts[-1] - recent_counts[0]
    return float(np.clip(count_delta / 8.0, 0.0, 1.0))


def classify_risk(person_count: int, speed_norm: float, direction_chaos: float, surge_score: float):
    density_score = float(np.clip(person_count / MAX_DENSITY_PEOPLE, 0.0, 1.0))

    violence_score = float(np.clip(0.65 * speed_norm + 0.35 * direction_chaos, 0.0, 1.0))
    stampede_score = float(np.clip(0.60 * density_score + 0.40 * surge_score, 0.0, 1.0))
    combined_score = max(violence_score, stampede_score)

    if combined_score >= 0.75:
        risk_level = "HIGH"
    elif combined_score >= 0.45:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    if stampede_score >= 0.65 and stampede_score >= violence_score:
        prediction = "Possible stampede surge risk from dense crowd pressure"
    elif violence_score >= 0.65:
        prediction = "Potential violent crowd behavior from abrupt person movement"
    elif person_count >= 10:
        prediction = "Crowd is dense but movement appears controlled"
    else:
        prediction = "Normal person movement flow"

    return risk_level, prediction, violence_score, stampede_score


def draw_overlay(
    frame: np.ndarray,
    zone: str,
    person_count: int,
    risk_level: str,
    prediction: str,
    violence_score: float,
    stampede_score: float,
):
    cv2.putText(frame, f"Zone: {zone}", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    cv2.putText(frame, f"People: {person_count}", (8, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    cv2.putText(frame, f"Risk: {risk_level}", (8, 64), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    cv2.putText(
        frame,
        f"Violence:{violence_score:.2f} Stampede:{stampede_score:.2f}",
        (8, 86),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.4,
        (255, 255, 0),
        1,
    )
    cv2.putText(frame, prediction, (8, 108), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 0), 1)


def process_frame(source: Dict, frame: np.ndarray, now: float, send_to_backend: bool, save_snapshot: bool):
    frame = cv2.resize(frame, FRAME_SIZE)
    boxes = detect_person_boxes(frame)
    person_count = len(boxes)

    for x1, y1, x2, y2 in boxes:
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, "Person", (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    speed_norm, direction_chaos = update_person_tracking(source, boxes, now)
    source["recent_counts"].append(person_count)
    surge_score = compute_surge_score(source["recent_counts"])
    risk_level, prediction, violence_score, stampede_score = classify_risk(
        person_count,
        speed_norm,
        direction_chaos,
        surge_score,
    )

    if save_snapshot and risk_level == "HIGH" and (now - source["last_snapshot_time"] >= 5.0):
        filename = os.path.join(SNAPSHOT_DIR, f"{source['zone']}_{int(now)}.jpg")
        cv2.imwrite(filename, frame)
        source["last_snapshot_time"] = now

    if send_to_backend and ENABLE_BACKEND_POST and (now - source["last_sent_time"] >= SEND_INTERVAL_SECONDS):
        payload = {
            "zone": source["zone"],
            "person_count": person_count,
            "risk_level": risk_level,
            "prediction": prediction,
            "violence_score": round(violence_score, 3),
            "stampede_score": round(stampede_score, 3),
        }
        try:
            requests.post(BACKEND_URL, json=payload, timeout=3)
            source["last_sent_time"] = now
        except Exception as error:
            print(f"Failed to send data for {source['zone']}: {error}")

    draw_overlay(
        frame=frame,
        zone=source["zone"],
        person_count=person_count,
        risk_level=risk_level,
        prediction=prediction,
        violence_score=violence_score,
        stampede_score=stampede_score,
    )

    return frame, {
        "zone": source["zone"],
        "person_count": person_count,
        "risk_level": risk_level,
        "prediction": prediction,
        "violence_score": round(violence_score, 3),
        "stampede_score": round(stampede_score, 3),
    }


def run_live_mode():
    cameras = build_default_cameras()
    for cam in cameras:
        cam["cap"] = connect_camera(cam["url"])

    try:
        while True:
            now = time.time()
            processed_frames = []

            for cam in cameras:
                ret, frame = cam["cap"].read()

                if not ret or frame is None:
                    print(f"{cam['zone']} disconnected. Reconnecting...")
                    cam["cap"].release()
                    time.sleep(1)
                    cam["cap"] = connect_camera(cam["url"])

                    blank = np.zeros((FRAME_SIZE[1], FRAME_SIZE[0], 3), dtype=np.uint8)
                    cv2.putText(
                        blank,
                        f"{cam['zone']} - No Signal",
                        (20, 120),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2,
                    )
                    processed_frames.append(blank)
                    continue

                processed_frame, _ = process_frame(
                    source=cam,
                    frame=frame,
                    now=now,
                    send_to_backend=True,
                    save_snapshot=True,
                )
                processed_frames.append(processed_frame)

            while len(processed_frames) < 4:
                processed_frames.append(np.zeros((FRAME_SIZE[1], FRAME_SIZE[0], 3), dtype=np.uint8))

            top_row = np.hstack((processed_frames[0], processed_frames[1]))
            bottom_row = np.hstack((processed_frames[2], processed_frames[3]))
            grid = np.vstack((top_row, bottom_row))

            if SHOW_WINDOW:
                cv2.imshow("SikSikSafe Multi-Camera Monitor", grid)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except Exception as error:
        print("Runtime error:", error)
    finally:
        for cam in cameras:
            if cam["cap"] is not None:
                cam["cap"].release()
        cv2.destroyAllWindows()


def run_dataset_mode(dataset_dir: str):
    dataset_path = Path(dataset_dir)
    video_files = sorted(dataset_path.rglob("*.mp4"))

    if not video_files:
        print(f"No .mp4 videos found in dataset path: {dataset_path.resolve()}")
        return

    if len(video_files) > DATASET_MAX_VIDEOS:
        print(
            f"Found {len(video_files)} MP4 videos. "
            f"Using first {DATASET_MAX_VIDEOS} for prototype run."
        )
        video_files = video_files[:DATASET_MAX_VIDEOS]
    else:
        print(f"Found {len(video_files)} MP4 videos in {dataset_path.resolve()}")

    summary = []
    risk_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

    for video_path in video_files:
        source = create_source_state(zone=video_path.stem)
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"Skipping unreadable video: {video_path}")
            continue

        frame_index = 0
        highest_risk = "LOW"
        last_metrics = None
        high_risk_frames = 0

        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            frame_index += 1
            if frame_index % DATASET_FRAME_STRIDE != 0:
                continue

            now = time.time()
            processed_frame, metrics = process_frame(
                source=source,
                frame=frame,
                now=now,
                send_to_backend=DATASET_SEND_BACKEND,
                save_snapshot=False,
            )
            last_metrics = metrics

            if risk_rank[metrics["risk_level"]] > risk_rank[highest_risk]:
                highest_risk = metrics["risk_level"]
            if metrics["risk_level"] == "HIGH":
                high_risk_frames += 1

            if SHOW_WINDOW:
                cv2.imshow("ViolenceDetectioDataset Monitor", processed_frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        cap.release()
        if last_metrics is None:
            continue

        video_summary = {
            "video": str(video_path),
            "highest_risk": highest_risk,
            "high_risk_frames": high_risk_frames,
            "final_prediction": last_metrics["prediction"],
            "final_person_count": last_metrics["person_count"],
            "final_violence_score": last_metrics["violence_score"],
            "final_stampede_score": last_metrics["stampede_score"],
        }
        summary.append(video_summary)
        print(
            f"[{video_path.name}] highest_risk={highest_risk}, "
            f"high_risk_frames={high_risk_frames}, "
            f"violence={last_metrics['violence_score']}, "
            f"stampede={last_metrics['stampede_score']}"
        )

    cv2.destroyAllWindows()

    if DATASET_SUMMARY_PATH:
        output_path = Path(DATASET_SUMMARY_PATH)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as output_file:
            json.dump(summary, output_file, indent=2)
        print(f"Saved dataset summary to {output_path.resolve()}")


if __name__ == "__main__":
    if INPUT_MODE == "dataset":
        run_dataset_mode(DATASET_DIR)
    else:
        run_live_mode()