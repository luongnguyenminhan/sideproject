"""
Group Request and Response Schemas
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum

from fastapi import Body
from pydantic import BaseModel, Field, validator

from app.core.base_model import (
    APIResponse,
    FilterableRequestSchema,
    PaginatedResponse,
    RequestSchema,
    ResponseSchema,
)
from app.enums.group_enums import GroupMemberRoleEnum, GroupRequestType, GroupRequestStatus
from app.middleware.translation_manager import _


class GroupResponse(ResponseSchema):
    """Group info Response model"""

    group_id: str = Field(
        ...,
        description='Group ID',
        examples=['d9fc5dc0-e4b7-4a7d-83a1-7dda5fed129b'],
    )
    group_name: str = Field(..., description='Group name', examples=['Developers'])
    group_picture: str | None = Field(default=None, description='Group picture URL', examples=['https://example.com/group.jpg'])
    leader: str = Field(..., description='Leader ID', examples=['leader-user-id'])
    created_at: datetime | None = Field(default=None, description='Creation date', examples=['2024-09-01 15:00:00'])
    members_count: int = Field(..., description='Number of group members', examples=[10])


# Group CRUD Schemas
class GroupCreate(BaseModel):
    """Schema for creating a new group"""
    group_name: str = Field(..., min_length=1, max_length=100, description="Group name")
    group_picture: Optional[str] = Field(None, max_length=255, description="Group profile picture URL")
    
    @validator('group_name')
    def validate_group_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Group name cannot be empty')
        return v.strip()


class GroupUpdate(BaseModel):
    """Schema for updating group information"""
    group_name: Optional[str] = Field(None, min_length=1, max_length=100)
    group_picture: Optional[str] = Field(None, max_length=255)
    
    @validator('group_name')
    def validate_group_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Group name cannot be empty')
        return v.strip() if v else v


# Group Member Schemas
class GroupMemberResponse(ResponseSchema):
    """Group member response schema"""
    id: str = Field(..., description="Member ID")
    group_id: str = Field(..., description="Group ID")
    user_id: str = Field(..., description="User ID")
    nickname: Optional[str] = Field(None, description="Nickname in the group")
    role: GroupMemberRoleEnum = Field(..., description="Member role")
    invited_by: Optional[str] = Field(None, description="ID of who invited this member")
    created_at: datetime = Field(..., description="Join date")


class InviteMemberRequest(RequestSchema):
    """Schema for inviting a member to group"""
    user_id: str = Field(..., description="ID of user to invite")
    message: Optional[str] = Field(None, max_length=500, description="Invitation message")


class JoinGroupRequest(RequestSchema):
    """Schema for requesting to join group"""
    message: Optional[str] = Field(None, max_length=500, description="Join request message")


class ApproveRequestRequest(RequestSchema):
    """Schema for approving a group request"""
    nickname: Optional[str] = Field(None, max_length=255, description="Nickname for the new member")


class UpdateNicknameRequest(RequestSchema):
    """Schema for updating nickname in group"""
    nickname: str = Field(..., min_length=1, max_length=255, description="New nickname")
    
    @validator('nickname')
    def validate_nickname(cls, v):
        if not v or not v.strip():
            raise ValueError('Nickname cannot be empty')
        return v.strip()


# Group Request Schemas
class GroupRequestResponse(ResponseSchema):
    """Group request response schema"""
    id: str = Field(..., description="Request ID")
    group_id: str = Field(..., description="Group ID")
    user_id: str = Field(..., description="User ID")
    request_type: GroupRequestType = Field(..., description="Request type")
    status: GroupRequestStatus = Field(..., description="Request status")
    message: Optional[str] = Field(None, description="Request message")
    requested_by: Optional[str] = Field(None, description="ID of who created the request")
    requested_at: datetime = Field(..., description="Request creation time")
    processed_at: Optional[datetime] = Field(None, description="Request processing time")
    processed_by: Optional[str] = Field(None, description="ID of who processed the request")


# Search and Filter Schemas
class SearchGroupRequest(FilterableRequestSchema):
    """SearchGroupRequest - Provides dynamic search filters for groups"""
    search: Optional[str] = Field(None, description="Search term for group name")
    leader_id: Optional[str] = Field(None, description="Filter by leader ID")


class GroupMemberFilter(BaseModel):
    """Schema for group member filters"""
    role: Optional[GroupMemberRoleEnum] = Field(None, description="Filter by member role")
    search: Optional[str] = Field(None, description="Search term for user or nickname")


class GroupRequestFilter(BaseModel):
    """Schema for group request filters"""
    request_type: Optional[GroupRequestType] = Field(None, description="Filter by request type")
    status: Optional[GroupRequestStatus] = Field(None, description="Filter by request status")


# Response Schemas
class SearchGroupResponse(APIResponse):
    """SearchGroupResponse"""
    data: PaginatedResponse[GroupResponse] | None


class GroupDetailResponse(APIResponse):
    """GroupDetailResponse"""
    data: GroupResponse | None = None


class GroupMembersResponse(APIResponse):
    """Group members list response"""
    data: List[GroupMemberResponse] | None = None


class GroupRequestsResponse(APIResponse):
    """Group requests list response"""
    data: List[GroupRequestResponse] | None = None


class GroupActionResponse(APIResponse):
    """Generic group action response"""
    message: str = Field(..., description="Action result message")


class CreateGroupResponse(APIResponse):
    """Create group response"""
    data: GroupResponse | None = None
    message: str = Field(default="Group created successfully")


class InviteMemberResponse(APIResponse):
    """Invite member response"""
    data: GroupRequestResponse | None = None
    message: str = Field(default="Invitation sent successfully")


class JoinRequestResponse(APIResponse):
    """Join request response"""
    data: GroupRequestResponse | None = None
    message: str = Field(default="Join request sent successfully")


class ApproveRequestResponse(APIResponse):
    """Approve request response"""
    data: GroupMemberResponse | None = None
    message: str = Field(default="Request approved successfully")


class UpdateNicknameResponse(APIResponse):
    """Update nickname response"""
    data: GroupMemberResponse | None = None
    message: str = Field(default="Nickname updated successfully")


# Legacy schemas (giữ lại để tương thích)
class CreateGroupRequest(RequestSchema):
    """CreateGroupRequest - Legacy schema"""
    group_name: str = Field(..., description='Group name')
    group_picture: str | None = Field(default=None, description='Group picture URL')


class UpdateGroupRequest(RequestSchema):
    """UpdateGroupRequest - Legacy schema"""
    group_name: str | None = Field(default=None, description='Group name')
    group_picture: str | None = Field(default=None, description='Group picture URL')


# Bulk Operation Schemas
class BulkInviteRequest(RequestSchema):
    """Schema for bulk inviting members"""
    user_ids: List[str] = Field(..., min_items=1, max_items=50, description="List of user IDs to invite")
    message: Optional[str] = Field(None, max_length=500, description="Invitation message")


class BulkInviteResponse(APIResponse):
    """Bulk invite response"""
    data: List[GroupRequestResponse] | None = None
    successful_count: int = Field(default=0, description="Number of successful invitations")
    failed_count: int = Field(default=0, description="Number of failed invitations")
    message: str = Field(default="Bulk invitation completed")


# Statistics Schema
class GroupStatsResponse(ResponseSchema):
    """Group statistics response"""
    total_members: int = Field(..., description="Total number of members")
    total_leaders: int = Field(..., description="Total number of leaders")
    pending_requests: int = Field(..., description="Number of pending requests")
    recent_joins: int = Field(..., description="Number of members joined in last 30 days")