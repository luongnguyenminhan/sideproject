from pydantic import Field
from app.core.base_model import RequestSchema
from typing import Optional


class SaveApiKeyRequest(RequestSchema):
	"""Request schema for saving API key"""

	provider: str = Field(..., description='AI service provider (openai, anthropic, etc.)')
	api_key: str = Field(..., description='API key for the service')
	is_default: bool = Field(default=False, description='Set as default API key for this provider')
	key_name: Optional[str] = Field(default=None, description='Optional name for the API key')
