import os
import sys
import hashlib
import uuid
from datetime import datetime, timezone
import firebase_admin
from firebase_admin import credentials, firestore, storage

# -----------------------
# CONFIG - update these
# -----------------------
import os

# Allow overriding via environment variables to avoid hard-coded paths
SERVICE_ACCOUNT_PATH = os.environ.get(
    "SERVICE_ACCOUNT_PATH",
    r"d:\Project\RoadEyeAI\zonedatabase-d0432-firebase-adminsdk-fbsvc-3f55e1789f.json",
)
FIREBASE_STORAGE_BUCKET = os.environ.get(
    "FIREBASE_STORAGE_BUCKET", "your-project-id.appspot.com"
)  # <-- replace with your bucket name
FIRESTORE_COLLECTION = "VehicleLogs"  # collection to store logs
# -----------------------

# Initialize Firebase
if not os.path.isfile(SERVICE_ACCOUNT_PATH):
    print("ERROR: service account JSON not found at:", SERVICE_ACCOUNT_PATH)
    sys.exit(1)

cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
firebase_admin.initialize_app(cred, {"storageBucket": FIREBASE_STORAGE_BUCKET})
db = firestore.client()
bucket = storage.bucket()


def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def upload_image_to_storage(local_path, dest_folder="vehicle_images"):
    """Uploads local image file to Firebase Storage and returns blob path and size."""
    if not os.path.isfile(local_path):
        raise FileNotFoundError(f"Image not found: {local_path}")

    ext = os.path.splitext(local_path)[1] or ".jpg"
    unique_name = f"{dest_folder}/{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex}{ext}"
    blob = bucket.blob(unique_name)

    # Upload file (non-resumable for simplicity)
    blob.upload_from_filename(local_path, content_type="image/jpeg")

    # Optionally you can make public (not recommended for evidence). We store path + signed URL instead.
    # blob.make_public()

    return unique_name, blob.size if blob.exists() else None


def generate_signed_url(blob_path, expires_seconds=7 * 24 * 3600):
    """Return a temporary signed URL for a blob (useful for admin viewing)."""
    blob = bucket.blob(blob_path)
    url = blob.generate_signed_url(expiration=expires_seconds)
    return url


def upload_vehicle_record(
    local_image_path,
    plate_number,
    camera_id,
    camera_name,
    camera_lat,
    camera_lon,
    vehicle_type="HMV",  # or "LMV", "two_wheeler", etc.
):
    """Uploads image to Storage and creates a Firestore evidence document."""
    # 1) compute hash
    image_hash = sha256_of_file(local_image_path)

    # 2) upload image
    storage_path, size = upload_image_to_storage(local_image_path)

    # 3) optional signed url for temporary preview (7 days)
    try:
        signed_url = generate_signed_url(storage_path, expires_seconds=7 * 24 * 3600)
    except Exception:
        signed_url = None

    # 4) compose Firestore doc
    now = datetime.now(timezone.utc)
    doc = {
        "plate_number": plate_number,
        "image_storage_path": storage_path,
        "image_signed_url_preview": signed_url,  # optional short-lived preview (not required)
        "image_hash_sha256": image_hash,
        "camera_id": camera_id,
        "camera_name": camera_name,
        "camera_location": {"lat": float(camera_lat), "lon": float(camera_lon)},
        "vehicle_type": vehicle_type,
        "captured_at_iso": now.isoformat(),
        "captured_at_ts": int(now.timestamp() * 1000),  # milliseconds epoch
        "evidence_uploaded_at": firestore.SERVER_TIMESTAMP,
        # optional: any extra metadata
        "meta": {"uploader": "local_test_script", "file_bytes": size},
    }

    # 5) write to Firestore
    doc_ref = db.collection(FIRESTORE_COLLECTION).add(doc)
    return doc_ref, doc


# -----------------------
# Example usage / CLI
# -----------------------
if __name__ == "__main__":
    # sample run:
    # python upload_vehicle_evidence.py "d:/Project/RoadEyeAI/images/car1.jpg" "MH12AB1234" cam001 "GateCam-1" 18.5204 73.8567 HMV

    if len(sys.argv) < 7:
        print("Usage:")
        print(
            " python upload_vehicle_evidence.py <image_path> <plate_number> <camera_id> <camera_name> <camera_lat> <camera_lon> [vehicle_type]"
        )
        print("Example:")
        print(
            ' python upload_vehicle_evidence.py "d:/Project/RoadEyeAI/images/car1.jpg" "MH12AB1234" cam001 "GateCam-1" 18.5204 73.8567 HMV'
        )
        sys.exit(1)

    image_path = sys.argv[1]
    plate = sys.argv[2]
    cam_id = sys.argv[3]
    cam_name = sys.argv[4]
    cam_lat = float(sys.argv[5])
    cam_lon = float(sys.argv[6])
    vtype = sys.argv[7] if len(sys.argv) > 7 else "HMV"

    try:
        ref, data = upload_vehicle_record(
            image_path, plate, cam_id, cam_name, cam_lat, cam_lon, vtype
        )
        print(
            "✅ Uploaded evidence doc id:", ref[1].id
        )  # .add returns (write_result, document_reference) depending on admin SDK; print doc id if available
        print("Stored fields:")
        for k, v in data.items():
            print(" ", k, ":", v)
    except Exception as e:
        print("ERROR:", e)
        raise
