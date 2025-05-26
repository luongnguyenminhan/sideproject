"""Initialize event hooks for calendar synchronization"""

import logging

from app.core.database import get_db
from app.modules.meeting_calendar.repository.calendar_event_repo import (
	CalendarEventRepo,
)

logger = logging.getLogger(__name__)


def register_calendar_event_hooks():
	"""Register event hooks for calendar synchronization

	This function should be called during application startup to register
	event handlers for meeting, transcript, and file events.
	"""
	logger.info('Registering calendar event hooks...')

	try:
		# Get database session
		db = next(get_db())

		# Initialize calendar event repo which registers the event hooks
		CalendarEventRepo(db)

		logger.info('Calendar event hooks registered successfully')
	except Exception as ex:
		logger.error(f'Failed to register calendar event hooks: {ex}')
