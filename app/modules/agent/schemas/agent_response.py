from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.core.base_model import ResponseSchema, APIResponse
from app.modules.agent.models.agent import ModelProvider


class SystemAgentResponse(ResponseSchema):
	"""Response schema for system agent (with embedded config)"""

	model_config = ConfigDict(from_attributes=True)

	id: str
	name: str
	description: Optional[str] = None
	is_active: bool
	model_provider: ModelProvider
	model_name: str
	temperature: float
	max_tokens: Optional[int] = None
	default_system_prompt: Optional[str] = None
	tools_config: Optional[Dict[str, Any]] = None
	api_provider: str
	has_api_key: bool = False  # Don't expose actual API key
	create_date: Optional[datetime] | Optional[str] = None
	update_date: Optional[datetime] | Optional[str] = None


class ConversationChatResponse(BaseModel):
	"""Response schema for conversation chat execution"""

	content: str
	metadata: Dict[str, Any]
	conversation_id: str
	execution_time_ms: int
	tokens_used: Optional[int] = None
	model_used: str


class ModelInfo(BaseModel):
	"""Response schema for model information"""

	provider: str
	models: List[str]


class AvailableModelsResponse(BaseModel):
	"""Response schema for available models"""

	providers: List[ModelInfo]


class SystemAgentValidationResponse(BaseModel):
	"""Response schema for system agent validation"""

	is_valid: bool
	test_response: Optional[str] = None
	error_message: Optional[str] = None
	execution_time_ms: Optional[int] = None


# Compound responses using APIResponse
class ConversationChatExecutionResponse(APIResponse):
	"""Response for conversation chat execution"""

	pass


class GetSystemAgentResponse(APIResponse):
	"""Response for getting system agent"""

	pass


class UpdateSystemAgentResponse(APIResponse):
	"""Response for updating system agent"""

	pass


class UpdateSystemAgentApiKeyResponse(APIResponse):
	"""Response for updating system agent API key"""

	pass


class GetModelsResponse(APIResponse):
	"""Response for getting available models"""

	pass


class ValidateSystemAgentResponse(APIResponse):
	"""Response for system agent validation"""

	pass
