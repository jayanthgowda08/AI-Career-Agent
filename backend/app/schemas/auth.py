"""
schemas/auth.py — Pydantic Schemas for Authentication
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegisterRequest(BaseModel):
    """Schema for incoming registration payload."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128, description="Password must be at least 8 characters.")


class UserLoginRequest(BaseModel):
    """Schema for JSON login payload."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT Token response returned upon successful authentication."""
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    email: EmailStr


class TokenPayload(BaseModel):
    """Decoded internal JWT payload."""
    sub: str  # user_id as string
    email: EmailStr
    exp: datetime


class UserResponse(BaseModel):
    """Safe user representation (no passwords)."""
    id: uuid.UUID
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
