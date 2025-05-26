"""Group schemas for API request/response models"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

from app.core.base_model import (
	RequestSchema,
	ResponseSchema,
	PaginatedResponse,
	APIResponse,
	FilterableRequestSchema,
)
from app.modules.groups.models.group_member import (
	GroupMemberRole,
	GroupMemberJoinStatus,
)
from app.modules.users.schemas.users import UserResponse


# --- Group schemas ---


class GroupBase(BaseModel):
	"""Base schema for Group"""

	name: str = Field(..., description='Group name')
	description: Optional[str] = Field(None, description='Group description')
	is_public: bool = Field(False, description='Whether the group is public')


class GroupCreate(GroupBase):
	"""Schema for creating a new Group"""

	pass


class GroupUpdate(BaseModel):
	"""Schema for updating a Group"""

	name: Optional[str] = Field(None, description='Group name')
	description: Optional[str] = Field(None, description='Group description')
	is_public: Optional[bool] = Field(None, description='Whether the group is public')
	is_active: Optional[bool] = Field(None, description='Whether the group is active')


class GroupResponse(GroupBase, ResponseSchema):
	"""Schema for Group response"""

	id: str
	created_by: str
	create_date: datetime
	update_date: datetime
	is_active: bool

	class Config:
		from_attributes = True


class GroupFilter(RequestSchema):
	"""Schema for filtering Groups"""

	name: Optional[str] = Field(None, description='Filter by group name (partial match)')
	is_public: Optional[bool] = Field(None, description='Filter by public status')
	is_active: Optional[bool] = Field(None, description='Filter by active status')


class GroupPaginatedResponse(PaginatedResponse):
	"""Schema for paginated Group response"""

	items: List[GroupResponse]


# --- GroupMember schemas ---


class GroupMemberBase(BaseModel):
	"""Base schema for GroupMember"""

	group_id: str = Field(..., description='Group ID')
	user_id: str = Field(..., description='User ID')
	role: GroupMemberRole = Field(GroupMemberRole.MEMBER, description='Member role')


class GroupMemberCreate(GroupMemberBase):
	"""Schema for creating a new GroupMember"""

	join_status: GroupMemberJoinStatus = Field(GroupMemberJoinStatus.PENDING, description='Join status')
	invited_by: Optional[str] = Field(None, description='User ID of the inviter')


class GroupMemberUpdate(BaseModel):
	"""Schema for updating a GroupMember"""

	role: Optional[GroupMemberRole] = Field(None, description='Member role')
	join_status: Optional[GroupMemberJoinStatus] = Field(None, description='Join status')


class GroupMemberResponse(GroupMemberBase, ResponseSchema):
	"""Schema for GroupMember response"""

	id: str
	join_status: GroupMemberJoinStatus
	invited_by: Optional[str]
	invited_at: datetime
	responded_at: Optional[datetime]
	create_date: datetime
	update_date: datetime
	user_data: Optional[UserResponse] = Field(None, description='User data associated with the member')

	class Config:
		from_attributes = True


class GroupMemberFilter(RequestSchema):
	"""Schema for filtering GroupMembers"""

	role: Optional[GroupMemberRole] = Field(None, description='Filter by role')
	join_status: Optional[GroupMemberJoinStatus] = Field(None, description='Filter by join status')


class GroupMemberPaginatedResponse(PaginatedResponse):
	"""Schema for paginated GroupMember response"""

	items: List[GroupMemberResponse]


# --- Action schemas ---


class GroupInviteRequest(BaseModel):
	"""Schema for inviting a user to a group"""

	email: EmailStr = Field(..., description='Email of the user to invite')
	role: GroupMemberRole = Field(GroupMemberRole.MEMBER, description='Role for the invited user')


class GroupMemberActionRequest(BaseModel):
	"""Schema for GroupMember actions (accept/reject invitation)"""

	action: str = Field(..., description='Action to perform (accept or reject)')


# --- Combined schemas ---


class GroupWithMembersResponse(GroupResponse):
	"""Schema for Group response with member list"""

	members: Optional[List[GroupMemberResponse]] = Field([], description='Group members')


class GroupWithMembershipStatusResponse(GroupResponse):
	"""Schema for Group response including current user's membership status"""

	membership_status: Optional[GroupMemberJoinStatus] = Field(None, description="Current user's join status in this group")


class GroupWithMembershipDetailsResponse(GroupResponse):
	"""Schema for Group response including current user's membership status and role"""

	member_id: Optional[str] = Field(None, description="ID of the current user's membership record")
	member_role: Optional[GroupMemberRole] = Field(None, description="Current user's role in the group")
	join_status: Optional[GroupMemberJoinStatus] = Field(None, description="Current user's join status in the group")


class GroupWithMembershipDetailsPaginatedResponse(PaginatedResponse):
	"""Schema for paginated GroupWithMembershipDetailsResponse response"""

	items: List[GroupWithMembershipDetailsResponse]


# --- Search schemas ---


class SearchGroupRequest(FilterableRequestSchema):
	"""Schema for searching groups with filters and pagination"""

	pass


class SearchGroupResponse(APIResponse):
	"""Response model for group search results"""

	data: Optional[PaginatedResponse[GroupWithMembershipDetailsResponse]] = Field(None, description='Paginated group search results with membership details')
