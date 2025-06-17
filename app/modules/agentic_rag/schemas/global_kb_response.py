from app.core.base_model import ResponseSchema, APIResponse
from pydantic import ConfigDict
from typing import List, Optional


class GlobalKBResponse(ResponseSchema):
	model_config = ConfigDict(from_attributes=True)
	id: Optional[str] = None
	title: str
	content: str
	category: str
	tags: List[str]
	source: Optional[str] = None
	create_date: Optional[str] = None


class ListGlobalKBResponse(APIResponse):
	pass
