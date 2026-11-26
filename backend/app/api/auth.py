"""Authentication: register, login, refresh, logout, forgot/reset, profile."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.deps import get_current_user, limit
from ..core.security import (
    create_access_token, create_refresh_token, decode_token, hash_password,
    hash_reset_token, new_reset_token, verify_password,
)
from ..db.base import get_db
from ..db.models import User
from ..schemas import (
    ForgotIn, LoginIn, ProfileUpdateIn, RefreshIn, RegisterIn, ResetIn, TokenOut, UserOut,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _tokens(user: User) -> TokenOut:
    return TokenOut(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id, user.role),
        user=UserOut.model_validate(user),
    )


@router.post("/register", response_model=TokenOut, status_code=201,
             dependencies=[Depends(limit("auth", settings.auth_rate_limit_per_min))])
def register(body: RegisterIn, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == body.email.lower()))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    user = User(
        name=body.name.strip(), email=body.email.lower(), phone=body.phone, city=body.city,
        password_hash=hash_password(body.password), matric_marks=body.matric_marks,
        inter_marks=body.inter_marks, interested_program_id=body.interested_program_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _tokens(user)


@router.post("/login", response_model=TokenOut,
             dependencies=[Depends(limit("auth", settings.auth_rate_limit_per_min))])
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash) or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return _tokens(user)


@router.post("/refresh", response_model=TokenOut)
def refresh(body: RefreshIn, db: Session = Depends(get_db)):
    payload = decode_token(body.refresh_token, "refresh")
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return _tokens(user)


@router.post("/logout")
def logout(user: User = Depends(get_current_user)):
    # Stateless JWT: logout is client-side token deletion. Endpoint kept for API completeness.
    return {"detail": "Logged out. Please delete your tokens on the client."}


@router.post("/forgot-password")
def forgot_password(body: ForgotIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    response = {"detail": "If this email is registered, a password reset link has been created."}
    if user is not None:
        token = new_reset_token()
        user.reset_token_hash = hash_reset_token(token)
        user.reset_expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
        db.commit()
        if settings.environment == "dev":
            # Demo convenience only — in production the token is emailed, never returned.
            response["reset_token_dev_only"] = token
    return response


@router.post("/reset-password")
def reset_password(body: ResetIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.reset_token_hash == hash_reset_token(body.token)))
    if user is None or user.reset_expires_at is None or \
            user.reset_expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Reset token is invalid or expired")
    user.password_hash = hash_password(body.new_password)
    user.reset_token_hash = None
    user.reset_expires_at = None
    db.commit()
    return {"detail": "Password has been reset. You can now log in."}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.put("/profile", response_model=UserOut)
@router.put("/me", response_model=UserOut)
@router.patch("/me", response_model=UserOut)
def update_profile(body: ProfileUpdateIn, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user
