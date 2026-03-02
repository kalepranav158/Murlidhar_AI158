# ============================================================
# ✅ COMPREHENSIVE TEST SUITE - Edge Case Validation
# ============================================================

"""
Non-Regression Test Plan for:
1. Mastery Counter Persistence
2. Non-Regression Unlock Verification
3. Streak Reset Bug Fix
4. Analytics Snapshot Pruning
5. Composite Weight Configuration

Run: python -m pytest tests/test_edge_cases.py -v
"""

import pytest
import sqlite3
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from database.db import (
    init_db,
    update_skill_progress,
    compute_session_hash,
    session_hash_exists,
    register_session_hash,
    get_user_timezone,
    set_user_timezone,
    get_logical_date,
    verify_unlock_integrity,
    update_practice_streak,
    get_practice_streak,
    prune_analytics_window,
)
from app.services.analytics_config import (
    compute_composite_score,
    RollingWindowAnalytics,
    COMPOSITE_CONFIG,
    validate_composite_config,
)


# ============================================================
# 🔧 TEST FIXTURES & SETUP
# ============================================================

import database.db as db

SKILL_TYPE = "alankar"
THRESHOLD = 0.75


def _assert_not_live_db(path: str):
    live_name = "practice_data.db"
    if os.path.basename(path).lower() == live_name:
        raise RuntimeError(
            "Refusing to run tests against live Practice_data.db. "
            "Use an isolated test DB file."
        )

@pytest.fixture(autouse=True)
def setup_test_db():
    test_db = f"test_edge_cases_{uuid.uuid4().hex}.db"
    _assert_not_live_db(test_db)
    db.DB_NAME = test_db
    db.init_db(test_db)
    yield
    try:
        os.remove(test_db)
    except OSError:
        pass

def get_skill_progress(user_id: str, skill_id: str) -> dict:
    """Helper: Get current skill progress state."""
    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT successful_sessions, last_success_at, composite_average, 
                  is_unlocked, unlocked_at
           FROM skill_progress WHERE user_id = ? AND skill_id = ?""",
        (user_id, skill_id)
    )
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    return {
        "successful_sessions": row[0],
        "last_success_at": row[1],
        "composite_average": row[2],
        "is_unlocked": bool(row[3]),
        "unlocked_at": row[4],
    }


# ============================================================
# 1️⃣ TEST: UNLOCK ONLY AFTER 3 VALID SESSIONS
# ============================================================

def test_unlock_requires_three_successful_sessions():
    """
    ✅ Requirement: Only unlock after 3 consecutive successes above threshold.
    
    Scenario:
    - Session 1: score 0.8 (above threshold) → sessions = 1, not unlocked
    - Session 2: score 0.85 (above threshold) → sessions = 2, not unlocked
    - Session 3: score 0.78 (above threshold) → sessions = 3, UNLOCKED ✓
    """
    user_id = "test_user_1"
    skill_id = "skill_1"
    
    # Session 1
    result1 = update_skill_progress(user_id, skill_id, SKILL_TYPE, 0.80, THRESHOLD)
    assert result1["updated"] is True
    assert result1["unlocked_now"] is False
    assert result1["successful_sessions"] == 1
    assert result1["is_unlocked"] is False
    
    # Session 2
    result2 = update_skill_progress(user_id, skill_id, SKILL_TYPE, 0.85, THRESHOLD)
    assert result2["updated"] is True
    assert result2["unlocked_now"] is False
    assert result2["successful_sessions"] == 2
    assert result2["is_unlocked"] is False
    
    # Session 3 - TRIGGERS UNLOCK
    result3 = update_skill_progress(user_id, skill_id, SKILL_TYPE, 0.78, THRESHOLD)
    assert result3["updated"] is True
    assert result3["unlocked_now"] is True
    assert result3["successful_sessions"] == 3
    assert result3["is_unlocked"] is True
    
    # Verify database state
    progress = get_skill_progress(user_id, skill_id)
    assert progress["successful_sessions"] == 3
    assert progress["is_unlocked"] is True
    assert progress["unlocked_at"] is not None


# ============================================================
# 2️⃣ TEST: FAILED SESSION DOES NOT INCREMENT COUNTER
# ============================================================

def test_failed_session_does_not_increment_counter():
    """
    ✅ Critical: Failure (score < threshold) does NOT decrement or reset.
    
    Scenario:
    - Session 1: score 0.8 → sessions = 1
    - Session 2: score 0.5 (FAIL) → sessions = 1 (unchanged!)
    - Session 3: score 0.8 → sessions = 2
    """
    user_id = "test_user_2"
    skill_id = "skill_2"
    
    # Session 1: Success
    result1 = update_skill_progress(user_id, skill_id, SKILL_TYPE, 0.80, THRESHOLD)
    assert result1["successful_sessions"] == 1
    
    # Session 2: Failure below threshold
    result2 = update_skill_progress(user_id, skill_id, SKILL_TYPE, 0.50, THRESHOLD)
    assert result2["updated"] is False  # No update on failure
    assert result2["successful_sessions"] == 1  # Counter unchanged!
    
    # Session 3: Success
    result3 = update_skill_progress(user_id, skill_id, SKILL_TYPE, 0.80, THRESHOLD)
    assert result3["updated"] is True
    assert result3["successful_sessions"] == 2  # Incremented from 1, NOT reset
    
    # Verify counter never reset
    progress = get_skill_progress(user_id, skill_id)
    assert progress["successful_sessions"] == 2


# ============================================================
# 3️⃣ TEST: UNLOCK NEVER REVERSES
# ============================================================

def test_unlock_never_reverses():
    """
    ✅ Immutable: Once unlocked, state is permanent.
    
    Even with poor performance later, unlock status must remain true.
    """
    user_id = "test_user_3"
    skill_id = "skill_3"
    
    # Unlock the skill
    result1 = update_skill_progress(user_id, skill_id, SKILL_TYPE, 0.80, THRESHOLD)
    result2 = update_skill_progress(user_id, skill_id, SKILL_TYPE, 0.85, THRESHOLD)
    result3 = update_skill_progress(user_id, skill_id, SKILL_TYPE, 0.78, THRESHOLD)
    assert result3["is_unlocked"] is True
    
    first_unlock_time = result3["message"]
    
    # Submit many failed sessions
    for i in range(10):
        result = update_skill_progress(user_id, skill_id, SKILL_TYPE, 0.30, THRESHOLD)
        # is_unlocked should REMAIN TRUE
        assert result["is_unlocked"] is True, f"Unlock reversed on attempt {i+1}!"
    
    # Verify unlock is still true
    integrity = verify_unlock_integrity(user_id, skill_id)
    assert integrity["is_unlocked"] is True
    assert integrity["valid"] is True


# ============================================================
# 4️⃣ TEST: DUPLICATE SESSION REJECTED
# ============================================================

def test_duplicate_session_rejected():
    """
    ✅ Idempotency: Same session hash cannot be processed twice.
    
    Scenario:
    - Submit session with hash ABC → accepted
    - Submit same hash again → rejected as duplicate
    """
    user_id = "test_user_4"
    skill_id = "skill_4"
    
    # Create session hash
    session_hash = compute_session_hash(user_id, skill_id, "audio_checksum_123")
    
    # First submission
    result1 = update_skill_progress(
        user_id, skill_id, SKILL_TYPE, 0.80, THRESHOLD, session_hash=session_hash
    )
    assert result1["updated"] is True
    assert result1["duplicate"] is False
    assert result1["successful_sessions"] == 1
    
    # Second submission with SAME hash
    result2 = update_skill_progress(
        user_id, skill_id, SKILL_TYPE, 0.85, THRESHOLD, session_hash=session_hash
    )
    assert result2["updated"] is False
    assert result2["duplicate"] is True
    assert result2["successful_sessions"] == 1  # No change!
    
    # Verify in database
    progress = get_skill_progress(user_id, skill_id)
    assert progress["successful_sessions"] == 1


# ============================================================
# 5️⃣ TEST: STREAK STABLE ACROSS UTC MIDNIGHT
# ============================================================

def test_streak_stable_across_utc_midnight():
    """
    ✅ Timezone-safe: Logical day calculation prevents midnight resets.
    
    Scenario:
    - User in IST (UTC+5:30)
    - Practice at 23:00 IST (17:30 UTC) → logical date = today
    - Practice at 01:00 IST next day (19:30 UTC prev day) → should still be same logical day
    """
    user_id = "test_user_5"
    
    # Set IST timezone (330 minutes = 5.5 hours ahead)
    set_user_timezone(user_id, timezone_offset_minutes=330)
    
    # Simulate practice near midnight IST
    # 23:00 IST = 17:30 UTC
    dt1 = datetime(2024, 2, 27, 17, 30, 0)  # 23:00 IST
    logical_date1 = get_logical_date(user_id, dt1)
    
    # Update streak
    result1 = update_practice_streak(user_id, current_date=dt1)
    assert result1["current_streak"] == 1
    
    # Next day at 01:00 IST = 19:30 UTC previous day (still same logical date!)
    dt2 = datetime(2024, 2, 27, 19, 30, 0)  # 01:00 IST next day
    logical_date2 = get_logical_date(user_id, dt2)
    
    # Different logical date because midnight boundary is local-date based.
    assert logical_date1 != logical_date2
    
    # Update streak again
    result2 = update_practice_streak(user_id, current_date=dt2)
    assert result2["current_streak"] == 2  # Increment (next logical day)
    
    # Move to actual next logical day (01:00 IST = 19:30 UTC + 24h)
    dt3 = datetime(2024, 2, 28, 19, 30, 0)  # 01:00 IST day after tomorrow
    result3 = update_practice_streak(user_id, current_date=dt3)
    assert result3["current_streak"] == 3  # Next day increments again


# ============================================================
# 6️⃣ TEST: ROLLING WINDOW CAPPED AT 30
# ============================================================

def test_rolling_window_capped_at_30():
    """
    ✅ Memory bounded: Analytics snapshots pruned to keep only last 30.
    """
    user_id = "test_user_6"
    skill_id = "skill_6"
    
    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    
    # Insert 50 snapshots
    for i in range(50):
        cursor.execute(
            """INSERT INTO analytics_snapshots 
               (user_id, skill_id, session_id, accuracy_score, 
                timing_score, technique_score, composite_score)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, skill_id, i, 80.0, 85.0, 0.8, 0.82)
        )
    conn.commit()
    conn.close()
    
    # Verify initial count
    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM analytics_snapshots WHERE user_id = ? AND skill_id = ?",
        (user_id, skill_id)
    )
    initial_count = cursor.fetchone()[0]
    assert initial_count == 50
    conn.close()
    
    # Prune to rolling window
    prune_analytics_window(user_id, skill_id, max_window=30)
    
    # Verify final count
    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM analytics_snapshots WHERE user_id = ? AND skill_id = ?",
        (user_id, skill_id)
    )
    final_count = cursor.fetchone()[0]
    assert final_count == 30
    conn.close()


# ============================================================
# 7️⃣ TEST: WEIGHTED AVERAGE FAVORS RECENT
# ============================================================

def test_weighted_average_favors_recent():
    """
    ✅ Recency bias: Recent scores weighted more heavily.
    
    Scores: [70, 75, 80]
    Weights: [1, 2, 3]
    Expected: (70*1 + 75*2 + 80*3) / 6 = 470/6 ≈ 78.33
    """
    scores = [70.0, 75.0, 80.0]
    
    analyzer = RollingWindowAnalytics()
    weighted = analyzer.weighted_average(scores)
    
    # Calculate expected
    expected = (70 * 1 + 75 * 2 + 80 * 3) / (1 + 2 + 3)
    assert abs(weighted - expected) < 0.01
    
    # Verify recent scores have more influence
    simple_avg = sum(scores) / len(scores)
    assert weighted > simple_avg  # Weighted should be higher (favors 80)


# ============================================================
# 8️⃣ TEST: COMPOSITE CONFIG VALIDATION
# ============================================================

def test_composite_config_validation():
    """
    ✅ Configuration: Weights must sum to 1.0 and have all keys.
    """
    # Valid config
    valid_config = {
        "accuracy": 0.45,
        "timing": 0.35,
        "technique": 0.20,
    }
    assert validate_composite_config(valid_config) is True
    
    # Invalid: Wrong keys
    bad_keys = {"accuracy": 0.5, "timing": 0.5}
    assert validate_composite_config(bad_keys) is False
    
    # Invalid: Sum != 1.0
    bad_sum = {
        "accuracy": 0.4,
        "timing": 0.4,
        "technique": 0.3,  # Sum = 1.1
    }
    assert validate_composite_config(bad_sum) is False


# ============================================================
# 9️⃣ TEST: COMPOSITE SCORE CALCULATION
# ============================================================

def test_composite_score_calculation():
    """
    ✅ Calculation: Composite score correctly weighting three dimensions.
    
    accuracy=90, timing=85, technique=0.8
    Expected: (0.90 * 0.45) + (0.85 * 0.35) + (0.80 * 0.20)
            = 0.405 + 0.2975 + 0.16 = 0.8625
    """
    config = {
        "accuracy": 0.45,
        "timing": 0.35,
        "technique": 0.20,
    }
    
    composite = compute_composite_score(
        accuracy_score=90,
        timing_score=85,
        technique_score=0.80,
        config=config
    )
    
    expected = (90/100 * 0.45) + (85/100 * 0.35) + (0.80 * 0.20)
    assert abs(composite - expected) < 0.01


# ============================================================
# 🔟 TEST: UNLOCK INTEGRITY CHECK
# ============================================================

def test_unlock_integrity_violation_detection():
    """
    ✅ Integrity: Detects impossible unlock states.
    
    Anomaly: is_unlocked=true but unlocked_at=null
    """
    user_id = "test_user_10"
    skill_id = "skill_10"
    
    # DB-level check constraints should block anomalous state insertion.
    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            """INSERT INTO skill_progress 
               (user_id, skill_id, skill_type, successful_sessions, is_unlocked, unlocked_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, skill_id, SKILL_TYPE, 10, 1, None)
        )
        conn.commit()
    conn.close()


# ============================================================
# 1️⃣1️⃣ TEST: SESSION HASH DEDUPLICATION
# ============================================================

def test_session_hash_deduplication():
    """
    ✅ Hashing: Session hash correctly identifies duplicates.
    """
    user_id = "test_user_11"
    skill_id = "skill_11"
    audio_hash = "audio_123"
    
    # Generate hash
    hash1 = compute_session_hash(user_id, skill_id, audio_hash)
    
    # Same inputs → same hash
    hash2 = compute_session_hash(user_id, skill_id, audio_hash)
    assert hash1 == hash2
    
    # Different audio → different hash
    hash3 = compute_session_hash(user_id, skill_id, "different_audio")
    assert hash1 != hash3
    
    # Register hash
    register_session_hash(hash1, user_id, skill_id, 1)
    assert session_hash_exists(hash1) is True
    assert session_hash_exists(hash3) is False


# ============================================================
# 🧪 INTEGRATION TEST - Full Mastery Flow
# ============================================================

def test_full_mastery_flow():
    """
    ✅ Integration: Complete unlock flow from 0 to unlock.
    
    Scenario:
    - 3 successful sessions → unlock
    - 1 failed session → no regression
    - Repeated failures → unlock stays
    """
    user_id = "test_integration"
    skill_id = "skill_integration"
    
    # === Phase 1: Build streak ===
    sessions = [
        (1, 0.80, False),  # Session 1: Success
        (2, 0.82, False),  # Session 2: Success
        (3, 0.79, True),   # Session 3: Success → UNLOCK
    ]
    
    for session_num, score, should_unlock in sessions:
        result = update_skill_progress(
            user_id, skill_id, SKILL_TYPE, score, THRESHOLD,
            session_hash=compute_session_hash(user_id, skill_id, f"audio_{session_num}")
        )
        assert result["successful_sessions"] == session_num
        assert result["unlocked_now"] == should_unlock
    
    # === Phase 2: Failed sessions don't reverse unlock ===
    for fail_num in range(1, 4):
        result = update_skill_progress(
            user_id, skill_id, SKILL_TYPE, 0.30, THRESHOLD,
            session_hash=compute_session_hash(user_id, skill_id, f"fail_{fail_num}")
        )
        assert result["is_unlocked"] is True, f"Unlock reversed on fail {fail_num}!"
    
    # === Verify final state ===
    progress = get_skill_progress(user_id, skill_id)
    assert progress["is_unlocked"] is True
    assert progress["successful_sessions"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
