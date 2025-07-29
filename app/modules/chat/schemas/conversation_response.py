from typing import Optional
from pydantic import ConfigDict, Field
from app.core.base_model import ResponseSchema, PaginatedResponse
from datetime import datetime


class ConversationResponse(ResponseSchema):
	"""Response schema for conversation information"""

	model_config = ConfigDict(from_attributes=True)

	id: str
	name: str
	message_count: int
	last_activity: datetime
	create_date: datetime
	update_date: Optional[datetime]
	system_prompt: Optional[str]


class CountConversationsResponse(ResponseSchema):
	"""Count conversations response model"""
	
	total_count: int = Field(..., description='Total number of conversations', examples=[75])
