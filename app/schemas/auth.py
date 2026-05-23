"""Request/response shapes for authentication endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """Body for POST /auth/register"""

    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
        description="At least 8 characters",
    )


class UserLogin(BaseModel):
    """Optional JSON login — Swagger also supports OAuth2 form on /auth/login"""

    email: EmailStr
    password: str


class Token(BaseModel):
    """OAuth2-style token response"""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Safe user data — never includes hashed_password"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime
