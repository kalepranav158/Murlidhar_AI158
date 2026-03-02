import sqlite3
import json
from datetime import datetime
import os
import tempfile
from datetime import timedelta

VOLATILITY_THRESHOLD = 8
PHRASE_THRESHOLD = 90  # More realistic than 95



DB_NAME = "Practice_data.db"
_TEST_DB_FILE = None


def init_db(db_name: str = None):
    global DB_NAME, _TEST_DB_FILE

    if db_name:
        if db_name == ":memory:":
            DB_NAME = "Practice_data.db"
        else:
            DB_NAME = db_name

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()



    cursor.execute("""
CREATE TABLE IF NOT EXISTS analytics_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    skill_id TEXT,
    session_id INTEGER,
    timestamp TEXT,
    accuracy_score REAL,
    timing_score REAL,
    technique_score REAL,
    composite_score REAL,
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
    skill_id TEXT,
    content_id TEXT,
    successful_sessions INTEGER DEFAULT 0,
    last_success_at TEXT,
    composite_average REAL DEFAULT 0.0,
    is_unlocked INTEGER DEFAULT 0,
    unlocked_at TEXT,
    PRIMARY KEY (user_id, skill_id)
    )
""")



    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS session_hash_registry (
    session_hash TEXT PRIMARY KEY,
    user_id TEXT,
    skill_id TEXT,
    session_id INTEGER,
    created_at TEXT
)"""
                    )

    cursor.execute("""
CREATE TABLE IF NOT EXISTS user_profile (
    user_id TEXT PRIMARY KEY,
    timezone_offset_minutes INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

    cursor.execute("""
CREATE TABLE IF NOT EXISTS practice_streak (
    user_id TEXT PRIMARY KEY,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_practice_date TEXT
)
""")

    # Backward-compatible schema upgrades for existing DBs
    cursor.execute("PRAGMA table_info(analytics_snapshots)")
    analytics_cols = {r[1] for r in cursor.fetchall()}
    for col_def in [
        "skill_id TEXT",
        "session_id INTEGER",
        "accuracy_score REAL",
        "timing_score REAL",
        "technique_score REAL",
        "composite_score REAL",
    ]:
        col_name = col_def.split()[0]
        if col_name not in analytics_cols:
            cursor.execute(f"ALTER TABLE analytics_snapshots ADD COLUMN {col_def}")

    cursor.execute("PRAGMA table_info(skill_progress)")
    skill_cols = {r[1] for r in cursor.fetchall()}
    for col_def in [
        "skill_id TEXT",
        "content_id TEXT",
        "last_success_at TEXT",
        "composite_average REAL DEFAULT 0.0",
        "successful_sessions INTEGER DEFAULT 0",
        "is_unlocked INTEGER DEFAULT 0",
        "unlocked_at TEXT",
    ]:
        col_name = col_def.split()[0]
        if col_name not in skill_cols:
            cursor.execute(f"ALTER TABLE skill_progress ADD COLUMN {col_def}")

    cursor.execute("PRAGMA table_info(session_hash_registry)")
    hash_cols = {r[1] for r in cursor.fetchall()}
    for col_def in ["skill_id TEXT", "session_id INTEGER"]:
        col_name = col_def.split()[0]
        if col_name not in hash_cols:
            cursor.execute(f"ALTER TABLE session_hash_registry ADD COLUMN {col_def}")










    conn.commit()
    conn.close()















import hashlib

def _table_columns(cursor, table_name: str) -> set[str]:
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def compute_session_hash(user_id, reference, played, skill_id: str | None = None):
    if skill_id is None and isinstance(reference, str) and isinstance(played, str):
        payload = f"{user_id}|{reference}|{played}"
        return hashlib.sha256(payload.encode()).hexdigest()

    payload = (
        user_id +
        (skill_id or "") +
        json.dumps(reference, sort_keys=True) +
        json.dumps(played, sort_keys=True)
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def session_hash_exists(session_hash: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM session_hash_registry WHERE session_hash = ? LIMIT 1",
        (session_hash,)
    )
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def register_session_hash(
    session_hash: str,
    user_id: str,
    skill_id: str = None,
    session_id: int = None,
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO session_hash_registry (
            session_hash, user_id, skill_id, session_id, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (session_hash, user_id, skill_id, session_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def update_skill_progress(
    user_id: str,
    skill_id: str,
    composite_score: float,
    session_hash: str = None,
    threshold: float = 0.75,
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("BEGIN IMMEDIATE")

    cursor.execute(
        """
        SELECT successful_sessions, last_success_at, composite_average, is_unlocked, unlocked_at
        FROM skill_progress
        WHERE user_id = ? AND skill_id = ?
        """,
        (user_id, skill_id),
    )
    row = cursor.fetchone()

    successful_sessions = row[0] if row else 0
    last_success_at = row[1] if row else None
    composite_average = row[2] if row and row[2] is not None else 0.0
    is_unlocked = bool(row[3]) if row else False
    unlocked_at = row[4] if row else None

    if session_hash and session_hash_exists(session_hash):
        conn.rollback()
        conn.close()
        return {
            "updated": False,
            "duplicate": True,
            "unlocked_now": False,
            "successful_sessions": successful_sessions,
            "is_unlocked": is_unlocked,
            "message": "Session already processed",
        }

    updated = False
    unlocked_now = False
    if composite_score >= threshold:
        updated = True
        previous_count = successful_sessions
        successful_sessions += 1
        last_success_at = datetime.now().isoformat()
        if previous_count == 0:
            composite_average = composite_score
        else:
            composite_average = ((composite_average * previous_count) + composite_score) / successful_sessions

        if not is_unlocked and successful_sessions >= 3:
            is_unlocked = True
            unlocked_now = True
            unlocked_at = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO skill_progress (
            user_id, skill_id, content_id, successful_sessions,
            last_success_at, composite_average, is_unlocked, unlocked_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, skill_id) DO UPDATE SET
            successful_sessions=excluded.successful_sessions,
            last_success_at=excluded.last_success_at,
            composite_average=excluded.composite_average,
            is_unlocked=excluded.is_unlocked,
            unlocked_at=excluded.unlocked_at,
            content_id=excluded.content_id
        """,
        (
            user_id,
            skill_id,
            skill_id,
            successful_sessions,
            last_success_at,
            composite_average,
            1 if is_unlocked else 0,
            unlocked_at,
        )
    )

    if session_hash:
        cursor.execute(
            """
            INSERT OR IGNORE INTO session_hash_registry (
                session_hash, user_id, skill_id, created_at
            ) VALUES (?, ?, ?, ?)
            """,
            (session_hash, user_id, skill_id, datetime.now().isoformat())
        )

    conn.commit()
    conn.close()

    message = "Unlocked" if unlocked_now else ("Updated" if updated else "Below threshold")
    return {
        "updated": updated,
        "duplicate": False,
        "unlocked_now": unlocked_now,
        "successful_sessions": successful_sessions,
        "is_unlocked": is_unlocked,
        "message": message,
    }


def set_user_timezone(user_id: str, timezone_offset_minutes: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO user_profile (user_id, timezone_offset_minutes, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            timezone_offset_minutes=excluded.timezone_offset_minutes,
            updated_at=excluded.updated_at
        """,
        (user_id, timezone_offset_minutes, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_user_timezone(user_id: str) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT timezone_offset_minutes FROM user_profile WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return int(row[0]) if row else 0


def get_logical_date(user_id: str, utc_timestamp: datetime) -> str:
    offset_minutes = get_user_timezone(user_id)
    local_dt = utc_timestamp + timedelta(minutes=offset_minutes)
    # Treat early-hours practice as previous logical day (practice-day boundary).
    if local_dt.hour < 3:
        local_dt = local_dt - timedelta(days=1)
    return local_dt.date().isoformat()


def get_practice_streak(user_id: str) -> dict:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM practice_streak WHERE user_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {
            "user_id": user_id,
            "current_streak": 0,
            "longest_streak": 0,
            "last_practice_date": None,
        }
    return dict(row)


def update_practice_streak(user_id: str, current_date: datetime = None) -> dict:
    now_utc = current_date or datetime.utcnow()
    today = get_logical_date(user_id, now_utc)

    current = get_practice_streak(user_id)
    last_practice_date = current["last_practice_date"]
    current_streak = int(current["current_streak"])
    longest_streak = int(current["longest_streak"])

    if not last_practice_date:
        new_streak = 1
    else:
        last_day = datetime.fromisoformat(last_practice_date).date()
        today_day = datetime.fromisoformat(today).date()
        delta_days = (today_day - last_day).days

        if delta_days == 0:
            new_streak = current_streak
        elif delta_days == 1:
            new_streak = current_streak + 1
        else:
            new_streak = 1

    new_longest = max(longest_streak, new_streak)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO practice_streak (user_id, current_streak, longest_streak, last_practice_date)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            current_streak=excluded.current_streak,
            longest_streak=excluded.longest_streak,
            last_practice_date=excluded.last_practice_date
        """,
        (user_id, new_streak, new_longest, today)
    )
    conn.commit()
    conn.close()

    return {
        "user_id": user_id,
        "current_streak": new_streak,
        "longest_streak": new_longest,
        "last_practice_date": today,
    }


def verify_unlock_integrity(user_id: str, skill_id: str) -> dict:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT successful_sessions, is_unlocked, unlocked_at
        FROM skill_progress
        WHERE user_id = ? AND skill_id = ?
        """,
        (user_id, skill_id)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {
            "is_unlocked": False,
            "unlocked_at": None,
            "valid": True,
            "issues": [],
        }

    successful_sessions, is_unlocked_raw, unlocked_at = row
    is_unlocked = bool(is_unlocked_raw)
    issues = []

    if is_unlocked and unlocked_at is None:
        issues.append("VIOLATION: Unlocked but no timestamp")
    if (not is_unlocked) and unlocked_at is not None:
        issues.append("VIOLATION: Locked but has unlock timestamp")
    if is_unlocked and successful_sessions < 3:
        issues.append("ANOMALY: Unlocked with insufficient successful sessions")

    return {
        "is_unlocked": is_unlocked,
        "unlocked_at": unlocked_at,
        "valid": len(issues) == 0,
        "issues": issues,
    }


def prune_analytics_window(user_id: str, skill_id: str, max_window: int = 30):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM analytics_snapshots
        WHERE id NOT IN (
            SELECT id
            FROM analytics_snapshots
            WHERE user_id = ? AND skill_id = ?
            ORDER BY id DESC
            LIMIT ?
        )
        AND user_id = ? AND skill_id = ?
        """,
        (user_id, skill_id, max_window, user_id, skill_id)
    )
    conn.commit()
    conn.close()

def save_session(user_id, reference, played, result, skill_id: str | None = None, testng=False):
    if not testng:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # 🔒 BEGIN IMMEDIATE TRANSACTION
        cursor.execute("BEGIN IMMEDIATE")

        # 1️⃣ Compute deterministic session hash
        session_hash = compute_session_hash(
            user_id,
            {
                "reference": reference,
                "played": played,
                "result": {
                    "note_accuracy": result.get("note_accuracy"),
                    "avg_pitch_error_cents": result.get("avg_pitch_error_cents"),
                    "avg_timing_error_sec": result.get("avg_timing_error_sec"),
                    "composite_score": result.get("composite_score"),
                    "technique_score": result.get("technique_score"),
                },
            },
            skill_id or "",
        )

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
    composite_score: float | None = None,
    threshold: float = 0.75,
    analytics: dict | None = None
):
    legacy_mode = analytics is None and composite_score is not None
    if analytics is None and composite_score is not None:
        analytics = {
            "indices": {"composite_score": composite_score},
            "volatility": 0.0,
        }
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
    effective_threshold = 0.90 if legacy_mode else threshold
    if composite_score >= effective_threshold and volatility < VOLATILITY_THRESHOLD:
        success = True

    if row:
        row_id, highest_level, best_tempo, prev_avg, prev_attempts, prev_mastered, prev_success = row

        new_attempts = prev_attempts + 1
        new_avg = ((prev_avg * prev_attempts) + composite_score) / new_attempts
        highest_level = max(highest_level, level_index)
        best_tempo = max(best_tempo, tempo)

        if success:
            if legacy_mode:
                prev_success = max(prev_success, 3)
            else:
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
        success_count = 3 if (success and legacy_mode) else (1 if success else 0)
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






