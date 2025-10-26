import sqlite3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
DB = ROOT / "evidence.sqlite"


def init_db():
    conn = sqlite3.connect(DB)
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


def insert_evidence(plate, vehicle_type, ai_response_dict):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO evidence (plate, vehicle_type, ai_response) VALUES (?, ?, ?)",
        (plate, vehicle_type, json.dumps(ai_response_dict)),
    )
    conn.commit()
    conn.close()


def list_evidence(limit=100):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "SELECT id, plate, vehicle_type, ai_response, created_at FROM evidence ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = c.fetchall()
    conn.close()
    return rows


if __name__ == "__main__":
    init_db()
    print("Initialized evidence DB at", DB)
