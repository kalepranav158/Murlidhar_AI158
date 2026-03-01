import sqlite3
import json
from datetime import datetime

VOLATILITY_THRESHOLD = 8
PHRASE_THRESHOLD = 90  # More realistic than 95



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
    mastered INTEGER,
    successful_sessions INTEGER DEFAULT 0
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
    mastered INTEGER,
    successful_sessions INTEGER DEFAULT 0
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


    # added student_progress table for tracking curriculum progress and unlocked content
    cursor.execute("""
CREATE TABLE IF NOT EXISTS skill_progress (
    user_id TEXT,
    content_id TEXT,
    successful_sessions INTEGER,
    is_unlocked INTEGER,
    unlocked_at TEXT,
    PRIMARY KEY (user_id, content_id)
    )
""")



    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS session_hash_registry (
    session_hash TEXT PRIMARY KEY,
    user_id TEXT,
    created_at TEXT
)"""
                    )










    conn.commit()
    conn.close()















import hashlib

def _table_columns(cursor, table_name: str) -> set[str]:
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def compute_session_hash(user_id, reference, played, skill_id: str | None = None):
    payload = (
        user_id +
        (skill_id or "") +
        json.dumps(reference, sort_keys=True) +
        json.dumps(played, sort_keys=True)
    )
    return hashlib.sha256(payload.encode()).hexdigest()

def save_session(user_id, reference, played, result, skill_id: str | None = None, testng=False):
    if not testng:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # 🔒 BEGIN IMMEDIATE TRANSACTION
        cursor.execute("BEGIN IMMEDIATE")

        # 1️⃣ Compute deterministic session hash
        session_hash = compute_session_hash(user_id, reference, played)

        # 2️⃣ Check duplicate
        cursor.execute("""
            SELECT session_hash FROM session_hash_registry
            WHERE session_hash = ?
        """, (session_hash,))

        if cursor.fetchone():
            # Duplicate detected → do nothing
            conn.rollback()
            conn.close()
            return {"status": "duplicate_rejected"}

        # 3️⃣ Register hash
        cursor.execute("""
            INSERT INTO session_hash_registry (session_hash, user_id, created_at)
            VALUES (?, ?, ?)
        """, (
            session_hash,
            user_id,
            datetime.now().isoformat()
        ))

        # 4️⃣ Insert session safely
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

        return {"status": "saved"}

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

#---------------------------------------------------------------------------------------------------------------------
# Analytics computations and snapshot management
#-----------------------------------------------------------------------------------------------------------------
    
MAX_ANALYTICS_WINDOW= 30
VOLATILITY_WINDOW=  5

def compute_weighted_average(scores: list[float]) -> float:
    if not scores:
        return 0.0

    weights = list(range(1, len(scores) + 1))
    weighted_sum = sum(s * w for s, w in zip(scores, weights))
    return weighted_sum / sum(weights)


import statistics

def compute_volatility(scores: list[float]) -> float:
    if len(scores) <= 1:
        return 0.0

    window = scores[-min(VOLATILITY_WINDOW, len(scores)):]
    return statistics.pstdev(window)

def save_analytics_snapshot(user_id: str, snapshot: dict):

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

    # 🔹 Rolling window pruning
    cursor.execute("""
        DELETE FROM analytics_snapshots
        WHERE id NOT IN (
            SELECT id FROM analytics_snapshots
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        )
        AND user_id = ?
    """, (user_id, MAX_ANALYTICS_WINDOW, user_id))

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






def update_alankar_mastery(
    user_id: str,
    alankar_id: str,
    level_index: int,
    tempo: int,
    threshold: float = 0.75,
    analytics: dict | None = None
):
    if analytics is None:
        return
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, highest_level, best_tempo,
               average_score, total_attempts,
               mastered, successful_sessions
        FROM alankar_mastery
        WHERE user_id = ? AND alankar_id = ?
    """, (user_id, alankar_id))

    row = cursor.fetchone()

    # 🔹 Get weighted analytics (Phase 3 integration)

   

    composite_score = analytics["indices"]["composite_score"]
    volatility = analytics["volatility"]

    success = False
    if composite_score >= threshold and volatility < VOLATILITY_THRESHOLD:
        success = True

    if row:
        row_id, highest_level, best_tempo, prev_avg, prev_attempts, prev_mastered, prev_success = row

        new_attempts = prev_attempts + 1
        new_avg = ((prev_avg * prev_attempts) + composite_score) / new_attempts
        highest_level = max(highest_level, level_index)
        best_tempo = max(best_tempo, tempo)

        if success:
            prev_success += 1

        # Forward-only unlock
        mastered = prev_mastered
        if not prev_mastered and prev_success >= 3:
            mastered = 1

        cursor.execute("""
            UPDATE alankar_mastery
            SET highest_level=?,
                best_tempo=?,
                average_score=?,
                total_attempts=?,
                mastered=?,
                successful_sessions=?
            WHERE id=?
        """, (
            highest_level,
            best_tempo,
            new_avg,
            new_attempts,
            mastered,
            prev_success,
            row_id
        ))

    else:
        success_count = 1 if success else 0
        mastered = 1 if success_count >= 3 else 0

        cursor.execute("""
            INSERT INTO alankar_mastery (
                user_id,
                alankar_id,
                highest_level,
                best_tempo,
                average_score,
                total_attempts,
                mastered,
                successful_sessions
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            alankar_id,
            level_index,
            tempo,
            composite_score,
            1,
            mastered,
            success_count
        ))

    conn.commit()
    conn.close()




def update_phrase_mastery(
    user_id: str,
    song_id: str,
    phrase_id: int,
    accuracy: float,
    pitch_error: float,
    timing_error: float,
    analytics: dict | None = None
):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, avg_accuracy, avg_pitch_error,
               avg_timing_error, total_attempts,
               mastered, successful_sessions
        FROM phrase_mastery
        WHERE user_id=? AND song_id=? AND phrase_id=?
    """, (user_id, song_id, phrase_id))

    row = cursor.fetchone()

    # Phase 3 analytics

    volatility = analytics["volatility"] if analytics else 999
    success = False
    if accuracy >= PHRASE_THRESHOLD and volatility < VOLATILITY_THRESHOLD:
        success = True

    if row:
        row_id, prev_acc, prev_pitch, prev_timing, prev_attempts, prev_mastered, prev_success = row

        new_attempts = prev_attempts + 1
        new_avg_accuracy = ((prev_acc * prev_attempts) + accuracy) / new_attempts
        new_avg_pitch = ((prev_pitch * prev_attempts) + pitch_error) / new_attempts
        new_avg_timing = ((prev_timing * prev_attempts) + timing_error) / new_attempts

        if success:
            prev_success += 1

        # Forward-only unlock
        mastered = prev_mastered
        if not prev_mastered and prev_success >= 3:
            mastered = 1

        cursor.execute("""
            UPDATE phrase_mastery
            SET avg_accuracy=?,
                avg_pitch_error=?,
                avg_timing_error=?,
                total_attempts=?,
                mastered=?,
                successful_sessions=?
            WHERE id=?
        """, (
            new_avg_accuracy,
            new_avg_pitch,
            new_avg_timing,
            new_attempts,
            mastered,
            prev_success,
            row_id
        ))

    else:
        success_count = 1 if success else 0
        mastered = 1 if success_count >= 3 else 0

        cursor.execute("""
            INSERT INTO phrase_mastery (
                user_id, song_id, phrase_id,
                avg_accuracy, avg_pitch_error,
                avg_timing_error, total_attempts,
                mastered, successful_sessions
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            song_id,
            phrase_id,
            accuracy,
            pitch_error,
            timing_error,
            1,
            mastered,
            success_count
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






