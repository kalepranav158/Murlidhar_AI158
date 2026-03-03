# ============================================================
# 🔍 DEBUG ENDPOINTS - CURRENT DATABASE VERSION
# ============================================================

from fastapi import APIRouter
import sqlite3
from datetime import datetime
import database.db as db
from app.routes.response_envelope import no_data_response

router = APIRouter(prefix="/debug", tags=["Debug"])


# ============================================================
# 📝 RECENT SESSIONS
# ============================================================

@router.get("/sessions/{user_id}")
async def debug_sessions(user_id: str, limit: int = 10):

    conn = sqlite3.connect(db.DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, timestamp, note_accuracy,
               avg_pitch_error, avg_timing_error,
               composite_score, technique_score
        FROM sessions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (user_id, limit))

    rows = cursor.fetchall()
    conn.close()

    return {
        "user_id": user_id,
        "total_returned": len(rows),
        "sessions": [dict(row) for row in rows],
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================
# 🎼 ALANKAR MASTERY STATE
# ============================================================

@router.get("/alankar/{user_id}/{alankar_id}")
async def debug_alankar_mastery(user_id: str, alankar_id: str):

    conn = sqlite3.connect(db.DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM skill_progress
        WHERE user_id = ? AND skill_id = ? AND skill_type = 'alankar'
    """, (user_id, alankar_id))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return no_data_response("No skill_progress record found")

    return dict(row)


# ============================================================
# 🎵 PHRASE MASTERY STATE
# ============================================================

@router.get("/phrase/{user_id}/{song_id}/{phrase_id}")
async def debug_phrase_mastery(user_id: str, song_id: str, phrase_id: int):

    conn = sqlite3.connect(db.DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM skill_progress
        WHERE user_id = ? AND skill_id = ? AND skill_type = 'phrase'
    """, (user_id, f"{song_id}:phrase:{phrase_id}"))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return no_data_response("No phrase skill_progress record found")

    return dict(row)


# ============================================================
# 📊 ANALYTICS SNAPSHOT WINDOW
# ============================================================

@router.get("/analytics/{user_id}")
async def debug_analytics_snapshots(user_id: str, limit: int = 30):

    conn = sqlite3.connect(db.DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM analytics_snapshots
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (user_id, limit))

    rows = cursor.fetchall()

    cursor.execute("""
        SELECT COUNT(*)
        FROM analytics_snapshots
        WHERE user_id = ?
    """, (user_id,))
    total = cursor.fetchone()[0]

    conn.close()

    return {
        "user_id": user_id,
        "total_snapshots": total,
        "window_returned": len(rows),
        "window_max": 30,
        "snapshots": [dict(row) for row in rows],
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================
# 🎓 STUDENT PROGRESS STATE
# ============================================================

@router.get("/student/{user_id}")
async def debug_student_progress(user_id: str):

    conn = sqlite3.connect(db.DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM student_progress
        WHERE user_id = ?
    """, (user_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return no_data_response("No student progress record found")

    return dict(row)