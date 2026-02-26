import sqlite3
import json
from datetime import datetime

DB_NAME = "Practice_data.db"


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
    mistakes TEXT,
    composite_score REAL,
    pitch_index REAL,
    rhythm_index REAL,
    consistency_index REAL,
    technique_score REAL
)
""")
    # ensure table upgrade: add new column if missing from older databases
    cursor.execute("PRAGMA table_info(sessions)")
    cols = [r[1] for r in cursor.fetchall()]
    if "technique_score" not in cols:
        cursor.execute("ALTER TABLE sessions ADD COLUMN technique_score REAL")



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

    cursor.execute("""
CREATE TABLE IF NOT EXISTS student_progress (
    user_id TEXT PRIMARY KEY,
    current_level TEXT,
    unlocked_content TEXT,
    mastered_content TEXT,
    last_evaluated TEXT
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
        consistency_index,
        technique_score
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    result.get("technique_score"),
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
    "consistency_index": row["consistency_index"],
    "technique_score": row.get("technique_score") if isinstance(row, dict) else row["technique_score"]
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


# ---------------------------
# Student progress / curriculum helpers
# ---------------------------

def get_student_progress(user_id: str):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM student_progress WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "user_id": row["user_id"],
        "current_level": row["current_level"],
        "unlocked_content": json.loads(row["unlocked_content"] or "[]"),
        "mastered_content": json.loads(row["mastered_content"] or "[]"),
        "last_evaluated": row["last_evaluated"]
    }


def update_student_progress(user_id: str, profile: dict):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    unlocked_json = json.dumps(profile.get("unlocked_content", []))
    mastered_json = json.dumps(profile.get("mastered_content", []))
    level = profile.get("current_level")
    last = profile.get("last_evaluated")

    cursor.execute(
        "SELECT user_id FROM student_progress WHERE user_id = ?",
        (user_id,)
    )
    if cursor.fetchone():
        cursor.execute(
            """
            UPDATE student_progress
            SET current_level=?, unlocked_content=?, mastered_content=?, last_evaluated=?
            WHERE user_id=?
            """,
            (level, unlocked_json, mastered_json, last, user_id)
        )
    else:
        cursor.execute(
            """
            INSERT INTO student_progress (
                user_id, current_level, unlocked_content, mastered_content, last_evaluated
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, level, unlocked_json, mastered_json, last)
        )

    conn.commit()
    conn.close()


def is_alankar_mastered(user_id: str, alankar_id: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT mastered FROM alankar_mastery WHERE user_id=? AND alankar_id=?",
        (user_id, alankar_id)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return bool(row[0])
    return False


def count_mastered_alankars(user_id: str) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM alankar_mastery WHERE user_id=? AND mastered=1",
        (user_id,)
    )
    cnt = cursor.fetchone()[0]
    conn.close()
    return cnt


def count_mastered_songs(user_id: str) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT song_id, COUNT(*) as mastered_phrases FROM phrase_mastery WHERE user_id=? AND mastered=1 GROUP BY song_id",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    from music.song_loader import load_song
    total = 0
    for song_id, mastered_phrases in rows:
        try:
            song = load_song(f"songs/{song_id}.json")
            if len(song.get("phrases", [])) == mastered_phrases:
                total += 1
        except Exception:
            continue
    return total

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