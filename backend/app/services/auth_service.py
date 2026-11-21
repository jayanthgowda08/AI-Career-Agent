"""
services/auth_service.py — Authentication & Security Service

Handles:
1. Password hashing and verification using passlib (bcrypt).
2. JWT generation and decoding using python-jose.
3. FastAPI dependency for extracting and validating the authenticated user from the Bearer token.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User

# OAuth2 scheme extracts token from "Authorization: Bearer <token>" header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login-form")


# ============================================================
# Password Utilities (Native bcrypt with 72-byte handling)
# ============================================================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a stored bcrypt hash.
    Safely handles UTF-8 encoding and bcrypt's 72-byte input constraint.
    """
    try:
        password_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """
    Generates a secure bcrypt hash for a plain-text password with a unique salt.
    """
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


# ============================================================
# JWT Utilities
# ============================================================
def create_access_token(
    user_id: uuid.UUID,
    email: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Creates a signed JWT access token containing subject (user_id) and email.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decodes and cryptographically validates a JWT token.
    Raises HTTPException(401) if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_01_UNAUTHORIZED,
            detail="Could not validate credentials or token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================
# FastAPI Dependency: get_current_user
# ============================================================
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency that enforces authentication on protected endpoints.
    Extracts the Bearer token, validates it, and fetches the User from the database.
    """
    payload = decode_access_token(token)
    user_id_str: str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account.",
        )

    return user
