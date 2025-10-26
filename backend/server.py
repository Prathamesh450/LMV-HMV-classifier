from flask import Flask, request, jsonify, send_file
import os
import requests
import sqlite3
import csv
from pathlib import Path
import tempfile
import json

app = Flask(__name__)

ROOT = Path(__file__).resolve().parent
AI_URL = os.environ.get("AI_WORKER_URL", "http://127.0.0.1:5000/process")
UPLOADS = ROOT / "uploads"
OUTPUTS_PROXY = ROOT / "artifacts"  # proxy to ai outputs
DATABASE = ROOT / "evidence.db"

UPLOADS.mkdir(parents=True, exist_ok=True)
OUTPUTS_PROXY.mkdir(parents=True, exist_ok=True)


def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate TEXT,
        vehicle_type TEXT,
        ai_response TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )
    conn.commit()
    conn.close()


init_db()


@app.route("/")
def home():
    return jsonify({"message": "Backend server alive"})


@app.route("/upload_video", methods=["POST"])
def upload_video():
    if "video" not in request.files:
        return jsonify({"error": "No video provided"}), 400

    f = request.files["video"]
    filename = f.filename or "upload_" + next(tempfile._get_candidate_names())
    dest = UPLOADS / filename
    f.save(dest)

    # Forward to AI worker
    with open(dest, "rb") as fh:
        files = {"video": (filename, fh, "video/mp4")}
        resp = requests.post(AI_URL, files=files, timeout=300)

    if resp.status_code != 200:
        return jsonify({"error": "AI worker failed", "details": resp.text}), 500

    data = resp.json()

    # store summary into sqlite using helper (with fallback)
    plate = None
    vehicle_type = None
    ai_json = "{}"
    try:
        ai_json = json.dumps(data.get("results", {}))
        plate = data.get("results", {}).get("plates_csv")
        vehicle_type = "unknown"
    except Exception:
        ai_json = "{}"

    try:
        # prefer the database helper if available
        from database.evidence_db import insert_evidence

        insert_evidence(plate, vehicle_type, data.get("results", {}))
    except Exception:
        # fallback: write directly to backend sqlite
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute(
            "INSERT INTO evidence (plate, vehicle_type, ai_response) VALUES (?, ?, ?)",
            (plate, vehicle_type, ai_json),
        )
        conn.commit()
        conn.close()

    # Attempt to upload any evidence artifacts returned by the AI worker
    try:
        results = data.get("results", {}) or {}
        evidence_files = results.get("evidence_files") or []

        # Helper: try to extract a plate from a plates CSV if present
        def extract_first_plate_from_csv(csv_path):
            try:
                if not csv_path:
                    return None
                csv_name = os.path.basename(csv_path)
                csv_local = OUTPUTS_PROXY / csv_name
                if not csv_local.exists():
                    return None
                with open(csv_local, newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    _ = next(reader, None)
                    for row in reader:
                        if len(row) >= 3:
                            # expected: Vehicle_ID, Vehicle_Type, Plate_Number
                            return row[2]
                        elif len(row) >= 1:
                            return row[0]
            except Exception:
                return None

        plates_csv = results.get("plates_csv")
        sample_plate = extract_first_plate_from_csv(plates_csv)

        # Gather camera metadata from env (fallbacks available)
        cam_id = os.environ.get("CAMERA_ID", "unknown_cam")
        cam_name = os.environ.get("CAMERA_NAME", "unknown")
        cam_lat = float(os.environ.get("CAMERA_LAT", 0.0))
        cam_lon = float(os.environ.get("CAMERA_LON", 0.0))

        # upload each artifact file if present in artifacts folder
        from database.upload_vehicle_evidence import upload_vehicle_record

        for fname in evidence_files:
            try:
                local_path = OUTPUTS_PROXY / fname
                if local_path.exists():
                    vtype = vehicle_type or "HMV"
                    plate_to_send = sample_plate or ""
                    try:
                        ref, doc = upload_vehicle_record(
                            str(local_path),
                            plate_to_send,
                            cam_id,
                            cam_name,
                            cam_lat,
                            cam_lon,
                            vtype,
                        )
                        app.logger.info(
                            f"Uploaded evidence {fname} to storage; doc={getattr(ref[1], 'id', str(ref))}"
                        )
                    except Exception as e:
                        app.logger.warning(f"Failed to upload evidence {fname}: {e}")
                else:
                    app.logger.debug(
                        f"Evidence file not found in artifacts folder: {fname}"
                    )
            except Exception as e:
                app.logger.exception(f"Error processing evidence file {fname}: {e}")
    except Exception:
        # avoid failing the API if uploads fail
        app.logger.exception("Error while processing evidence uploads")

    return jsonify({"message": "processed", "ai": data})


@app.route("/artifact", methods=["GET"])
def get_artifact():
    filename = request.args.get("file")
    if not filename:
        return jsonify({"error": "file query param required"}), 400
    path = OUTPUTS_PROXY / filename
    if not path.exists():
        return jsonify({"error": "not found"}), 404
    return send_file(str(path), as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
