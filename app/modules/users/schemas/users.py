"""
User Request and Response Schemas for Google OAuth
"""

from datetime import datetime
from typing import List

from fastapi import Body
from pydantic import BaseModel, EmailStr, Field

from app.core.base_model import (
    APIResponse,
    FilterableRequestSchema,
    PaginatedResponse,
    RequestSchema,
    ResponseSchema,
)
from app.enums.user_enums import UserRoleEnum
from app.middleware.translation_manager import _


class UserResponse(ResponseSchema):
    """User info Response model"""

    id: str = Field(
        ...,
        description='User ID',
        examples=['d9fc5dc0-e4b7-4a7d-83a1-7dda5fed129b'],
    )
    email: str = Field(..., description='Email address', examples=['abc@gmail.com'])
    role: str = Field(..., description='Role', examples=['user'])
    name: str | None = Field(default=None, description='Full name', examples=['John Doe'])
    username: str = Field(..., description='Username', examples=['johndoe'])
    confirmed: bool = Field(..., description='Account verification status', examples=[True])
    create_date: datetime | None = Field(default=None, description='Creation date', examples=['2024-09-01 15:00:00'])
    update_date: datetime | None = Field(default=None, description='Update date', examples=['2024-09-01 15:00:00'])
    profile_picture: str | None = Field(
        default=None,
        description='Profile picture URL',
        examples=['https://example.com/image.jpg'],
    )
    first_name: str | None = Field(default=None, description='First name', examples=['John'])
    last_name: str | None = Field(default=None, description='Last name', examples=['Doe'])
    locale: str | None = Field(default=None, description='Locale', examples=['en'])
    google_id: str | None = Field(default=None, description='Google User ID', examples=['10987654321'])
    access_token: str | None = Body(default=None, description='Access token', examples=['xaasvwewe'])
    refresh_token: str | None = Body(default=None, description='Refresh token', examples=['xaasvwewe'])
    token_type: str | None = Body(default=None, description='Token type', examples=['bearer'])


class SearchUserRequest(FilterableRequestSchema):
    """SearchUserRequest - Provides dynamic search filters for users"""

class RefreshTokenRequest(RequestSchema):
	"""RefreshTokenRequest"""

	refresh_token: str = Field(..., description='Refresh token')

class SearchUserResponse(APIResponse):
    """SearchUserResponse"""

    data: PaginatedResponse[UserResponse] | None


class GoogleDirectLoginRequest(BaseModel):
    """Request model for direct Google OAuth login (used by mobile apps)"""

    access_token: str
    id_token: str | None = None
    refresh_token: str | None = None
    expires_in: int | None = None
    token_type: str | None = None
    scope: str | None = None


class GoogleRevokeTokenRequest(BaseModel):
    """Request model for revoking Google OAuth token"""

    token: str


class GoogleLoginResponse(APIResponse):
    """Response model for Google OAuth login"""

    data: UserResponse | None = None


class OAuthUserInfo(BaseModel):
    """OAuth user information model"""

    email: str
    name: str | None = None
    picture: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    locale: str | None = None
    sub: str  # OAuth subject/user id
    granted_scopes: List[str] | None = None  # List of scopes granted by the user
