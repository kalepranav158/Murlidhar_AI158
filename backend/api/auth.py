import os
import secrets
import threading
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # If dotenv is unavailable, environment variables can still come from the host shell.
    pass

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

_AUTH_USERNAME = os.getenv("VENORA_AUTH_USERNAME", "gokul")
_AUTH_PASSWORD = os.getenv("VENORA_AUTH_PASSWORD", "venora123")
_GOOGLE_CLIENT_ID = os.getenv("VENORA_GOOGLE_CLIENT_ID", "").strip()
_GOOGLE_CLIENT_IDS = {
    value.strip()
    for value in os.getenv("VENORA_GOOGLE_CLIENT_IDS", "").split(",")
    if value.strip()
}
if _GOOGLE_CLIENT_ID:
    _GOOGLE_CLIENT_IDS.add(_GOOGLE_CLIENT_ID)
_GOOGLE_ALLOWED_DOMAIN = os.getenv("VENORA_GOOGLE_ALLOWED_DOMAIN", "").strip().lower()
_GOOGLE_ALLOWED_EMAILS = {
    value.strip().lower()
    for value in os.getenv("VENORA_GOOGLE_ALLOWED_EMAILS", "").split(",")
    if value.strip()
}
_AUTH_DEBUG = os.getenv("VENORA_AUTH_DEBUG", "false").strip().lower() == "true"

try:
    # Allows minor local clock drift when validating Google ID token iat/exp.
    _GOOGLE_CLOCK_SKEW_SECONDS = max(
        0,
        min(300, int(os.getenv("VENORA_GOOGLE_CLOCK_SKEW_SECONDS", "30"))),
    )
except ValueError:
    _GOOGLE_CLOCK_SKEW_SECONDS = 30

try:
    _TOKEN_TTL_MINUTES = max(10, int(os.getenv("VENORA_AUTH_TOKEN_TTL_MINUTES", "480")))
except ValueError:
    _TOKEN_TTL_MINUTES = 480

_sessions: dict[str, dict[str, object]] = {}
_sessions_lock = threading.Lock()

try:
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token

    _GOOGLE_AUTH_AVAILABLE = True
except Exception:
    google_requests = None
    google_id_token = None
    _GOOGLE_AUTH_AVAILABLE = False


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=1, max_length=8192)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None

    return token.strip()


def _create_session(
    username: str,
    auth_provider: str = "password",
    email: str | None = None,
) -> tuple[str, datetime]:
    token = secrets.token_urlsafe(32)
    expires_at = _utcnow() + timedelta(minutes=_TOKEN_TTL_MINUTES)

    with _sessions_lock:
        _sessions[token] = {
            "username": username,
            "auth_provider": auth_provider,
            "email": email,
            "expires_at": expires_at,
        }

    return token, expires_at


def _get_session(token: str) -> dict[str, object] | None:
    with _sessions_lock:
        session = _sessions.get(token)
        if not session:
            return None

        expires_at = session.get("expires_at")
        if not isinstance(expires_at, datetime) or expires_at <= _utcnow():
            _sessions.pop(token, None)
            return None

        return {
            "username": str(session.get("username") or ""),
            "auth_provider": str(session.get("auth_provider") or "password"),
            "email": str(session.get("email") or "") or None,
            "expires_at": expires_at,
        }


def _delete_session(token: str) -> None:
    with _sessions_lock:
        _sessions.pop(token, None)


def _require_session(authorization: str | None) -> dict[str, object]:
    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    session = _get_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or invalid token")

    return {
        "token": token,
        **session,
    }


def _verify_google_credential(credential: str) -> dict[str, Any]:
    if not _GOOGLE_CLIENT_IDS:
        raise HTTPException(
            status_code=503,
            detail="Google Sign-In is not configured on the server",
        )

    if not _GOOGLE_AUTH_AVAILABLE or google_id_token is None or google_requests is None:
        raise HTTPException(
            status_code=503,
            detail="Google Sign-In dependency is not installed",
        )

    try:
        payload = google_id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            clock_skew_in_seconds=_GOOGLE_CLOCK_SKEW_SECONDS,
        )
    except Exception as exc:
        logger.exception("Google credential verification failed")
        message = "Invalid Google credential"
        if _AUTH_DEBUG:
            message = f"{message}: {exc}"
        raise HTTPException(status_code=401, detail=message)

    audience = str(payload.get("aud") or "").strip()
    if audience not in _GOOGLE_CLIENT_IDS:
        raise HTTPException(status_code=401, detail="Google credential audience mismatch")

    issuer = str(payload.get("iss") or "")
    if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(status_code=401, detail="Invalid Google credential issuer")

    email = str(payload.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=401, detail="Google account email not available")

    if payload.get("email_verified") is False:
        raise HTTPException(status_code=401, detail="Google account email is not verified")

    if _GOOGLE_ALLOWED_DOMAIN and not email.endswith(f"@{_GOOGLE_ALLOWED_DOMAIN}"):
        raise HTTPException(status_code=403, detail="Google account is not in the allowed domain")

    if _GOOGLE_ALLOWED_EMAILS and email not in _GOOGLE_ALLOWED_EMAILS:
        raise HTTPException(status_code=403, detail="Google account is not allowed")

    full_name = str(payload.get("name") or "").strip()
    username = full_name or email.split("@", maxsplit=1)[0]

    return {
        "username": username,
        "email": email,
    }


@router.post("/login")
def login(payload: LoginRequest):
    user_ok = secrets.compare_digest(payload.username, _AUTH_USERNAME)
    pass_ok = secrets.compare_digest(payload.password, _AUTH_PASSWORD)

    if not (user_ok and pass_ok):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token, expires_at = _create_session(payload.username, auth_provider="password")

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": payload.username,
        "auth_provider": "password",
        "email": None,
        "expires_at": expires_at.isoformat(),
    }


@router.post("/google")
def google_login(payload: GoogleLoginRequest):
    google_identity = _verify_google_credential(payload.credential)
    username = str(google_identity["username"])
    email = str(google_identity["email"])

    token, expires_at = _create_session(
        username,
        auth_provider="google",
        email=email,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": username,
        "auth_provider": "google",
        "email": email,
        "expires_at": expires_at.isoformat(),
    }


@router.get("/verify")
def verify(authorization: str | None = Header(default=None, alias="Authorization")):
    session = _require_session(authorization)
    expires_at = session.get("expires_at")
    expires_at_iso = expires_at.isoformat() if isinstance(expires_at, datetime) else _utcnow().isoformat()

    return {
        "authenticated": True,
        "username": session["username"],
        "auth_provider": session["auth_provider"],
        "email": session["email"],
        "expires_at": expires_at_iso,
    }


@router.post("/logout")
def logout(authorization: str | None = Header(default=None, alias="Authorization")):
    token = _extract_bearer_token(authorization)
    if token:
        _delete_session(token)

    return {
        "success": True,
    }
