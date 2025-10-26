# LMV-HMV-classifier

A mobile-first repository for detecting LMV/HMV vehicles and capturing violation evidence from CCTV streams and uploaded videos. The project is split into four logical parts so each can be developed and deployed independently.

## Layout

- `frontend/flutter/` — Flutter app (mobile & web UI for authority users). Contains the Flutter app sources and tests.
- `backend/` — Flask-based backend that accepts uploads, forwards them to the AI worker for processing, stores metadata locally (SQLite), and serves artifacts.
- `ai/` — AI worker (Flask) that runs vehicle detection + OCR (YOLO, EasyOCR). Produces annotated outputs and CSV artifacts.
- `database/` — Helper scripts for evidence upload (Firebase Admin examples) and a tiny SQLite helper to store evidence locally.

## Quick start (local dev)

Prerequisites

- Python 3.8+ installed and on PATH
- pip
- (Optional) Flutter SDK if you want to run the frontend app
- If you plan to run the AI worker you need ML packages and model files (see notes below)

### 1) Backend

Open PowerShell in the repo root and create a virtualenv:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

Run the backend:

```powershell
cd backend
python .\server.py
```

The backend listens by default on http://0.0.0.0:8000 and exposes:

- GET `/` — health
- POST `/upload_video` — accepts multipart/form-data `video` and forwards to AI worker
- GET `/artifact?file=<name>` — download artifact (proxy)

Environment variables (use before running the backend):

- `AI_WORKER_URL` — URL of the AI worker `/process` endpoint (default: `http://127.0.0.1:5000/process`)

### 2) AI worker (local)

The `ai/` folder contains a Flask app. It expects model files referenced in `ai/main.py`. Install dependencies separately (not provided as a full pinned file in this repo because models and accelerators vary):

- ultralytics (YOLOv8)
- opencv-python
- easyocr

Run locally (PowerShell):

```powershell
cd ai
# Optionally set folders and GPU usage
$env:AI_UPLOAD_FOLDER = (Resolve-Path .\data\uploads).Path
$env:AI_OUTPUT_FOLDER = (Resolve-Path .\data\outputs).Path
$env:EASYOCR_GPU = "false"
python .\app.py
```

The AI worker exposes:

- POST `/process` — accepts `video` multipart file, runs detection, writes artifacts into `ai/data/outputs`, and returns JSON with paths.
- GET `/download/<filetype>` — download `video`, `vehicle_csv` or `plates_csv` produced by last run.

Notes about AI dependencies and models

- `ai/main.py` references YOLO models (paths like `models/yolov8n.pt`). You must provide trained model files at the expected locations or change the paths inside `ai/main.py`.
- Running the detection requires the heavy ML packages and a suitable environment (CPU-only works but is slower). Use `EASYOCR_GPU` env var to enable/disable GPU for EasyOCR.

### 3) Upload test (quick smoke)

From a separate shell, upload a small test video to the backend (PowerShell example using curl):

```powershell
curl -X POST -F "video=@C:\path\to\sample.mp4" http://127.0.0.1:8000/upload_video
```

The backend will forward the file to the AI worker and store a brief summary row in `backend/evidence.db` (SQLite).

### 4) Frontend (Flutter)

To run the mobile/web UI you need the Flutter SDK. The Flutter app is in `frontend/flutter/`. Typical steps:

```powershell
cd frontend\flutter
flutter pub get
flutter run   # or flutter run -d chrome for web
```

The UI is a simple authority dashboard and demo login screen. It can be wired to hit the backend API endpoints.

## Database / Evidence storage

- `database/evidence_db.py` — tiny SQLite helper (init / insert / list).
- `database/upload_vehicle_evidence.py` and `database/upload_zones.py` — helper scripts showing how to upload to Firebase Storage / Firestore using `firebase_admin`. These require a service account JSON and proper `FIREBASE_STORAGE_BUCKET` env var.

Set environment variables for Firebase scripts (PowerShell example):

```powershell
# $env:SERVICE_ACCOUNT_PATH = "D:\path\to\serviceAccount.json"
# $env:FIREBASE_STORAGE_BUCKET = "your-project-id.appspot.com"
```

## Events and notifications

Current implementation is minimal: the AI worker processes videos and returns a results dict. The backend stores a minimal evidence record in SQLite. To implement the full event flow described in the project overview (emit `violation:<jurisdiction>` events and send push notifications to authority users) you can choose one of the following next steps:

- Use a message broker (Redis pub/sub, RabbitMQ, or Kafka) where AI pushes `violation:<jurisdiction>` messages and the backend or a notification service subscribes and sends push notifications (FCM/APNs).
- Add a small WebSocket/Socket.IO server to the backend to push real-time notifications to connected admin UIs.

If you'd like, I can add a simple Redis pub/sub demo and a small notification sender that prints or logs messages and sends FCM notifications (requires server key).

## Environment summary

Key env vars used by scripts in this repo:

- `AI_WORKER_URL` — backend -> AI worker URL (default: `http://127.0.0.1:5000/process`)
- `AI_UPLOAD_FOLDER`, `AI_OUTPUT_FOLDER` — override AI worker storage locations
- `EASYOCR_GPU` — enable EasyOCR GPU (true/false)
- `SERVICE_ACCOUNT_PATH`, `FIREBASE_STORAGE_BUCKET` — used by `database/` scripts

## Next steps I can implement for you

- Add `ai/requirements.txt` and a Dockerfile for AI worker (CPU-friendly pinned packages).
- Wire Redis or Socket.IO for real-time `violation:<jurisdiction>` events and a sample authority subscription.
- Wire backend to automatically upload images/artifacts to Firebase Storage / S3 and store proper evidence docs using `database/upload_vehicle_evidence.py`.
- Clean up/move remaining root-level Flutter files and remove duplicates.

Tell me which of the next steps above you'd like me to implement and I will continue.

## Quick Docker Compose (dev)

If you want to run Redis, the AI worker and the backend locally using Docker Compose (best-effort; AI image may require more tuning for ultralytics and model files), run:

```powershell
docker compose up --build
```

This will:

- start a Redis instance on localhost:6379
- build and run the AI worker (exposes port 5000)
- build and run the backend (exposes port 8000)

Note: The AI Dockerfile installs Python packages and system libs but may still require model files available under `ai/models/` and additional system dependencies depending on your platform. Use this for local development and testing of integration flows.

# LMV-HMV-classifier - repo reorganized

This repository contains a mobile-first system for vehicle detection and violation evidence collection.

Top-level layout after reorganization:

- `frontend/flutter/` — Flutter mobile/web app (UI for authority users)
- `backend/` — Python Flask backend that accepts uploads, forwards to AI worker, stores metadata
- `ai/` — AI worker (Flask) that runs detection and OCR and produces artifacts
- `database/` — database utilities and upload scripts (Firestore+Firebase helpers, SQLite helper)

See each folder for run instructions. The AI and backend are simple Flask apps; the frontend is a Flutter app.
