import sqlite3
import json
from datetime import datetime

DB_NAME = "practice_sessions.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            reference TEXT,
            played_notes TEXT,
            note_accuracy REAL,
            avg_pitch_error REAL,
            avg_timing_error REAL,
            mistakes TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_session(reference, played, result):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sessions (
            timestamp,
            reference,
            played_notes,
            note_accuracy,
            avg_pitch_error,
            avg_timing_error,
            mistakes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        json.dumps(reference),
        json.dumps(played),
        result["note_accuracy"],
        result["avg_pitch_error_cents"],
        result["avg_timing_error_sec"],
        json.dumps(result["mistakes"])
    ))

    conn.commit()
    conn.close()


def get_all_sessions():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sessions ORDER BY id DESC")
    rows = cursor.fetchall()

    conn.close()
    return rows
