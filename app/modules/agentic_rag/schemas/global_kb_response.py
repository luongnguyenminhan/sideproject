from app.core.base_model import ResponseSchema, APIResponse
from pydantic import ConfigDict
from typing import List, Optional


class GlobalKBResponse(ResponseSchema):
	model_config = ConfigDict(from_attributes=True)
	id: str
	title: str
	content: str
	category: str
	tags: List[str]
	source: Optional[str]
	create_date: str


class ListGlobalKBResponse(APIResponse):
	pass
