from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field
from app.core.base_model import ResponseSchema
from app.modules.chat.models.message import MessageRole


class MessageResponse(ResponseSchema):
	"""Response schema for message data - prevents recursion issues"""

	id: str = Field(..., description='Message ID')
	conversation_id: str = Field(..., description='Conversation ID')
	user_id: str = Field(..., description='User ID')
	role: MessageRole = Field(..., description='Message role')
	content: str = Field(..., description='Message content')
	timestamp: datetime = Field(..., description='Message timestamp')
	model_used: Optional[str] = Field(None, description='AI model used')
	tokens_used: Optional[str] = Field(None, description='Tokens used')
	response_time_ms: Optional[str] = Field(None, description='Response time in milliseconds')
	create_date: datetime = Field(..., description='Created date')
	update_date: Optional[datetime] = Field(None, description='Updated date')
	is_deleted: bool = Field(False, description='Is deleted flag')

	@classmethod
	def from_message(cls, message) -> 'MessageResponse':
		"""Create MessageResponse from Message model without triggering relationships"""
		return cls(
			id=message.id,
			conversation_id=message.conversation_id,
			user_id=message.user_id,
			role=message.role,
			content=message.content,
			timestamp=message.timestamp,
			model_used=message.model_used,
			tokens_used=message.tokens_used,
			response_time_ms=message.response_time_ms,
			create_date=message.create_date,
			update_date=message.update_date,
			is_deleted=message.is_deleted,
		)


class MessageListResponse(ResponseSchema):
	"""Response schema for message list"""

	messages: List[MessageResponse] = Field(default=[], description='List of messages')
	total_count: int = Field(0, description='Total message count')
	page: int = Field(1, description='Current page')
	page_size: int = Field(50, description='Page size')
	total_pages: int = Field(0, description='Total pages')
