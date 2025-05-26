"""Token usage schemas"""

from pydantic import BaseModel, Field


class TokenUsageAnalyticsResponse(BaseModel):
	"""Token usage analytics response model"""

	operation_type: str = Field(..., description='Type of operation (summarization, transcription, etc.)')
	input_tokens: int = Field(..., description='Number of input tokens used')
	output_tokens: int = Field(..., description='Number of output tokens generated')
	context_tokens: int = Field(..., description='Number of context tokens used')
	total_tokens: int = Field(..., description='Total number of tokens used')
	total_price_vnd: float = Field(..., description='Total price in VND')
	usage_count: int = Field(..., description='Number of operations performed')
	average_tokens: float = Field(..., description='Average tokens per operation')


class TokenUsageSummaryResponse(BaseModel):
	"""Token usage summary response model"""

	total_input_tokens: int = Field(..., description='Total input tokens used')
	total_output_tokens: int = Field(..., description='Total output tokens generated')
	total_context_tokens: int = Field(..., description='Total context tokens used')
	total_price_vnd: float = Field(..., description='Total price in VND')


class UserTokenUsageSummary(TokenUsageSummaryResponse):
	"""User token usage summary with user information"""

	user_id: str = Field(..., description='User ID')
	email: str = Field(..., description='User email')
	name: str | None = Field(None, description='User name')
