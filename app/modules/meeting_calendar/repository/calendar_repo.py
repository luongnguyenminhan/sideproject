"""Calendar repository for calendar events management"""

import logging
from typing import Any, Dict, List

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.base_repo import BaseRepo
from app.core.database import get_db
from app.modules.meeting_calendar.adapters.google_calendar_adapter import (
	GoogleCalendarAdapter,
)
from app.modules.meeting_calendar.dal.calendar_dal import (
	CalendarEventDAL,
	CalendarIntegrationDAL,
)
from app.modules.meeting_calendar.models.calendar import (
	CalendarEvent,
)
from app.modules.users.models.users import User

logger = logging.getLogger(__name__)


class CalendarRepo(BaseRepo):
	"""Repository for calendar operations"""

	def __init__(self, db: Session = Depends(get_db)):
		"""Initialize CalendarRepo

		Args:
		    db (Session): Database session
		"""
		self.db = db
		self.calendar_event_dal = CalendarEventDAL(db)
		self.calendar_integration_dal = CalendarIntegrationDAL(db)

	def get_calendar_events(self, user: User, days: int = 30) -> List[Dict[str, Any]]:
		"""Get calendar events for syncing with meetings

		This method returns raw event dictionaries from the provider for syncing purposes.

		Args:
		    user (User): User to get calendar events for
		    days (int): Number of days to fetch events for

		Returns:
		    List[Dict[str, Any]]: List of raw calendar events
		"""
		try:
			# Currently only handling Google Calendar
			adapter = GoogleCalendarAdapter(user)
			return adapter.list_events(days)
		except Exception as ex:
			logger.error(f'Failed to get calendar events: {ex}')
			return []

	def get_calendar_event_objects(self, user: User, days: int = 30) -> List[CalendarEvent]:
		"""Get calendar events as response objects

		This method returns CalendarEvent objects for API responses.

		Args:
		    user (User): User to get calendar events for
		    days (int): Number of days to fetch events for

		Returns:
		    List[CalendarEvent]: List of calendar events as response objects
		"""
		try:
			# Currently only handling Google Calendar
			adapter = GoogleCalendarAdapter(user)
			return adapter.get_calendar_event_objects(days)
		except Exception as ex:
			logger.error(f'Failed to get calendar event objects: {ex}')
			return []

	def create_event_in_calendar(self, user: User, event_data: Dict[str, Any]) -> CalendarEvent | None:
		"""Create a calendar event

		Args:
		    user (User): User to create the event for
		    event_data (Dict[str, Any]): Event data

		Returns:
		    Optional[CalendarEvent]: Created calendar event or None if failed
		"""
		try:
			# Currently only handling Google Calendar
			adapter = GoogleCalendarAdapter(user)
			return adapter.create_event(event_data)
		except Exception as ex:
			logger.error(f'Failed to create calendar event: {ex}')
			return None
