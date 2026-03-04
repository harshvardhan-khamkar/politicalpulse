from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.users import AppUser
from app.schemas.auth import TokenResponse, UserCreate, UserProfile
from app.security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a normal user account (role=user)."""
    existing = db.query(AppUser).filter(AppUser.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    existing_email = db.query(AppUser).filter(AppUser.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = AppUser(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role="user",
        is_active=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    """Issue JWT token for any valid app user (admin/user), via username or email."""
    content_type = (request.headers.get("content-type") or "").lower()

    if "application/json" in content_type:
        try:
            payload = await request.json()
        except ValueError:
            payload = {}
    else:
        payload = await request.form()

    if not hasattr(payload, "get"):
        payload = {}

    identifier = ((payload.get("username") or payload.get("email") or "")).strip()
    password = payload.get("password")

    if not identifier or not isinstance(password, str) or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide username or email, and password",
        )

    user = authenticate_user(db, identifier, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expires_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role, "uid": str(user.id)},
        expires_delta=timedelta(minutes=expires_minutes),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_minutes * 60,
    }


@router.get("/me", response_model=UserProfile)
def get_me(current_user: AppUser = Depends(get_current_user)):
    """Validate current bearer token and return profile."""
    return current_user
