"""Simple integration test that posts a small file to backend and checks sqlite entry.

This test assumes backend is running at http://127.0.0.1:8000 and ai_worker is available.
Place a tiny sample MP4 at tests/sample.mp4 before running.
"""

import requests
import time
import sqlite3
from pathlib import Path

BACKEND = "http://127.0.0.1:8000"
SAMPLE = Path("tests/sample.mp4")


def run():
    if not SAMPLE.exists():
        print("Place a small sample video at tests/sample.mp4 to run this test.")
        return

    with SAMPLE.open("rb") as fh:
        files = {"video": (SAMPLE.name, fh, "video/mp4")}
        r = requests.post(BACKEND + "/upload_video", files=files, timeout=600)
        print("backend response:", r.status_code, r.text)

    # wait a bit for async uploads
    time.sleep(5)

    db = Path("backend/evidence.db")
    if not db.exists():
        print("backend sqlite not found at backend/evidence.db")
        return
    conn = sqlite3.connect(str(db))
    c = conn.cursor()
    c.execute(
        "SELECT id, plate, vehicle_type, created_at FROM evidence ORDER BY id DESC LIMIT 5"
    )
    rows = c.fetchall()
    conn.close()
    print("recent evidence rows:", rows)


if __name__ == "__main__":
    run()
