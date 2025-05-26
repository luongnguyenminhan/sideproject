"""Calendar schemas for API request/response models."""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from app.core.base_model import APIResponse, RequestSchema, ResponseSchema
from app.enums.calendar_enums import CalendarProviderEnum


class CalendarEvent(ResponseSchema):
	"""Base calendar event model"""

	id: str = Field(description='Event unique identifier')
	title: str = Field(description='Event title')
	description: str | None = None
	start_time: datetime
	end_time: datetime
	location: str | None = None
	meeting_id: str | None = None


class CalendarEventCreate(RequestSchema):
	"""Model for creating a calendar event"""

	title: str
	description: str | None = None
	start_time: datetime
	end_time: datetime
	location: str | None = None
	meeting_id: str | None = None


class CalendarIntegration(ResponseSchema):
	"""Calendar integration model"""

	id: str
	provider: str = Field(default=CalendarProviderEnum.GOOGLE.value)
	calendar_id: str | None = None


class CalendarSyncRequest(RequestSchema):
	"""Request model for calendar sync"""

	provider: str = Field(default=CalendarProviderEnum.GOOGLE.value)
	days_range: int | None = Field(default=365, ge=1, le=365)


class CalendarSyncStats(BaseModel):
	"""Statistics about calendar sync operation"""

	total: int = Field(description='Total number of events processed')
	processed: int = Field(description='Number of events successfully processed')
	meetings_created: int = Field(description='Number of meetings created')
	meetings_updated: int = Field(description='Number of meetings updated')
	meetings_linked: int = Field(description='Number of meetings linked to events')
	skipped: int = Field(description='Number of events skipped')
	errors: int = Field(description='Number of errors encountered')


class CalendarSyncResponse(APIResponse):
	"""Response model for calendar sync operation"""

	data: List[CalendarEvent] | None = None
	sync_stats: CalendarSyncStats | None = None


class CalendarResponse(APIResponse):
	"""Generic calendar response model"""

	data: List[CalendarEvent] | None = None
