from pydantic import BaseModel, validator
from typing import Optional
from app.core.base_model import RequestSchema


class ConversationChatRequest(RequestSchema):
	"""Request schema for conversation-based chat execution"""

	message: str
	conversation_id: str
	system_prompt: Optional[str] = None  # Conversation-specific system prompt
	streaming: Optional[bool] = True

	@validator('message')
	def message_must_not_be_empty(cls, v):
		if not v or not v.strip():
			raise ValueError('Message cannot be empty')
		return v.strip()


class UpdateSystemAgentRequest(RequestSchema):
	"""Request schema for updating system agent configuration"""

	model_name: Optional[str] = None
	temperature: Optional[float] = None
	max_tokens: Optional[int] = None
	default_system_prompt: Optional[str] = None
	tools_config: Optional[dict] = None

	@validator('temperature')
	def temperature_range(cls, v):
		if v is not None and not 0 <= v <= 2:
			raise ValueError('Temperature must be between 0 and 2')
		return v

	@validator('max_tokens')
	def max_tokens_range(cls, v):
		if v is not None and not 1 <= v <= 1000000:
			v = 1000000  # Cap max tokens to a reasonable limit
		return v


class UpdateSystemAgentApiKeyRequest(RequestSchema):
	"""Request schema for updating system agent API key"""

	api_key: str
	api_provider: Optional[str] = 'google'

	@validator('api_key')
	def api_key_must_not_be_empty(cls, v):
		if not v or not v.strip():
			raise ValueError('API key cannot be empty')
		return v.strip()


class ValidateSystemAgentRequest(RequestSchema):
	"""Request schema for system agent validation"""

	test_message: Optional[str] = 'Hello, how are you?'
	override_api_key: Optional[str] = None
