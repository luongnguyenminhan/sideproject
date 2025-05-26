"""Meeting tag schemas for API request/response models."""

from pydantic import Field

from app.core.base_model import (
	APIResponse,
	FilterableRequestSchema,
	PaginatedResponse,
	RequestSchema,
	ResponseSchema,
)


class TagResponse(ResponseSchema):
	"""Response model for a tag"""

	id: str = Field(description='Tag unique identifier')
	user_id: str = Field(description='ID of the user who created the tag')
	name: str = Field(description='Name of the tag')
	is_system: bool = Field(description='Whether this is a system tag')


class TagCreate(RequestSchema):
	"""Request model for creating a tag"""

	name: str = Field(description='Name of the tag')
	is_system: bool | None = Field(False, description='Whether this is a system tag')


class SearchTagRequest(FilterableRequestSchema):
	"""Schema for searching tags with filters

	This model inherits from FilterableRequestSchema which provides:
	- Standard pagination (page, page_size)
	- Dynamic filtering through the 'filters' field
	- Backward compatibility through extra field support
	"""


class SearchTagResponse(APIResponse):
	"""Response model for tag search results"""

	data: PaginatedResponse[TagResponse] | None = Field(None, description='Paginated tag search results')


class TagUpdate(RequestSchema):
	"""Request model for updating a tag"""

	name: str | None = Field(None, description='Name of the tag')
	is_system: bool | None = Field(None, description='Whether this is a system tag')
