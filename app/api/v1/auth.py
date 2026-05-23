"""
Authentication routes.

POST /register  — create account
POST /login     — get JWT (form data for OAuth2 / Swagger Authorize button)
GET  /me        — current user (protected)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token, UserRegister, UserResponse
from app.services import auth_service
from app.utils.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new account",
)
async def register(
    body: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    existing = await auth_service.get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = await auth_service.create_user(db, body.email, body.password)
    return user


@router.post("/login", response_model=Token, summary="Login and receive JWT")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    OAuth2 password flow.

    Swagger sends `username` — we use that field for **email**.
    """
    user = await auth_service.authenticate_user(
        db,
        form_data.username,
        form_data.password,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user.id, settings)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse, summary="Current logged-in user")
async def read_current_user(
    current_user: User = Depends(get_current_user),
):
    """Protected route — requires Authorization: Bearer <token>."""
    return current_user
