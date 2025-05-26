"""Meeting transcript schemas for API request/response models."""

from typing import Any, Dict

from pydantic import BaseModel, Field

from app.core.base_model import (
	APIResponse,
	FilterableRequestSchema,
	PaginatedResponse,
	ResponseSchema,
)


class TranscriptCreate(BaseModel):
	"""Schema for creating a transcript"""

	content: Dict[str, Any]
	language: str | None = 'vi'
	token_usage: Dict[str, Any] | None = None


class TranscriptResponse(ResponseSchema):
	"""Response model for a transcript"""

	id: str = Field(description='Transcript unique identifier')
	meeting_id: str = Field(description='Meeting ID associated with the transcript')
	content: str = Field(description='Transcript content')
	language: str = Field(description='Language of the transcript')
	duration_seconds: int | None = Field(None, description='Duration of the transcript in seconds')
	word_count: int | None = Field(None, description='Word count of the transcript')
	status: str = Field(description='Processing status of the transcript')


class SearchTranscriptRequest(FilterableRequestSchema):
	"""Schema for searching transcripts with filters

	This model inherits from FilterableRequestSchema which provides:
	- Standard pagination (page, page_size)
	- Dynamic filtering through the 'filters' field
	- Backward compatibility through extra field support
	"""


class SearchTranscriptResponse(APIResponse):
	"""Response model for transcript search results"""

	data: PaginatedResponse[TranscriptResponse] | None = Field(None, description='Paginated transcript search results')
