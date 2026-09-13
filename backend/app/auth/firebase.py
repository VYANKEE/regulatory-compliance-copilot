"""
Firebase Authentication -- token verification dependency.

Init is lazy (`_ensure_initialized()`), so importing this module never
crashes even without Firebase configured; a missing credentials file gives
a clean 500 "auth not configured" instead of a raw firebase exception,
so unrelated routes (like /health) still work in local dev.
"""

import firebase_admin
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

from ..core.config import get_settings

_bearer = HTTPBearer(auto_error=False)
_initialized = False


def _ensure_initialized() -> None:
    global _initialized
    if _initialized:
        return
    settings = get_settings()
    if not settings.firebase_credentials_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Firebase auth not configured on this server (FIREBASE_CREDENTIALS_PATH missing).",
        )
    cred = credentials.Certificate(settings.firebase_credentials_abspath)
    firebase_admin.initialize_app(cred)
    _initialized = True


def verify_firebase_token(
    creds: HTTPAuthorizationCredentials | None = None,
) -> dict:
    """Verifies the bearer token and returns decoded claims (uid, email, ...).
    Invalid/expired/missing token -> 401."""
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token.")

    _ensure_initialized()
    try:
        decoded = firebase_auth.verify_id_token(creds.credentials)
    except Exception as e:  # firebase raises several distinct exception types
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid auth token: {e}")
    return decoded


bearer_scheme = _bearer
