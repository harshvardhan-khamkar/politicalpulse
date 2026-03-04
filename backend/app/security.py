from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, get_db
from app.models.users import AppUser

# Exposed in Swagger auth modal
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def authenticate_user(db: Session, username_or_email: str, password: str) -> Optional[AppUser]:
    identifier = (username_or_email or "").strip()
    if not identifier:
        return None

    user = (
        db.query(AppUser)
        .filter(
            AppUser.is_active == 1,
            or_(
                AppUser.username == identifier,
                func.lower(AppUser.email) == identifier.lower(),
            ),
        )
        .first()
    )
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(data: Dict[str, str], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> AppUser:
    """Dependency that validates bearer token and returns current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(AppUser).filter(AppUser.username == username, AppUser.is_active == 1).first()
    if not user:
        raise credentials_exception

    return user


def get_current_admin(current_user: AppUser = Depends(get_current_user)) -> AppUser:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def ensure_admin_user_exists() -> None:
    """Create default admin user from environment settings if it does not exist."""
    db = SessionLocal()
    try:
        existing = db.query(AppUser).filter(AppUser.username == settings.ADMIN_USERNAME).first()
        if existing:
            if existing.role != "admin":
                existing.role = "admin"
                db.commit()
            return

        admin_user = AppUser(
            username=settings.ADMIN_USERNAME,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role="admin",
            is_active=1,
        )
        db.add(admin_user)
        db.commit()
    finally:
        db.close()
