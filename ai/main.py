from ultralytics import YOLO
import cv2
import csv
from pathlib import Path
import time
import os
import easyocr


def run_detection(video_path, output_dir="outputs"):
    """
    Runs vehicle and license plate detection on the given video.
    Returns paths to output video and CSV files.
    """

    # ---------------- CONFIG ----------------
    MODEL_PATH = "models/yolov8n.pt"  # vehicle detection model
    PLATE_MODEL_PATH = "models/license_plate_detector.pt"  # license plate model
    VIDEO_PATH = video_path  # input video
    OUTPUT_VIDEO = os.path.join(output_dir, "output_video.avi")  # annotated output
    VEHICLE_CSV = os.path.join(output_dir, "vehicle_counts.csv")  # vehicle counts
    PLATE_CSV = os.path.join(output_dir, "plates.csv")  # plate numbers
    CONF_THRESHOLD = 0.3
    RESIZE_SCALE = 0.75
    HEADLESS = True  # no window display
    # ----------------------------------------

    os.makedirs(output_dir, exist_ok=True)

    # -------- File checks --------
    if not Path(MODEL_PATH).exists():
        raise FileNotFoundError(f"Vehicle model not found: {MODEL_PATH}")
    if not Path(PLATE_MODEL_PATH).exists():
        raise FileNotFoundError(f"Plate model not found: {PLATE_MODEL_PATH}")
    if not Path(VIDEO_PATH).exists():
        raise FileNotFoundError(f"Video not found: {VIDEO_PATH}")

    # -------- Load models --------
    model = YOLO(MODEL_PATH)
    plate_model = YOLO(PLATE_MODEL_PATH)
    # GPU may not be available on all deployments; allow fallback via env var
    try:
        import os

        use_gpu = os.environ.get("EASYOCR_GPU", "false").lower() in ("1", "true", "yes")
    except Exception:
        use_gpu = False
    reader = easyocr.Reader(["en"], gpu=use_gpu)

    # Optional Redis publisher for violation events
    REDIS_URL = os.environ.get("REDIS_URL")
    redis_client = None
    if REDIS_URL:
        try:
            import redis as _redis

            redis_client = _redis.from_url(REDIS_URL)
        except Exception:
            redis_client = None

    JURISDICTION = os.environ.get("JURISDICTION", "unknown")

    # -------- Class setup --------
    CLASS_NAMES = model.model.names or {
        i: f"class_{i}" for i in range(model.model.model.nc)
    }

    def normalize(n: str) -> str:
        return n.lower().replace(" ", "").strip()

    LMV_CLASSES = {"car", "motorbike", "motorcycle", "auto", "autorickshaw", "scooter"}
    HMV_CLASSES = {"bus", "truck", "tractor"}
    LMV_IDS = {k for k, v in CLASS_NAMES.items() if normalize(v) in LMV_CLASSES}
    HMV_IDS = {k for k, v in CLASS_NAMES.items() if normalize(v) in HMV_CLASSES}

    # -------- Video setup --------
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        raise Exception("Video file could not be opened")

    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) * RESIZE_SCALE)
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) * RESIZE_SCALE)
    fps = cap.get(cv2.CAP_PROP_FPS) or 20.0

    out = cv2.VideoWriter(
        OUTPUT_VIDEO, cv2.VideoWriter_fourcc(*"XVID"), fps, (frame_w, frame_h)
    )
    if not out.isOpened():
        raise Exception("VideoWriter could not be created")

    # -------- CSV setup --------
    Path(VEHICLE_CSV).unlink(missing_ok=True)
    v_csv = open(VEHICLE_CSV, "w", newline="")
    v_writer = csv.writer(v_csv)
    v_writer.writerow(["Vehicle_ID", "Vehicle_Type"])

    Path(PLATE_CSV).unlink(missing_ok=True)
    p_csv = open(PLATE_CSV, "w", newline="")
    p_writer = csv.writer(p_csv)
    p_writer.writerow(["Vehicle_ID", "Vehicle_Type", "Plate_Number"])

    # -------- Helper for OCR --------
    def detect_plate_text(crop):
        """Detect license plate and return best text"""
        try:
            results = plate_model.predict(crop, conf=0.4, verbose=False)[0]
            if results and results.boxes is not None and len(results.boxes) > 0:
                for box in results.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    plate_img = crop[y1:y2, x1:x2]
                    if plate_img.size == 0:
                        continue
                    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
                    gray = cv2.equalizeHist(gray)
                    ocr = reader.readtext(gray, detail=1)
                    if not ocr:
                        continue
                    best = max(ocr, key=lambda x: x[2] if len(x) == 3 else 0)
                    text = best[1].strip()
                    clean = "".join(
                        ch for ch in text if ch.isalnum() or ch in ["-", " "]
                    )
                    return clean
        except Exception:
            return ""
        return ""

    # -------- Tracking memory --------
    counted_ids = set()
    plate_done = {}
    evidence_files = []

    # -------- MAIN LOOP --------
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        resized = cv2.resize(frame, (frame_w, frame_h))
        results = model.track(
            resized, persist=True, conf=CONF_THRESHOLD, verbose=False
        )[0]

        if results and results.boxes is not None:
            for box in results.boxes:
                conf = box.conf[0].item() if hasattr(box, "conf") else 1.0
                if conf < CONF_THRESHOLD:
                    continue

                cls_id = int(box.cls[0])
                if cls_id not in (LMV_IDS | HMV_IDS):
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                track_id = (
                    int(box.id[0]) if getattr(box, "id", None) is not None else None
                )
                vehicle_type = "LMV" if cls_id in LMV_IDS else "HMV"

                # Vehicle count only once
                if track_id is not None and track_id not in counted_ids:
                    counted_ids.add(track_id)
                    v_writer.writerow([track_id, vehicle_type])

                # License plate OCR only once per vehicle
                if track_id is not None and track_id not in plate_done:
                    crop = resized[y1:y2, x1:x2]
                    plate_text = detect_plate_text(crop)
                    if plate_text:
                        plate_done[track_id] = plate_text
                        p_writer.writerow([track_id, vehicle_type, plate_text])
                        # save crop evidence
                        try:
                            evidence_name = (
                                f"evidence_{track_id}_{int(time.time())}.jpg"
                            )
                            evidence_path = os.path.join(output_dir, evidence_name)
                            ok = cv2.imwrite(evidence_path, crop)
                            if ok:
                                evidence_files.append(evidence_path)
                        except Exception:
                            evidence_path = None

                        # publish violation event (if redis available)
                        try:
                            if redis_client is not None:
                                import json as _json

                                event = {
                                    "jurisdiction": JURISDICTION,
                                    "track_id": track_id,
                                    "vehicle_type": vehicle_type,
                                    "plate": plate_text,
                                    "evidence_path": evidence_path,
                                }
                                channel = f"violation:{JURISDICTION}"
                                redis_client.publish(channel, _json.dumps(event))
                        except Exception:
                            pass
                        cv2.putText(
                            resized,
                            plate_text,
                            (x1, max(y1 - 10, 20)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (255, 255, 0),
                            2,
                        )

                # Draw vehicle box
                color = (0, 255, 0) if vehicle_type == "LMV" else (0, 0, 255)
                label = f"{CLASS_NAMES[cls_id]} | ID:{track_id} | {vehicle_type}"
                cv2.rectangle(resized, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    resized,
                    label,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2,
                )

        out.write(resized)

        if not HEADLESS:
            cv2.imshow("Vehicle + Plate Detection", resized)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    # -------- Cleanup --------
    cap.release()
    out.release()
    v_csv.close()
    p_csv.close()
    if not HEADLESS:
        cv2.destroyAllWindows()

    return {
        "video": os.path.abspath(OUTPUT_VIDEO),
        "vehicle_csv": os.path.abspath(VEHICLE_CSV),
        "plates_csv": os.path.abspath(PLATE_CSV),
        "evidence_files": [os.path.basename(p) for p in evidence_files],
    }
