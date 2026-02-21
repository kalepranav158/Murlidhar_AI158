import sqlite3
import json
from datetime import datetime

DB_NAME = "practice_sessions.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
CREATE TABLE IF NOT EXISTS analytics_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    timestamp TEXT,
    average_accuracy REAL,
    trend_slope REAL,
    predicted_next_accuracy REAL,
    consistency_index REAL,
    difficulty_recommendation TEXT,
    trend_label TEXT
)
""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
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


def save_session(user_id, reference, played, result):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sessions (
            user_id,
            timestamp,
            reference,
            played_notes,
            note_accuracy,
            avg_pitch_error,
            avg_timing_error,
            mistakes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
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



def get_sessions(user_id: str , limit: int = 100):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if user_id:
        cursor.execute(
            "SELECT * FROM sessions WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )
    else:
        cursor.execute(
            "SELECT * FROM sessions ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        "SELECT * FROM sessions ORDER BY id DESC LIMIT ?",
        (limit,)
    

    rows = cursor.fetchall()
    conn.close()

    sessions = []

    for row in rows:
        sessions.append({
            "id": row["id"],
            "timestamp": row["timestamp"],
            "note_accuracy": row["note_accuracy"],
            "avg_pitch_error": row["avg_pitch_error"],
            "avg_timing_error": row["avg_timing_error"]
        })

    return sessions


def get_last_session(user_id: str):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM sessions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None

def save_analytics_snapshot(user_id: str, snapshot: dict):
    """
    Saves structured analytics snapshot into database.
    """

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO analytics_snapshots (
            user_id,
            timestamp,
            average_accuracy,
            trend_slope,
            predicted_next_accuracy,
            consistency_index,
            difficulty_recommendation,
            trend_label
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        datetime.now().isoformat(),
        snapshot.get("average_accuracy"),
        snapshot.get("trend_slope"),
        snapshot.get("predicted_next_accuracy"),
        snapshot.get("consistency_index"),
        snapshot.get("difficulty_recommendation"),
        snapshot.get("trend_label")
    ))

    conn.commit()
    conn.close()



def get_latest_analytics_snapshot(user_id: str):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM analytics_snapshots
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None
