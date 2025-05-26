"""Utility functions for finding existing Google Calendar events"""

import logging
from datetime import datetime, time

import pytz

from app.modules.meetings.models.meeting import Meeting

logger = logging.getLogger(__name__)


def check_existing_event_on_calendar(meeting: Meeting, service) -> str | None:
	"""Check if an event already exists on Google Calendar for a meeting

	Args:
	    meeting (Meeting): Meeting object
	    service: Google Calendar service

	Returns:
	    Optional[str]: Event ID if found, None if not
	"""
	try:
		# Get the meeting date
		meeting_date = meeting.meeting_date.date()

		# Create datetime for start and end of day with clear timezone
		vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
		day_start = datetime.combine(meeting_date, time.min).replace(tzinfo=vn_tz)
		day_end = datetime.combine(meeting_date, time.max).replace(tzinfo=vn_tz)

		# Format times according to RFC3339
		time_min = day_start.isoformat()
		time_max = day_end.isoformat()

		# Get list of events for the day
		try:
			events_result = (
				service.events()
				.list(
					calendarId='primary',
					timeMin=time_min,
					timeMax=time_max,
					singleEvents=True,
				)
				.execute()
			)

			events = events_result.get('items', [])

			# Check if any event matches the meeting title
			# Convert title to lowercase for case-insensitive comparison
			meeting_title_lower = meeting.title.lower()

			for event in events:
				event_title = event.get('summary', '')
				event_id = event.get('id')

				# If we find an event with a matching title
				if event_title.lower() == meeting_title_lower:
					logger.info(f"Found existing event with matching title: '{event_title}'")
					return event_id

			return None

		except Exception as ex:
			logger.error(f'Error listing events: {ex}')
			# Try fallback method if API error
			return fallback_check_existing_event(meeting, service)

	except Exception as ex:
		logger.error(f'Error checking for existing events: {ex}')
		# Try fallback method
		return fallback_check_existing_event(meeting, service)


def fallback_check_existing_event(meeting: Meeting, service) -> str | None:
	"""Fallback method to check if an event already exists on Google Calendar

	Args:
	    meeting (Meeting): Meeting object
	    service: Google Calendar service

	Returns:
	    Optional[str]: Event ID if found, None if not
	"""
	try:
		# Get all events from today to 7 days later
		from datetime import datetime, timedelta
		import pytz

		today = datetime.now(pytz.timezone('Asia/Ho_Chi_Minh'))
		one_week_later = today + timedelta(days=7)

		time_min = today.isoformat()
		time_max = one_week_later.isoformat()

		try:
			events_result = (
				service.events()
				.list(
					calendarId='primary',
					timeMin=time_min,
					timeMax=time_max,
					singleEvents=True,
					maxResults=100,
				)
				.execute()
			)

			events = events_result.get('items', [])

			# Exact search by title
			meeting_title_lower = meeting.title.lower()

			for event in events:
				event_title = event.get('summary', '')
				if event_title.lower() == meeting_title_lower:
					return event.get('id')

			return None

		except Exception as ex:
			logger.error(f'Error in fallback event search: {ex}')
			return None

	except Exception as ex:
		logger.error(f'Error in fallback event check: {ex}')
		return None
