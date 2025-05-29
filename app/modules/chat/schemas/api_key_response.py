from pydantic import ConfigDict
from app.core.base_model import ResponseSchema
from datetime import datetime
from typing import List


class ApiKeyResponse(ResponseSchema):
	"""Response schema for API key information"""

	model_config = ConfigDict(from_attributes=True)

	id: str
	provider: str
	masked_key: str
	is_default: bool
	key_name: str
	create_date: datetime
