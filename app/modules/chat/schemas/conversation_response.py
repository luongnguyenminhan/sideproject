from typing import Optional
from pydantic import ConfigDict

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
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
