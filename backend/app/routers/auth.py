from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import audit
from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import LoginRequest, RegisterRequest, Token, UserOut
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_token(user: User) -> Token:
    return Token(
        access_token=create_access_token(user_id=user.user_id, role=user.role),
        user=UserOut.model_validate(user),
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> Token:
    # In production we disable open self-registration (set ALLOW_REGISTRATION=false
    # on the EC2 .env). Admins can still create users via /api/admin/* and the
    # existing seeded accounts continue to work normally.
    if not settings.allow_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration is disabled on this deployment. Ask an admin for an account.",
        )

    email = payload.email.lower().strip()

    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        audit.record(db, user_id=None, event_type="register.duplicate",
                     detail=f"email={email}", request=request)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role="student",
    )
    db.add(user)
    db.flush()
    audit.record(db, user_id=user.user_id, event_type="register.success",
                 detail=f"email={email}", request=request)
    db.commit()
    db.refresh(user)
    return _issue_token(user)


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> Token:
    email = payload.email.lower().strip()
    user = db.scalar(select(User).where(User.email == email))

    # Use a single generic error to avoid leaking whether the email exists.
    if user is None or not verify_password(payload.password, user.password_hash):
        # Audit failed attempt -- counted toward intrusion-detection if added later.
        audit.record(db, user_id=user.user_id if user else None,
                     event_type="login.failed", detail=f"email={email}", request=request)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    user.last_login_at = datetime.now(timezone.utc)
    audit.record(db, user_id=user.user_id, event_type="login.success",
                 detail=f"email={email}", request=request)
    db.commit()
    db.refresh(user)
    return _issue_token(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)
