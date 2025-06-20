from app.core.base_model import ResponseSchema, APIResponse
from pydantic import ConfigDict, field_serializer
from typing import List, Optional, Union
from datetime import datetime


class GlobalKBResponse(ResponseSchema):
	model_config = ConfigDict(from_attributes=True)
	id: Optional[str] = None
	title: str
	file_name: str
	file_type: Optional[str] = None
	category: str
	source: Optional[str] = None  # MinIO URL
	indexed: bool = False
	index_status: str = 'pending'
	create_date: Optional[Union[str, datetime]] = None
	update_date: Optional[Union[str, datetime]] = None

	@field_serializer('create_date', 'update_date', when_used='always')
	def serialize_datetime(self, value, _info):
		if isinstance(value, datetime):
			return value.isoformat()
		return value


class ListGlobalKBResponse(APIResponse):
	pass
