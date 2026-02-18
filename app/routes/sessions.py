from fastapi import APIRouter, Query
from database.db import get_sessions

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("/")
def list_sessions(user_id: str , limit: int = Query(20, ge=1, le=100)):
    sessions = get_sessions(user_id=user_id, limit=limit)

    return {
        "count": len(sessions),
        "sessions": sessions
    }
