# 🚀 QUICK REFERENCE - How to Use the New Edge Case Fixes

---

## 1️⃣ Update Mastery Progress (Safe & Idempotent)

```python
from database.db import (
    update_skill_progress,
    compute_session_hash
)

# During practice session evaluation:

# Generate unique session hash to prevent duplicates
session_hash = compute_session_hash(
    user_id="user_123",
    skill_id="alankar_1",
    audio_checksum="sha256_of_audio_data"
)

# Update mastery (idempotent - safe to retry)
result = update_skill_progress(
    user_id="user_123",
    skill_id="alankar_1",
    composite_score=0.82,  # 0-1 range
    session_hash=session_hash
)

# Check result
if result["duplicate"]:
    print("Session already processed!")
elif result["unlocked_now"]:
    print("🎉 Skill unlocked!")
    print(f"After {result['successful_sessions']} successful sessions")
elif result["updated"]:
    print(f"Progress updated: {result['successful_sessions']}/3 sessions")
else:
    print(f"Session below threshold (need 0.75)")

# Result structure:
# {
#     "updated": bool,
#     "duplicate": bool,
#     "unlocked_now": bool,
#     "successful_sessions": int,
#     "is_unlocked": bool,
#     "message": str
# }
```

---

## 2️⃣ Timezone-Aware Streak Update

```python
from database.db import (
    set_user_timezone,
    update_practice_streak,
    get_practice_streak
)

# On first login, set user's timezone
set_user_timezone(
    user_id="user_123",
    timezone_offset_minutes=330  # IST: +5:30 hours = 330 minutes
)

# After practice session
streak = update_practice_streak(user_id="user_123")

# Check streak
current = get_practice_streak(user_id="user_123")
print(f"Streak: {current['current_streak']} days")
print(f"Longest: {current['longest_streak']} days")
print(f"Last practiced: {current['last_practice_date']}")

# Common timezone offsets:
timezones = {
    "IST": 330,              # India Standard Time (UTC+5:30)
    "PST": -480,             # Pacific Standard Time (UTC-8:00)
    "EST": -300,             # Eastern Standard Time (UTC-5:00)
    "UTC": 0,                # Coordinated Universal Time
    "CET": 60,               # Central European Time (UTC+1:00)
}
```

---

## 3️⃣ Calculate Composite Score (With Config)

```python
from app.services.analytics_config import (
    compute_composite_score,
    COMPOSITE_CONFIG
)

# Simple usage with default weights
composite = compute_composite_score(
    accuracy_score=85,       # 0-100
    timing_score=80,         # 0-100
    technique_score=0.75     # 0-1
)
# Result: 0.783 (weighted average)

# With custom weights for experimentation
custom_config = {
    "accuracy": 0.50,
    "timing": 0.30,
    "technique": 0.20,
}

custom_composite = compute_composite_score(
    accuracy_score=85,
    timing_score=80,
    technique_score=0.75,
    config=custom_config
)

# Default weights can be accessed
print(COMPOSITE_CONFIG)
# Output: {'accuracy': 0.45, 'timing': 0.35, 'technique': 0.20}
```

---

## 4️⃣ Rolling Window Analytics

```python
from app.services.analytics_config import RollingWindowAnalytics

analyzer = RollingWindowAnalytics()

# Weighted average (recent scores weighted more)
scores = [70.0, 75.0, 80.0, 85.0, 88.0]
avg = analyzer.weighted_average(scores)
# Recent scores (88, 85) have more influence than (70, 75)

# Trend analysis
slope = analyzer.trend_slope(scores)
# Positive = improving, Negative = declining

# Consistency measure
consistency = analyzer.consistency_index(scores)
# Higher = more stable performance

# Performance recommendation
if slope > 0.5:
    recommendation = "Strong improvement - keep momentum!"
elif slope < -0.5:
    recommendation = "Declining - review technique"
elif abs(slope) < 0.1:
    recommendation = "Plateau - try new methods"
```

---

## 5️⃣ Verify Unlock Integrity (Debug)

```python
from database.db import verify_unlock_integrity

# Check if unlock state is valid
integrity = verify_unlock_integrity(
    user_id="user_123",
    skill_id="alankar_1"
)

if integrity["valid"]:
    print("✓ Unlock state is valid")
else:
    print("✗ Data corruption detected!")
    for issue in integrity["issues"]:
        print(f"  - {issue}")

# Structure returned:
# {
#     "is_unlocked": bool,
#     "unlocked_at": str or None,
#     "successful_sessions": int,
#     "valid": bool,
#     "issues": [str]
# }
```

---

## 6️⃣ Using Debug Endpoints

```bash
# ==========================================
# View mastery progress state
# ==========================================
curl http://localhost:8000/debug/progress/user_123/alankar_1

# Response:
# {
#   "user_id": "user_123",
#   "skill_id": "alankar_1",
#   "successful_sessions": 2,
#   "last_success_at": "2024-02-27T15:30:00",
#   "composite_average": 0.81,
#   "is_unlocked": false,
#   "unlocked_at": null
# }

# ==========================================
# View analytics window (last 30 sessions)
# ==========================================
curl http://localhost:8000/debug/analytics/user_123/alankar_1

# Response:
# {
#   "user_id": "user_123",
#   "skill_id": "alankar_1",
#   "total_snapshots": 45,
#   "window_size": 30,
#   "pruned": true,
#   "snapshots": [...]
# }

# ==========================================
# View streak and timezone
# ==========================================
curl http://localhost:8000/debug/streak/user_123

# Response:
# {
#   "current_streak": 7,
#   "longest_streak": 14,
#   "last_practice_date": "2024-02-27",
#   "timezone_offset_minutes": 330,
#   "timezone_offset_hours": 5.5
# }

# ==========================================
# Verify unlock integrity
# ==========================================
curl http://localhost:8000/debug/unlock-check/user_123/alankar_1

# Response:
# {
#   "is_unlocked": true,
#   "unlocked_at": "2024-02-25T10:00:00",
#   "valid": true,
#   "issues": []
# }

# ==========================================
# View recent sessions
# ==========================================
curl http://localhost:8000/debug/sessions/user_123/alankar_1?limit=5

# Response:
# {
#   "sessions": [
#     {
#       "id": 1,
#       "timestamp": "2024-02-27T15:30:00",
#       "accuracy": 85.5,
#       "composite": 0.823,
#       "technique": 0.75
#     },
#     ...
#   ]
# }
```

---

## 7️⃣ Pruning Analytics (Manual)

```python
from database.db import prune_analytics_window

# Keep only last 30 snapshots per skill
prune_analytics_window(
    user_id="user_123",
    skill_id="alankar_1",
    max_window=30  # Default value
)

# This deletes oldest snapshots if count > 30
# Automatically preserves recent data
```

---

## 8️⃣ Practice Endpoint Integration Example

```python
# In your practice endpoint handler:

from fastapi import APIRouter
from database.db import (
    update_skill_progress,
    compute_session_hash,
    update_practice_streak
)
from app.services.analytics_config import compute_composite_score

router = APIRouter()

@router.post("/practice/submit/{user_id}/{skill_id}")
async def submit_practice(user_id: str, skill_id: str, file: UploadFile):
    
    # 1. Evaluate audio
    accuracy, timing, technique = evaluate_audio(file)
    
    # 2. Compute composite score
    composite = compute_composite_score(
        accuracy_score=accuracy,
        timing_score=timing,
        technique_score=technique
    )
    
    # 3. Generate session hash from audio
    audio_data = await file.read()
    audio_hash = sha256(audio_data).hexdigest()
    session_hash = compute_session_hash(user_id, skill_id, audio_hash)
    
    # 4. Update mastery (safe, idempotent)
    result = update_skill_progress(
        user_id=user_id,
        skill_id=skill_id,
        composite_score=composite,
        session_hash=session_hash
    )
    
    # 5. Update practice streak
    streak = update_practice_streak(user_id)
    
    # 6. Return feedback
    if result["duplicate"]:
        return {"status": "duplicate", "error": "Session already processed"}
    
    return {
        "status": "success",
        "composite_score": composite,
        "unlocked": result["unlocked_now"],
        "successful_sessions": result["successful_sessions"],
        "streak": streak["current_streak"]
    }
```

---

## 9️⃣ Running Tests

```bash
# Run all edge case tests
pytest tests/test_edge_cases.py -v

# Run specific test
pytest tests/test_edge_cases.py::test_unlock_requires_three_successful_sessions -v

# Run with coverage
pytest tests/test_edge_cases.py --cov=database --cov=app/services

# Run tests and show print statements
pytest tests/test_edge_cases.py -v -s
```

---

## 🔟 Environment Configuration

```bash
# Enable debug endpoints during development
export DEBUG_ENDPOINTS=true

# Disable debug endpoints for production
export DEBUG_ENDPOINTS=false

# Verify setting
python -c "import os; print('DEBUG_ENDPOINTS:', os.getenv('DEBUG_ENDPOINTS', 'true'))"
```

---

## 📋 Common Patterns

### Pattern: Handle Duplicate Submissions
```python
result = update_skill_progress(..., session_hash=hash)
if result["duplicate"]:
    # Idempotent: Return same response as original
    return {"status": "already_processed"}
```

### Pattern: Verify Unlock State
```python
integrity = verify_unlock_integrity(user_id, skill_id)
if not integrity["valid"]:
    logger.error(f"Unlock corruption: {integrity['issues']}")
    alert_admin("Data corruption detected")
```

### Pattern: Build Analytics Snapshot
```python
from app.services.analytics_config import build_analytics_snapshot

snapshot = build_analytics_snapshot(
    user_id=user_id,
    skill_id=skill_id,
    session_id=db_session_id,
    accuracy=accuracy_score,
    timing=timing_score,
    technique=technique_score
)

# Now can analyze with rolling window
```

### Pattern: Check for Unlock
```python
progress = get_skill_progress(user_id, skill_id)
if progress and progress["is_unlocked"]:
    # Show next skill
    return {"next_skill": "alankar_2"}
else:
    # Show practice page
    return {"practice_skill": skill_id}
```

---

## 🎓 Best Practices

1. **Always use `compute_session_hash()`** when submitting practice sessions
2. **Set user timezone** on first login for correct streak calculations
3. **Verify unlock integrity** in admin dashboards to catch data corruption
4. **Use debug endpoints** to troubleshoot issues in development
5. **Run tests** before deploying changes to production
6. **Monitor analytics table** size and run pruning periodically
7. **Validate configuration** after updating `COMPOSITE_CONFIG`

---

## ⚡ Performance Tips

- **Batch operations**: Call `prune_analytics_window()` as an async job, not per request
- **Cache timezone**: Cache `get_user_timezone()` results to reduce database hits
- **Index optimization**: Ensure indexes on `(user_id, skill_id)` for quick lookups
- **Async transactions**: Don't block requests on analytics pruning

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Duplicate session rejected" on first submit | Check `session_hash` is correctly computed |
| Unlock not triggering after 3 successes | Verify scores > 0.75 threshold |
| Streak resets unexpectedly | Check timezone offset is set with `set_user_timezone()` |
| Analytics window > 30 | Run `prune_analytics_window()` manually |
| Unlock integrity "VIOLATION" | Check database constraints, may need data repair |

---

**Last Updated:** February 27, 2026  
**Version:** 1.0
