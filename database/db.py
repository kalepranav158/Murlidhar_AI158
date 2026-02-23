import sqlite3
import json
from datetime import datetime

DB_NAME = "Practice_data.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()



        # Analytics Snapshots Table
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
        # Practice Sessions Table
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
    mistakes TEXT,
    composite_score REAL,
    pitch_index REAL,
    rhythm_index REAL,
    consistency_index REAL
)
""")




 # Alankar Mastery Table
    cursor.execute("""
CREATE TABLE IF NOT EXISTS alankar_mastery (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    alankar_id TEXT,
    highest_level INTEGER,
    best_tempo INTEGER,
    average_score REAL,
    total_attempts INTEGER,
    mastered INTEGER
)
""")
    

    # songs Phrase Mastery Table 
    cursor.execute("""
CREATE TABLE IF NOT EXISTS phrase_mastery (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    song_id TEXT,
    phrase_id INTEGER,
    avg_accuracy REAL,
    avg_pitch_error REAL,
    avg_timing_error REAL,
    total_attempts INTEGER,
    mastered INTEGER
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
        mistakes,
        composite_score,
        pitch_index,
        rhythm_index,
        consistency_index
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    user_id,
    datetime.now().isoformat(),
    json.dumps(reference),
    json.dumps(played),
    result["note_accuracy"],
    result["avg_pitch_error_cents"],
    result["avg_timing_error_sec"],
    json.dumps(result["mistakes"]),
    result.get("composite_score"),
    result.get("pitch_index"),
    result.get("rhythm_index"),
    result.get("consistency_index"),
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
    "avg_timing_error": row["avg_timing_error"],
    "composite_score": row["composite_score"],
    "pitch_index": row["pitch_index"],
    "rhythm_index": row["rhythm_index"],
    "consistency_index": row["consistency_index"]
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



def update_alankar_mastery(user_id: str, alankar_id: str, level_index: int, tempo: int, composite_score: float):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM alankar_mastery
        WHERE user_id = ? AND alankar_id = ?
    """, (user_id, alankar_id))

    row = cursor.fetchone()

    if row:
        # Update existing
        new_attempts = row[6] + 1
        new_avg = ((row[5] * row[6]) + composite_score) / new_attempts
        highest_level = max(row[3], level_index)
        best_tempo = max(row[4], tempo)
        mastered = 1 if new_avg >= 0.9 else 0

        cursor.execute("""
            UPDATE alankar_mastery
            SET highest_level=?, best_tempo=?, average_score=?, total_attempts=?, mastered=?
            WHERE id=?
        """, (
            highest_level,
            best_tempo,
            new_avg,
            new_attempts,
            mastered,
            row[0]
        ))

    else:
        mastered = 1 if composite_score >= 0.9 else 0

        cursor.execute("""
            INSERT INTO alankar_mastery (
                user_id, alankar_id, highest_level, best_tempo,
                average_score, total_attempts, mastered
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            alankar_id,
            level_index,
            tempo,
            composite_score,
            1,
            mastered
        ))

    conn.commit()
    conn.close()





def update_phrase_mastery(
    user_id: str,
    song_id: str,
    phrase_id: int,
    accuracy: float,
    pitch_error: float,
    timing_error: float
):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM phrase_mastery
        WHERE user_id=? AND song_id=? AND phrase_id=?
    """, (user_id, song_id, phrase_id))

    row = cursor.fetchone()

    if row:
        new_attempts = row[7] + 1
        new_avg_accuracy = ((row[4] * row[7]) + accuracy) / new_attempts
        new_avg_pitch = ((row[5] * row[7]) + pitch_error) / new_attempts
        new_avg_timing = ((row[6] * row[7]) + timing_error) / new_attempts

        mastered = 1 if new_avg_accuracy >= 95 else 0

        cursor.execute("""
            UPDATE phrase_mastery
            SET avg_accuracy=?, avg_pitch_error=?, avg_timing_error=?,
                total_attempts=?, mastered=?
            WHERE id=?
        """, (
            new_avg_accuracy,
            new_avg_pitch,
            new_avg_timing,
            new_attempts,
            mastered,
            row[0]
        ))

    else:
        mastered = 1 if accuracy >= 95 else 0

        cursor.execute("""
            INSERT INTO phrase_mastery (
                user_id, song_id, phrase_id,
                avg_accuracy, avg_pitch_error,
                avg_timing_error, total_attempts, mastered
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            song_id,
            phrase_id,
            accuracy,
            pitch_error,
            timing_error,
            1,
            mastered
        ))

    conn.commit()
    conn.close()    




def get_weakest_phrase(user_id: str, song_id: str):

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM phrase_mastery
        WHERE user_id=? AND song_id=? AND mastered=0
        ORDER BY avg_accuracy ASC
        LIMIT 1
    """, (user_id, song_id))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "phrase_id": row["phrase_id"],
            "avg_accuracy": row["avg_accuracy"],
            "attempts": row["total_attempts"]
        }

    return None    






def is_song_mastered(user_id: str, song_id: str, total_phrases: int):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM phrase_mastery
        WHERE user_id=? AND song_id=? AND mastered=1
    """, (user_id, song_id))

    mastered_count = cursor.fetchone()[0]
    conn.close()

    return mastered_count >= total_phrases