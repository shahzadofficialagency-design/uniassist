"""Auth dependencies + a tiny in-memory rate limiter."""
from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db.models import User
from .security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    payload = decode_token(creds.credentials, "access")
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return user


def get_optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User | None:
    if creds is None:
        return None
    payload = decode_token(creds.credentials, "access")
    if payload is None:
        return None
    return db.get(User, int(payload["sub"]))


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required")
    return user


class RateLimiter:
    """Sliding-window limiter keyed by client IP + bucket name."""

    def __init__(self) -> None:
        self._hits: dict[str, deque] = defaultdict(deque)

    def check(self, key: str, limit_per_min: int) -> bool:
        now = time.time()
        bucket = self._hits[key]
        while bucket and bucket[0] < now - 60:
            bucket.popleft()
        if len(bucket) >= limit_per_min:
            return False
        bucket.append(now)
        return True


rate_limiter = RateLimiter()


def limit(bucket_name: str, per_min: int):
    def _dep(request: Request):
        ip = request.client.host if request.client else "unknown"
        if not rate_limiter.check(f"{bucket_name}:{ip}", per_min):
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                                "Too many requests — please wait a minute and try again")
    return _dep
