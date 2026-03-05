import sqlite3
import json
from datetime import datetime, timezone
import os
import tempfile
from pathlib import Path
from datetime import timedelta
from typing import Optional

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_NAME = str(_PROJECT_ROOT / "Practice_data.db")
_TEST_DB_FILE = None


def _archive_legacy_mastery_structures(cursor):
    cursor.execute(
        """
        SELECT type, name
        FROM sqlite_master
        WHERE name IN (
            'alankar_mastery',
            'phrase_mastery',
            '_legacy_alankar_mastery',
            '_legacy_phrase_mastery'
        )
        """
    )
    objects = {(row[0], row[1]) for row in cursor.fetchall()}

    if ("table", "alankar_mastery") in objects and ("table", "_legacy_alankar_mastery") not in objects:
        cursor.execute("ALTER TABLE alankar_mastery RENAME TO _legacy_alankar_mastery")

    if ("table", "phrase_mastery") in objects and ("table", "_legacy_phrase_mastery") not in objects:
        cursor.execute("ALTER TABLE phrase_mastery RENAME TO _legacy_phrase_mastery")

    cursor.execute("DROP VIEW IF EXISTS alankar_mastery")
    cursor.execute("DROP VIEW IF EXISTS phrase_mastery")

    cursor.execute(
        """
        CREATE VIEW IF NOT EXISTS alankar_mastery AS
        SELECT
            NULL AS id,
            user_id,
            skill_id AS alankar_id,
            NULL AS highest_level,
            NULL AS best_tempo,
            composite_average AS average_score,
            total_sessions AS total_attempts,
            is_unlocked AS mastered,
            successful_sessions
        FROM skill_progress
        WHERE skill_type = 'alankar'
        """
    )

    cursor.execute(
        """
        CREATE VIEW IF NOT EXISTS phrase_mastery AS
        SELECT
            NULL AS id,
            user_id,
            CASE
                WHEN INSTR(skill_id, ':phrase:') > 0 THEN SUBSTR(skill_id, 1, INSTR(skill_id, ':phrase:') - 1)
                ELSE skill_id
            END AS song_id,
            CASE
                WHEN INSTR(skill_id, ':phrase:') > 0 THEN CAST(SUBSTR(skill_id, INSTR(skill_id, ':phrase:') + 8) AS INTEGER)
                ELSE NULL
            END AS phrase_id,
            composite_average * 100.0 AS avg_accuracy,
            NULL AS avg_pitch_error,
            NULL AS avg_timing_error,
            total_sessions AS total_attempts,
            is_unlocked AS mastered,
            successful_sessions
        FROM skill_progress
        WHERE skill_type = 'phrase'
        """
    )


def init_db(db_name: Optional[str] = None):
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
    skill_type TEXT NOT NULL DEFAULT 'alankar',
    successful_sessions INTEGER DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    last_success_at TEXT,
    composite_average REAL DEFAULT 0.0,
    recent_weighted_average REAL DEFAULT 0.0,
    last_composite_score REAL,
    last_session_at TEXT,
    is_unlocked INTEGER DEFAULT 0,
    unlocked_at TEXT,
    PRIMARY KEY (user_id, skill_id),
    CHECK (NOT (is_unlocked = 1 AND unlocked_at IS NULL)),
    CHECK (NOT (is_unlocked = 0 AND unlocked_at IS NOT NULL))
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
    last_practice_logical_date TEXT,
    total_practice_days INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

    cursor.execute("""
CREATE TABLE IF NOT EXISTS practice_days (
    user_id TEXT,
    logical_date TEXT,
    PRIMARY KEY (user_id, logical_date)
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
        "skill_type TEXT NOT NULL DEFAULT 'alankar'",
        "total_sessions INTEGER DEFAULT 0",
        "last_success_at TEXT",
        "composite_average REAL DEFAULT 0.0",
        "recent_weighted_average REAL DEFAULT 0.0",
        "last_composite_score REAL",
        "last_session_at TEXT",
        "successful_sessions INTEGER DEFAULT 0",
        "is_unlocked INTEGER DEFAULT 0",
        "unlocked_at TEXT",
    ]:
        col_name = col_def.split()[0]
        if col_name not in skill_cols:
            cursor.execute(f"ALTER TABLE skill_progress ADD COLUMN {col_def}")

    cursor.execute(
        "UPDATE skill_progress SET skill_type='alankar' WHERE skill_type IS NULL OR TRIM(skill_type) = ''"
    )

    cursor.execute(
        "UPDATE skill_progress SET total_sessions=successful_sessions WHERE total_sessions IS NULL OR total_sessions < successful_sessions"
    )

    cursor.execute(
        "UPDATE skill_progress SET recent_weighted_average=composite_average WHERE recent_weighted_average IS NULL"
    )

    _archive_legacy_mastery_structures(cursor)

    cursor.execute("PRAGMA table_info(session_hash_registry)")
    hash_cols = {r[1] for r in cursor.fetchall()}
    for col_def in ["skill_id TEXT", "session_id INTEGER"]:
        col_name = col_def.split()[0]
        if col_name not in hash_cols:
            cursor.execute(f"ALTER TABLE session_hash_registry ADD COLUMN {col_def}")

    cursor.execute("PRAGMA table_info(practice_streak)")
    streak_cols = {r[1] for r in cursor.fetchall()}
    for col_def in [
        "last_practice_logical_date TEXT",
        "total_practice_days INTEGER DEFAULT 0",
        "updated_at TEXT DEFAULT CURRENT_TIMESTAMP",
    ]:
        col_name = col_def.split()[0]
        if col_name not in streak_cols:
            cursor.execute(f"ALTER TABLE practice_streak ADD COLUMN {col_def}")

    if "last_practice_date" in streak_cols and "last_practice_logical_date" in streak_cols:
        cursor.execute(
            """
            UPDATE practice_streak
            SET last_practice_logical_date = COALESCE(last_practice_logical_date, last_practice_date)
            """
        )

    cursor.execute(
        """
        UPDATE practice_streak
        SET updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)
        """
    )

    cursor.execute(
        """
        UPDATE practice_streak
        SET total_practice_days = CASE
            WHEN total_practice_days IS NULL OR total_practice_days = 0 THEN
                CASE WHEN current_streak > 0 THEN current_streak ELSE 0 END
            ELSE total_practice_days
        END
        """
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO skill_progress (
            user_id, skill_id, skill_type, successful_sessions, total_sessions,
            composite_average, recent_weighted_average, is_unlocked, unlocked_at,
            last_success_at, last_session_at
        )
        SELECT
            user_id,
            alankar_id,
            'alankar',
            COALESCE(successful_sessions, 0),
            COALESCE(total_attempts, 0),
            COALESCE(average_score, 0.0),
            COALESCE(average_score, 0.0),
            CASE WHEN COALESCE(mastered, 0) = 1 THEN 1 ELSE 0 END,
            CASE WHEN COALESCE(mastered, 0) = 1 THEN CURRENT_TIMESTAMP ELSE NULL END,
            NULL,
            NULL
        FROM alankar_mastery
        """
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO skill_progress (
            user_id, skill_id, skill_type, successful_sessions, total_sessions,
            composite_average, recent_weighted_average, is_unlocked, unlocked_at,
            last_success_at, last_session_at
        )
        SELECT
            user_id,
            song_id || ':phrase:' || phrase_id,
            'phrase',
            COALESCE(successful_sessions, 0),
            COALESCE(total_attempts, 0),
            COALESCE(avg_accuracy, 0.0) / 100.0,
            COALESCE(avg_accuracy, 0.0) / 100.0,
            CASE WHEN COALESCE(mastered, 0) = 1 THEN 1 ELSE 0 END,
            CASE WHEN COALESCE(mastered, 0) = 1 THEN CURRENT_TIMESTAMP ELSE NULL END,
            NULL,
            NULL
        FROM phrase_mastery
        """
    )










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
    skill_id: Optional[str] = None,
    session_id: Optional[int] = None,
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
    skill_type: str,
    composite_score: float,
    threshold: float,
    session_hash: Optional[str] = None,
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("BEGIN IMMEDIATE")

    now_iso = datetime.now(timezone.utc).isoformat()

    if session_hash:
        cursor.execute(
            "SELECT 1 FROM session_hash_registry WHERE session_hash = ? LIMIT 1",
            (session_hash,),
        )
        if cursor.fetchone():
            cursor.execute(
                """
                SELECT successful_sessions, total_sessions, is_unlocked
                FROM skill_progress
                WHERE user_id = ? AND skill_id = ?
                """,
                (user_id, skill_id),
            )
            existing = cursor.fetchone()
            conn.rollback()
            conn.close()
            return {
                "updated": False,
                "duplicate": True,
                "unlocked_now": False,
                "successful_sessions": existing[0] if existing else 0,
                "total_sessions": existing[1] if existing else 0,
                "is_unlocked": bool(existing[2]) if existing else False,
                "message": "Session already processed",
            }

    cursor.execute(
        """
        SELECT successful_sessions, total_sessions, last_success_at,
               composite_average, recent_weighted_average,
               is_unlocked, unlocked_at
        FROM skill_progress
        WHERE user_id = ? AND skill_id = ?
        """,
        (user_id, skill_id),
    )
    row = cursor.fetchone()

    successful_sessions = row[0] if row else 0
    total_sessions = row[1] if row else 0
    last_success_at = row[2] if row else None
    composite_average = row[3] if row and row[3] is not None else 0.0
    recent_weighted_average = row[4] if row and row[4] is not None else 0.0
    is_unlocked = bool(row[5]) if row else False
    unlocked_at = row[6] if row else None

    total_sessions += 1
    if total_sessions == 1:
        composite_average = composite_score
        recent_weighted_average = composite_score
    else:
        previous_total = total_sessions - 1
        composite_average = ((composite_average * previous_total) + composite_score) / total_sessions
        recent_weighted_average = (recent_weighted_average * 0.7) + (composite_score * 0.3)

    updated = False
    unlocked_now = False
    if composite_score >= threshold:
        updated = True
        successful_sessions += 1
        last_success_at = now_iso

        if not is_unlocked and successful_sessions >= 3:
            is_unlocked = True
            unlocked_now = True
            unlocked_at = now_iso

    cursor.execute(
        """
        INSERT INTO skill_progress (
            user_id, skill_id, skill_type, successful_sessions,
            total_sessions, composite_average, recent_weighted_average,
            last_composite_score, last_session_at, last_success_at,
            is_unlocked, unlocked_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, skill_id) DO UPDATE SET
            skill_type=excluded.skill_type,
            successful_sessions=excluded.successful_sessions,
            total_sessions=excluded.total_sessions,
            last_success_at=excluded.last_success_at,
            composite_average=excluded.composite_average,
            recent_weighted_average=excluded.recent_weighted_average,
            last_composite_score=excluded.last_composite_score,
            last_session_at=excluded.last_session_at,
            is_unlocked=excluded.is_unlocked,
            unlocked_at=excluded.unlocked_at
        """,
        (
            user_id,
            skill_id,
            skill_type,
            successful_sessions,
            total_sessions,
            composite_average,
            recent_weighted_average,
            composite_score,
            now_iso,
            last_success_at,
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
            (session_hash, user_id, skill_id, now_iso)
        )

    conn.commit()
    conn.close()

    message = "Unlocked" if unlocked_now else ("Updated" if updated else "Below threshold")
    return {
        "updated": updated,
        "duplicate": False,
        "unlocked_now": unlocked_now,
        "successful_sessions": successful_sessions,
        "total_sessions": total_sessions,
        "composite_average": composite_average,
        "recent_weighted_average": recent_weighted_average,
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
            "last_practice_logical_date": None,
            "last_practice_date": None,
            "total_practice_days": 0,
        }
    payload = dict(row)
    payload["last_practice_date"] = payload.get("last_practice_logical_date")
    payload["total_practice_days"] = int(payload.get("total_practice_days") or 0)
    return payload


def update_practice_streak(user_id: str, current_date: Optional[datetime] = None) -> dict:
    now_utc = current_date or datetime.now(timezone.utc)
    logical_date = get_logical_date(user_id, now_utc)

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("BEGIN IMMEDIATE")

    cursor.execute(
        """
        INSERT OR IGNORE INTO practice_days (user_id, logical_date)
        VALUES (?, ?)
        """,
        (user_id, logical_date),
    )
    is_new_practice_day = cursor.rowcount > 0

    cursor.execute(
        """
        SELECT current_streak, longest_streak, last_practice_logical_date, total_practice_days
        FROM practice_streak
        WHERE user_id = ?
        """,
        (user_id,),
    )
    row = cursor.fetchone()

    current_streak = int(row["current_streak"]) if row else 0
    longest_streak = int(row["longest_streak"]) if row else 0
    last_practice_logical_date = row["last_practice_logical_date"] if row else None
    total_practice_days = int(row["total_practice_days"]) if row else 0

    if not last_practice_logical_date:
        new_streak = 1
    else:
        delta_days = (
            datetime.fromisoformat(logical_date).date() -
            datetime.fromisoformat(last_practice_logical_date).date()
        ).days
        if delta_days <= 0:
            new_streak = current_streak
        elif delta_days == 1:
            new_streak = current_streak + 1
        else:
            new_streak = 1

    if not is_new_practice_day and last_practice_logical_date:
        new_streak = current_streak
        effective_last_date = last_practice_logical_date
    else:
        effective_last_date = logical_date

    new_total_days = total_practice_days + (1 if is_new_practice_day else 0)
    new_longest = max(longest_streak, new_streak)
    updated_at = datetime.now(timezone.utc).isoformat()

    cursor.execute(
        """
        INSERT INTO practice_streak (
            user_id, current_streak, longest_streak,
            last_practice_logical_date, total_practice_days, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            current_streak=excluded.current_streak,
            longest_streak=excluded.longest_streak,
            last_practice_logical_date=excluded.last_practice_logical_date,
            total_practice_days=excluded.total_practice_days,
            updated_at=excluded.updated_at
        """,
        (
            user_id,
            new_streak,
            new_longest,
            effective_last_date,
            new_total_days,
            updated_at,
        )
    )
    conn.commit()
    conn.close()

    return {
        "user_id": user_id,
        "current_streak": new_streak,
        "longest_streak": new_longest,
        "total_practice_days": new_total_days,
        "last_practice_logical_date": effective_last_date,
        "last_practice_date": effective_last_date,
        "logical_date": logical_date,
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
        """
        SELECT is_unlocked
        FROM skill_progress
        WHERE user_id=? AND skill_id=? AND skill_type='alankar'
        """,
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
        """
        SELECT COUNT(*)
        FROM skill_progress
        WHERE user_id=? AND skill_type='alankar' AND is_unlocked=1
        """,
        (user_id,)
    )
    cnt = cursor.fetchone()[0]
    conn.close()
    return cnt


def count_mastered_songs(user_id: str) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT skill_id
        FROM skill_progress
        WHERE user_id=? AND skill_type='phrase' AND is_unlocked=1
        """,
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    from music.song_loader import load_song
    mastered_by_song: dict[str, int] = {}
    for (phrase_skill_id,) in rows:
        if not isinstance(phrase_skill_id, str) or ":phrase:" not in phrase_skill_id:
            continue
        song_id, _ = phrase_skill_id.split(":phrase:", 1)
        mastered_by_song[song_id] = mastered_by_song.get(song_id, 0) + 1

    total = 0
    for song_id, mastered_phrases in mastered_by_song.items():
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






def get_weakest_phrase(user_id: str, song_id: str):

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT skill_id, composite_average, total_sessions
        FROM skill_progress
        WHERE user_id=?
          AND skill_type='phrase'
          AND skill_id LIKE ?
          AND is_unlocked=0
        ORDER BY composite_average ASC
        LIMIT 1
    """, (user_id, f"{song_id}:phrase:%"))

    row = cursor.fetchone()
    conn.close()

    if row:
        skill_id = row["skill_id"]
        phrase_id = int(skill_id.rsplit(":phrase:", 1)[1])
        return {
            "phrase_id": phrase_id,
            "avg_accuracy": (row["composite_average"] or 0.0) * 100.0,
            "attempts": row["total_sessions"]
        }

    return None    






def is_song_mastered(user_id: str, song_id: str, total_phrases: int):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM skill_progress
        WHERE user_id=?
          AND skill_type='phrase'
          AND skill_id LIKE ?
          AND is_unlocked=1
    """, (user_id, f"{song_id}:phrase:%"))

    mastered_count = cursor.fetchone()[0]
    conn.close()

    return mastered_count >= total_phrases


def is_melody_mastered(user_id: str, melody_id: str, total_phrases: int):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM skill_progress
        WHERE user_id=?
          AND skill_type='melody_phrase'
          AND skill_id LIKE ?
          AND is_unlocked=1
    """,
        (user_id, f"{melody_id}:melody_phrase:%"),
    )

    mastered_count = cursor.fetchone()[0]
    conn.close()

    return mastered_count >= total_phrases






