"""
api/auth.py — Authentication Endpoints

Provides:
- POST /api/auth/register : Register a new user and auto-create an empty CandidateProfile
- POST /api/auth/login    : JSON-based login returning a signed JWT token
- POST /api/auth/login-form : Swagger-compatible OAuth2 password form login
- GET  /api/auth/me       : Return currently authenticated user info
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.profile import CandidateProfile
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    Token,
    UserResponse,
)
from app.services.auth_service import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Registers a new user:
    1. Checks if the email is already in use.
    2. Hashes the password using bcrypt.
    3. Creates the user record.
    4. Automatically initializes an empty CandidateProfile linked to the user.
    5. Returns an access token so the user is immediately logged in.
    """
    existing_user = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Create User
    new_user = User(
        email=payload.email.lower(),
        hashed_password=get_password_hash(payload.password),
    )
    db.add(new_user)
    db.flush()  # Flush to populate new_user.id for profile creation

    # Create linked empty profile
    initial_profile = CandidateProfile(user_id=new_user.id)
    db.add(initial_profile)
    db.commit()
    db.refresh(new_user)

    # Generate Token
    access_token = create_access_token(user_id=new_user.id, email=new_user.email)
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=new_user.id,
        email=new_user.email,
    )


@router.post(
    "/login",
    response_model=Token,
    summary="User login with JSON payload",
)
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticates a user via JSON body (for React frontend):
    1. Finds user by email.
    2. Verifies the bcrypt hash.
    3. Returns signed JWT token.
    """
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    access_token = create_access_token(user_id=user.id, email=user.email)
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
    )


@router.post(
    "/login-form",
    response_model=Token,
    include_in_schema=True,
    summary="OAuth2 compatible form login (for Swagger UI 'Authorize' button)",
)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    OAuth2 form login compatible with the 'Authorize' button on Swagger UI.
    Uses 'username' field for email.
    """
    user = db.query(User).filter(User.email == form_data.username.lower()).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user_id=user.id, email=user.email)
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user info",
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    """Returns the profile info for the currently authenticated user."""
    return current_user
