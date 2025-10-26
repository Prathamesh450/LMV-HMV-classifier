from flask import Flask, request, jsonify, send_file
from main import run_detection
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Use local folders inside the ai/ directory so the worker is portable.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.environ.get(
    "AI_UPLOAD_FOLDER", os.path.join(BASE_DIR, "data", "uploads")
)
OUTPUT_FOLDER = os.environ.get(
    "AI_OUTPUT_FOLDER", os.path.join(BASE_DIR, "data", "outputs")
)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return jsonify({"message": "🚗 Vehicle + License Plate Detection API is running!"})


@app.route("/process", methods=["POST"])
def process_video():
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    file = request.files["video"]
    filename = secure_filename(file.filename)
    video_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(video_path)

    try:
        # Run the detection
        results = run_detection(video_path, OUTPUT_FOLDER)
        return jsonify({"message": "✅ Detection complete", "results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download/<string:filetype>", methods=["GET"])
def download_file(filetype):
    if filetype == "video":
        path = os.path.join(OUTPUT_FOLDER, "output_video.avi")
    elif filetype == "vehicle_csv":
        path = os.path.join(OUTPUT_FOLDER, "vehicle_counts.csv")
    elif filetype == "plates_csv":
        path = os.path.join(OUTPUT_FOLDER, "plates.csv")
    else:
        return jsonify({"error": "Invalid file type"}), 400

    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404

    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
