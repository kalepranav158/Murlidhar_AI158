import os
import glob
import json
from datetime import datetime
from typing import Optional
from app.services.skill_profile import build_skill_profile
from database.db import get_student_progress  # type: ignore[attr-defined]
from database.db import update_student_progress  # type: ignore[attr-defined]
from database.db import is_alankar_mastered  # type: ignore[attr-defined]
from database.db import is_song_mastered  # type: ignore[attr-defined]
from database.db import count_mastered_alankars  # type: ignore[attr-defined]
from database.db import count_mastered_songs  # type: ignore[attr-defined]


def evaluate_curriculum_progress(user_id: str) -> dict:
    """Assess student's analytics and update unlocks / level accordingly.

    Returns a curriculum response block that can be attached to practice results.
    """

    # load or initialize profile
    profile = get_student_progress(user_id) or {
        "user_id": user_id,
        "current_level": "beginner",
        "unlocked_content": [],
        "mastered_content": [],
        "last_evaluated": None,
    }

    # compute skill snapshot
    skill = build_skill_profile(user_id)

    profile["skill_snapshot"] = {
        "accuracy": skill.get("accuracy_index", 0.0),
        "rhythm_index": skill.get("rhythm_stability_index", 0.0),
        # technique_score now derived from historical sessions
        "technique_score": skill.get("technique_score", 0.0),
        "composite_score": skill.get("composite_score", 0.0),
    }

    # level progression rules
    current = profile.get("current_level", "beginner")
    new_level = current

    if current == "beginner":
        if (
            skill.get("composite_score", 0.0) >= 0.75
            and skill.get("rhythm_stability_index", 0.0) >= 0.7
            and skill.get("breath_control_index", 0.0) >= 0.6
            and count_mastered_alankars(user_id) >= 5
        ):
            new_level = "intermediate"
    elif current == "intermediate":
        if (
            skill.get("composite_score", 0.0) >= 0.85
            and skill.get("breath_control_index", 0.0) >= 0.75
            and count_mastered_songs(user_id) >= 1
        ):
            new_level = "advanced"

    if new_level != current:
        profile["current_level"] = new_level

    # update mastery / unlocks
    # filter out any invalid entries that may have crept in (e.g. None)
    unlocked = {x for x in profile.get("unlocked_content", []) if isinstance(x, str)}
    mastered = {x for x in profile.get("mastered_content", []) if isinstance(x, str)}

    # ensure at least one piece of content is available for current level
    if not unlocked:
        for fname in glob.glob("songs/*.json"):
            try:
                cont = json.load(open(fname))
                cid = cont.get("id")
                if cid and cont.get("level") == profile.get("current_level"):
                    unlocked.add(cid)
            except Exception:
                continue
        # save preliminary unlocks even if empty
        profile["unlocked_content"] = list(unlocked)

    # examine each unlocked item for potential mastery
    for cid in list(unlocked):
        if cid in mastered:
            continue
        path = f"songs/{cid}.json"
        if not os.path.exists(path):
            continue
        try:
            content = json.load(open(path))
        except Exception:
            continue

        ctype = content.get("type")
        if ctype == "alankar":
            if is_alankar_mastered(user_id, cid):
                mastered.add(cid)
                nxt = content.get("unlock_next")
                if nxt:
                    unlocked.add(nxt)
        else:
            # treat anything else as song/exercise
            total = len(content.get("phrases", []))
            if total > 0 and is_song_mastered(user_id, cid, total):
                mastered.add(cid)
                nxt = content.get("unlock_next")
                if nxt:
                    unlocked.add(nxt)

    profile["unlocked_content"] = list(unlocked)
    profile["mastered_content"] = list(mastered)
    profile["last_evaluated"] = datetime.now().isoformat()

    # persist profile
    update_student_progress(user_id, profile)

    # recommendation & goals
    recommended = None
    reason = None
    for c in profile["unlocked_content"]:
        if c not in profile["mastered_content"]:
            recommended = c
            reason = "Next unlocked content"
            break

    locked = []
    for fname in glob.glob("songs/*.json"):
        try:
            cont = json.load(open(fname))
            cid = cont.get("id")
            if cid and cid not in unlocked:
                locked.append(cid)
        except Exception:
            continue

    next_goal = ""
    lvl = profile["current_level"]
    if lvl == "beginner":
        if skill.get("composite_score", 0.0) < 0.75:
            next_goal = "Increase composite score to 0.75"
        elif skill.get("rhythm_stability_index", 0.0) < 0.7:
            next_goal = "Improve rhythm stability to 0.7"
        elif count_mastered_alankars(user_id) < 5:
            next_goal = "Master 5 alankars"
    elif lvl == "intermediate":
        if skill.get("composite_score", 0.0) < 0.85:
            next_goal = "Composite ≥ 0.85"
        elif count_mastered_songs(user_id) < 1:
            next_goal = "Master 1 song"

    return {
        "current_level": profile["current_level"],
        "unlocked_content": profile["unlocked_content"],
        "mastered_content": profile["mastered_content"],
        "skill_snapshot": profile.get("skill_snapshot", {}),
        "recommended_content": recommended,
        "reason": reason,
        "locked": locked,
        "next_goal": next_goal,
    }
