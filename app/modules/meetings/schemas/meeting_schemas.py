"""
Meeting schemas for API request/response models.
"""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from app.core.base_model import (
	FilterableRequestSchema,
	RequestSchema,
)


class MeetingResponse(BaseModel):
	id: str = Field(description='Meeting unique identifier')
	user_id: str = Field(description='ID of the user who created the meeting')
	title: str = Field(description='Title of the meeting')
	description: str | None = Field(None, description='Detailed description of the meeting')
	meeting_date: datetime = Field(description='Date and time of the meeting')
	duration_seconds: int | None = Field(None, description='Duration of the meeting in seconds')
	meeting_type: str | None = Field(None, description='Type of the meeting')
	status: str = Field(description='Current status of the meeting')
	is_encrypted: bool = Field(description='Indicates if the meeting content is encrypted')
	is_recurring: bool = Field(default=False, description='Indicates if the meeting is recurring')
	language: str = Field(default='vi', description='Language of the meeting')
	platform: str | None = Field(None, description='Platform where the meeting is hosted')
	meeting_link: str | None = Field(None, description='Link to join the meeting')
	organizer_email: str | None = Field(None, description='Email of the meeting organizer')
	organizer_name: str | None = Field(None, description='Name of the meeting organizer')
	last_joined_at: datetime | None = Field(None, description='Last time user joined the meeting')


class MeetingCreate(RequestSchema):
	title: str = Field(description='Title of the meeting')
	description: str | None = Field(None, description='Detailed description of the meeting')
	meeting_date: datetime = Field(description='Date and time of the meeting')
	duration_seconds: int | None = Field(None, description='Duration of the meeting in seconds')
	meeting_type: str | None = Field(None, description='Type of the meeting')
	status: str | None = Field(None, description='Current status of the meeting')
	is_encrypted: bool | None = Field(False, description='Indicates if the meeting content is encrypted')
	encryption_key: str | None = Field(None, description='Encryption key for meeting content')
	is_recurring: bool | None = Field(False, description='Indicates if the meeting is recurring')
	language: str | None = Field('vi', description='Language of the meeting')
	tags: List[str] | None = Field([], description='Tags associated with the meeting')


class MeetingUpdate(RequestSchema):
	title: str | None = Field(None, description='Title of the meeting')
	description: str | None = Field(None, description='Detailed description of the meeting')
	meeting_date: datetime | None = Field(None, description='Date and time of the meeting')
	duration_seconds: int | None = Field(None, description='Duration of the meeting in seconds')
	meeting_type: str | None = Field(None, description='Type of the meeting')
	status: str | None = Field(None, description='Current status of the meeting')
	is_encrypted: bool | None = Field(None, description='Indicates if the meeting content is encrypted')
	encryption_key: str | None = Field(None, description='Encryption key for meeting content')
	is_recurring: bool | None = Field(None, description='Indicates if the meeting is recurring')
	language: str | None = Field(None, description='Language of the meeting')
	tags: List[str] | None = Field(None, description='Tags associated with the meeting')


class JoinMeetingRequest(RequestSchema):
	title: str = Field(description='Title of the meeting being joined')
	platform: str = Field(description='Platform where the meeting is hosted')
	timestamp: datetime = Field(description='Time when the user joined the meeting')
	url: str = Field(description='URL of the meeting')
	group_id: str | None = Field(None, description='Optional group ID for group meetings')


class SearchMeetingRequest(FilterableRequestSchema):
	"""Schema for searching meetings with filters

	This model inherits from FilterableRequestSchema which provides:
	- Standard pagination (page, page_size)
	- Dynamic filtering through the 'filters' field
	- Backward compatibility through extra field support
	"""
