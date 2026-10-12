"""
Administrator Authentication & Authorization Module.
Provides credential verification from environment variables,
cryptographic token generation, and FastAPI route protection.
"""

from datetime import datetime, timedelta, timezone
import hmac
import secrets
from threading import RLock
from typing import Any, Dict, Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings

# Thread-safe in-memory store for active admin tokens
_admin_tokens_lock = RLock()
_active_admin_tokens: Dict[str, Dict[str, Any]] = {}
TOKEN_LIFETIME_HOURS = 8

bearer_scheme = HTTPBearer(auto_error=False)


def authenticate_admin(username: str, password: str) -> Optional[str]:
    """
    Verifies admin credentials using timing-attack-safe string comparison.
    Generates an unguessable session token upon success.
    """
    expected_user = settings.ADMIN_USERNAME
    expected_pass = settings.ADMIN_PASSWORD

    user_match = hmac.compare_digest(username.strip().encode("utf-8"), expected_user.strip().encode("utf-8"))
    pass_match = hmac.compare_digest(password.encode("utf-8"), expected_pass.encode("utf-8"))

    if not (user_match and pass_match):
        return None

    # Generate high-entropy unguessable token
    token = f"adm_{secrets.token_urlsafe(36)}"
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=TOKEN_LIFETIME_HOURS)

    with _admin_tokens_lock:
        # Evict expired tokens periodically
        expired = [t for t, meta in _active_admin_tokens.items() if meta["expires_at"] < now]
        for t in expired:
            _active_admin_tokens.pop(t, None)

        _active_admin_tokens[token] = {
            "username": expected_user,
            "created_at": now.isoformat(),
            "expires_at": expires_at,
        }

    return token


def validate_admin_token(token: Optional[str]) -> bool:
    """Checks whether an admin token exists and has not expired."""
    if not token:
        return False

    clean_token = token.strip()
    if clean_token.startswith("Bearer "):
        clean_token = clean_token[7:].strip()

    now = datetime.now(timezone.utc)
    with _admin_tokens_lock:
        meta = _active_admin_tokens.get(clean_token)
        if not meta:
            return False
        if meta["expires_at"] < now:
            _active_admin_tokens.pop(clean_token, None)
            return False
        return True


def revoke_admin_token(token: Optional[str]) -> bool:
    """Revokes an active administrator session token."""
    if not token:
        return False
    clean_token = token.strip()
    if clean_token.startswith("Bearer "):
        clean_token = clean_token[7:].strip()

    with _admin_tokens_lock:
        return _active_admin_tokens.pop(clean_token, None) is not None


def get_current_admin(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
) -> Dict[str, str]:
    """
    FastAPI security dependency protecting administrative endpoints.
    Requires a valid admin token via Authorization header or X-Admin-Token.
    """
    token_to_verify = None
    if auth and auth.credentials:
        token_to_verify = auth.credentials
    elif x_admin_token:
        token_to_verify = x_admin_token

    if not token_to_verify or not validate_admin_token(token_to_verify):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator authentication required. Invalid or expired admin token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"username": settings.ADMIN_USERNAME}
