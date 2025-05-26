"""
Meeting note schemas for API request/response models.
"""

from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from app.core.base_model import (
	FilterableRequestSchema,
)


class MeetingItemResponse(BaseModel):
	"""Response model for a meeting item"""

	id: str = Field(description='Item unique identifier')
	meeting_note_id: str = Field(description='ID of the meeting note this item belongs to')
	type: str = Field(description='Type of the item (decision, action_item, question)')
	content: Dict[str, Any] = Field(description='Content of the item')
	create_date: datetime = Field(description='Creation timestamp')
	update_date: datetime = Field(description='Last update timestamp')


class MeetingNoteResponse(BaseModel):
	"""Response model for a meeting note"""

	id: str = Field(description='Note unique identifier')
	meeting_id: str = Field(description='ID of the meeting this note belongs to')
	transcript_id: str = Field(description='ID of the transcript this note was generated from')
	content: Dict[str, Any] = Field(description='Content of the note')
	version: int = Field(description='Version number of the note')
	is_latest: bool = Field(description='Indicates if this is the latest version of the note')
	is_encrypted: bool = Field(description='Indicates if the note content is encrypted')
	encryption_key: str | None = Field(None, description='Encryption key for note content')
	create_date: datetime = Field(description='Creation timestamp')
	update_date: datetime = Field(description='Last update timestamp')
	items: List[MeetingItemResponse] | None = Field(None, description='Meeting items in this note')


class SearchMeetingNoteRequest(FilterableRequestSchema):
	"""Schema for searching meeting notes with filters

	This model inherits from FilterableRequestSchema which provides:
	- Standard pagination (page, page_size)
	- Dynamic filtering through the 'filters' field
	"""


class AttendeesRequest(BaseModel):
	"""Schema for meeting attendees"""

	emails: List[str] = Field(
		description='List of email addresses of attendees',
		example=[
			'attendee1@example.com',
			'attendee2@example.com',
			'attendee3@example.com',
			'attendee4@example.com',
		],
	)
