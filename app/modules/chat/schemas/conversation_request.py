from pydantic import Field, BaseModel
from app.core.base_model import RequestSchema, FilterableRequestSchema
from typing import Optional


class CreateConversationRequest(RequestSchema):
	"""Request schema for creating a conversation"""

	name: str = Field(..., min_length=1, max_length=255, description='Conversation name')
	initial_message: Optional[str] = Field(default=None, description='Initial message (optional)')
	system_prompt: Optional[str] = Field(default=None, description='Custom system prompt for this conversation')


class UpdateConversationRequest(RequestSchema):
	"""Request schema for updating a conversation"""

	name: Optional[str] = Field(default=None, min_length=1, max_length=255, description='New conversation name')
	system_prompt: Optional[str] = Field(default=None, description='Custom system prompt for this conversation')


class ConversationListRequest(FilterableRequestSchema):
	"""Request schema for listing conversations"""

	search: Optional[str] = Field(default=None, description='Search by conversation name')
	order_by: Optional[str] = Field(default='last_activity', description='Sort by field')
	order_direction: Optional[str] = Field(default='desc', description='Sort direction: asc/desc')


class CountConversationsRequest(BaseModel):
	"""Request model for counting conversations with optional filters"""
	
	filters: list = Field(
		default=[],
		description='Optional filters to apply when counting conversations'
	)
	include_user_filter: bool = Field(
		default=True,
		description='Whether to filter conversations for current user only'
	)
