"""
Laptop-camera-only variant of app.py.

Live mode reads from a single local webcam (default camera index 0) and
does not use any DVR/RTSP camera sources.
"""

import os
import time
import importlib.util
from pathlib import Path

import cv2
import numpy as np

# Default dataset path for your local Windows machine.
# This can still be overridden by setting DATASET_VIDEO_DIR.
os.environ.setdefault(
    "DATASET_VIDEO_DIR",
    r"C:\Users\Acer\Downloads\ViolenceDetectionDataset",
)


def load_base_app_module():
    base_path = Path(__file__).with_name("app.py")
    if not base_path.exists():
        raise RuntimeError(f"Base app file not found: {base_path}")

    module_name = "siksiksafe_base_app"
    spec = importlib.util.spec_from_file_location(module_name, base_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load base app module from {base_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    required_attributes = [
        "INPUT_MODE",
        "DATASET_DIR",
        "run_dataset_mode",
        "create_source_state",
        "process_frame",
        "FRAME_SIZE",
        "SHOW_WINDOW",
    ]
    missing = [attr for attr in required_attributes if not hasattr(module, attr)]
    if missing:
        missing_text = ", ".join(missing)
        raise RuntimeError(
            "Your app.py does not contain the expected base pipeline. "
            f"Missing attributes: {missing_text}. "
            "Restore the original base app.py, then run app_laptop.py for webcam mode."
        )

    return module


base = load_base_app_module()

LAPTOP_CAMERA_INDEX = int(os.getenv("LAPTOP_CAMERA_INDEX", "0"))
LAPTOP_ZONE_NAME = os.getenv("LAPTOP_ZONE_NAME", "Laptop Camera")
RECONNECT_DELAY_SECONDS = float(os.getenv("RECONNECT_DELAY_SECONDS", "1.0"))


def connect_laptop_camera(camera_index: int):
    print(f"Connecting to laptop camera index: {camera_index}")
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def run_live_mode_laptop():
    # Single camera only: laptop webcam.
    camera = base.create_source_state(
        zone=LAPTOP_ZONE_NAME,
        url=f"device://{LAPTOP_CAMERA_INDEX}",
    )
    camera["cap"] = connect_laptop_camera(LAPTOP_CAMERA_INDEX)

    try:
        while True:
            now = time.time()
            ret, frame = camera["cap"].read()

            if not ret or frame is None:
                print("Laptop camera disconnected. Reconnecting...")
                camera["cap"].release()
                time.sleep(RECONNECT_DELAY_SECONDS)
                camera["cap"] = connect_laptop_camera(LAPTOP_CAMERA_INDEX)

                processed_frame = np.zeros((base.FRAME_SIZE[1], base.FRAME_SIZE[0], 3), dtype=np.uint8)
                cv2.putText(
                    processed_frame,
                    "Laptop Camera - No Signal",
                    (20, 120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2,
                )
            else:
                processed_frame, _ = base.process_frame(
                    source=camera,
                    frame=frame,
                    now=now,
                    send_to_backend=True,
                    save_snapshot=True,
                )

            if base.SHOW_WINDOW:
                cv2.imshow("SikSikSafe Laptop Camera Monitor", processed_frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except Exception as error:
        print("Runtime error:", error)
    finally:
        if camera["cap"] is not None:
            camera["cap"].release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    if base.INPUT_MODE == "dataset":
        base.run_dataset_mode(base.DATASET_DIR)
    else:
        run_live_mode_laptop()
