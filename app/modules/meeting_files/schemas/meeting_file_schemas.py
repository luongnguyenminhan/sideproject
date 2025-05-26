"""
Meeting file schemas for API request/response models.
"""

from datetime import datetime

from pydantic import Field

from app.core.base_model import (
	APIResponse,
	FilterableRequestSchema,
	PaginatedResponse,
	ResponseSchema,
)


class MeetingFileResponse(ResponseSchema):
	"""Response model for a meeting file"""

	id: str = Field(description='File unique identifier')
	meeting_id: str = Field(description='Meeting ID associated with the file')
	file_name: str = Field(description='Original filename')
	file_type: str = Field(description='MIME type of the file')
	file_size: int = Field(description='Size of the file in bytes')
	upload_date: datetime = Field(description='Date when the file was uploaded')
	file_url: str | None = Field(None, description='URL to access the file')
	object_name: str | None = Field(None, description='Object name in storage')
	processing_status: str | None = Field(None, description='Processing status of the file')


class SearchMeetingFileRequest(FilterableRequestSchema):
	"""Schema for searching meeting files with filters

	This model inherits from FilterableRequestSchema which provides:
	- Standard pagination (page, page_size)
	- Dynamic filtering through the 'filters' field
	- Backward compatibility through extra field support

	Legacy filter fields are kept for backward compatibility:
	"""

	meeting_id: str | None = Field(None, description='Filter by meeting ID')
	file_name: str | None = Field(None, description='Filter by file name')
	file_type: str | None = Field(None, description='Filter by file type')
	upload_date_from: datetime | None = Field(None, description='Filter by upload date (from)')
	upload_date_to: datetime | None = Field(None, description='Filter by upload date (to)')


class SearchMeetingFileResponse(APIResponse):
	"""Response model for meeting file search results"""

	data: PaginatedResponse[MeetingFileResponse] | None = Field(None, description='Paginated meeting file search results')


class FileUploadResponse(APIResponse):
	"""Response model for file upload results"""

	data: MeetingFileResponse | None = Field(None, description='Uploaded file details')
