"""
Shared FastAPI dependencies -- auth + rate limiting + DB session. Route
handlers import from here so this sequence stays identical everywhere.
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..auth.firebase import bearer_scheme, verify_firebase_token
from ..core.redis_client import check_rate_limit
from ..db import models
from ..db.session import get_db


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """Verifies the Firebase token, upserts the matching User row (created on
    first login, reused after), and returns it."""
    claims = verify_firebase_token(creds)
    uid = claims["uid"]
    email = claims.get("email", "")

    user = db.get(models.User, uid)
    if user is None:
        user = models.User(id=uid, email=email, display_name=claims.get("name", ""))
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def enforce_rate_limit(request: Request, user: models.User = Depends(get_current_user)) -> None:
    """Per-user rate limit, keyed on the authenticated user id rather than
    IP (which can be shared across users behind a NAT/proxy)."""
    allowed = check_rate_limit(key=user.id)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded. Try again shortly.")
