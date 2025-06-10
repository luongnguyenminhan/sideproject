"""
Group Request and Response Schemas
"""

from datetime import datetime
from typing import List

from fastapi import Body
from pydantic import BaseModel, Field

from app.core.base_model import (
    APIResponse,
    FilterableRequestSchema,
    PaginatedResponse,
    RequestSchema,
    ResponseSchema,
)
from app.middleware.translation_manager import _


class GroupResponse(ResponseSchema):
    """Group info Response model"""

    group_id: int = Field(
        ...,
        description='Group ID',
        examples=[1],
    )
    group_name: str = Field(..., description='Group name', examples=['Developers'])
    group_picture: str | None = Field(default=None, description='Group picture URL', examples=['https://example.com/group.jpg'])
    leader: str = Field(..., description='Leader email', examples=['leader@example.com'])
    create_at: datetime | None = Field(default=None, description='Creation date', examples=['2024-09-01 15:00:00'])
    members_count: int = Field(..., description='Number of group members', examples=[10])


class SearchGroupRequest(FilterableRequestSchema):
    """SearchGroupRequest - Provides dynamic search filters for groups"""


class CreateGroupRequest(RequestSchema):
    """CreateGroupRequest"""

    group_name: str = Field(..., description='Group name')
    group_picture: str | None = Field(default=None, description='Group picture URL')
    leader: str = Field(..., description='Leader email')


class UpdateGroupRequest(RequestSchema):
    """UpdateGroupRequest"""

    group_name: str | None = Field(default=None, description='Group name')
    group_picture: str | None = Field(default=None, description='Group picture URL')
    leader: str | None = Field(default=None, description='Leader email')


class SearchGroupResponse(APIResponse):
    """SearchGroupResponse"""

    data: PaginatedResponse[GroupResponse] | None


class GroupDetailResponse(APIResponse):
    """GroupDetailResponse"""

    data: GroupResponse | None = None