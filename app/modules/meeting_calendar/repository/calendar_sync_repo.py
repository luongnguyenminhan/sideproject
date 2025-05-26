"""Calendar sync repository for syncing events to meetings"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.base_model import Pagination
from app.core.base_repo import BaseRepo
from app.core.database import get_db
from app.enums.meeting_enums import MeetingStatusEnum
from app.exceptions.exception import CustomHTTPException
from app.middleware.translation_manager import _
from app.modules.meeting_calendar.dal.calendar_dal import (
	CalendarEventDAL,
	CalendarIntegrationDAL,
)
from app.modules.meeting_calendar.models.calendar import CalendarEvent
from app.modules.meetings.dal.meeting_dal import MeetingDAL
from app.modules.meetings.repository.meeting_repo import MeetingRepo

logger = logging.getLogger(__name__)


class CalendarSyncRepo(BaseRepo):
	"""Repository for synchronizing calendar events to meetings

	This class handles the logic for automatically creating meetings from calendar events
	and linking them together.
	"""

	def __init__(self, db: Session = Depends(get_db)):
		"""Initialize the CalendarSyncRepo

		Args:
		    db (Session): Database session
		"""
		self.db = db
		self.calendar_event_dal = CalendarEventDAL(db)
		self.calendar_integration_dal = CalendarIntegrationDAL(db)
		self.meeting_dal = MeetingDAL(db)
		self.meeting_repo = MeetingRepo(db)
		logger.debug('Initialized CalendarSyncRepo')

	def sync_events_to_meetings(self, user_id: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
		"""Synchronize calendar events to meetings

		Args:
		    user_id (str): User ID
		    events (List[Dict[str, Any]]): Raw calendar events from Google API

		Returns:
		    Dict[str, Any]: Sync statistics
		"""
		logger.info(f'Starting calendar to meeting sync for user {user_id} with {len(events)} events')

		stats = {
			'total': len(events),
			'processed': 0,
			'meetings_created': 0,
			'meetings_updated': 0,
			'meetings_linked': 0,
			'skipped': 0,
			'errors': 0,
		}

		try:
			# Process each event
			for event in events:
				if not isinstance(event, dict):
					logger.error(f'Expected dict but got {type(event)}')
					stats['errors'] += 1
					continue

				try:
					# Skip events without necessary data
					if not self._is_valid_event(event):
						stats['skipped'] += 1
						continue

					# Extract meeting link from event
					meeting_link, link_type = self._get_meeting_link(event)
					# Skip events without meeting links
					if not meeting_link:
						stats['skipped'] += 1
						continue

					print(f'Valid event: {event["summary"]} because meeting link is present=======')
					# Create or update the calendar event in our database
					event_checking: Pagination[CalendarEvent] = self.calendar_event_dal.get_by_external_id(
						user_id=user_id,
						external_event_id=event['id'],
					)
					print(f'Event checking: {event_checking}')
					if event_checking and len(event_checking.items) > 0:
						# Event already exists and is linked to a meeting
						print(f'Event {event_checking.items[0].external_event_id} already linked to meeting {event_checking.items[0].meeting_id}')
						stats['skipped'] += 1
						continue
					else:
						pass

					# Process the event
					created, updated, linked = self._process_event(user_id, event, meeting_link, link_type)

					# Update stats
					if created:
						stats['meetings_created'] += 1
					if updated:
						stats['meetings_updated'] += 1
					if linked:
						stats['meetings_linked'] += 1

					stats['processed'] += 1

				except Exception as ex:
					logger.error(f'Error processing event {event.get("id", "unknown")}: {ex}')
					stats['errors'] += 1
					continue

			logger.info(f'Calendar sync completed. Stats: {stats}')
			return stats

		except Exception as ex:
			logger.error(f'Calendar sync failed: {ex}')
			raise CustomHTTPException(
				message=_('calendar_sync_failed'),
			)

	def _is_valid_event(self, event: Dict[str, Any]) -> bool:
		"""Check if an event has all required data for sync

		Args:
		    event (Dict[str, Any]): Calendar event

		Returns:
		    bool: True if event is valid for sync
		"""
		# Event must have ID, title, and start/end times
		if not event.get('id') or not event.get('summary'):
			print(f'Invalid event: {event} because event id {event.get("id")} or summary {event.get("summary")} is missing')
			return False

		# Check start and end times
		if not event.get('start') and not event.get('end'):
			print(f'Invalid event: {event} because start {event.get("start")} and end {event.get("end")} are missing')
			return False

		# If the event is canceled, we should skip it
		if event.get('status') == 'cancelled':
			print(f'Invalid event: {event} because status is cancelled')
			return False

		print(f'Valid event: {event} because it has all required data')
		return True

	def _get_meeting_link(self, event: Dict[str, Any]) -> Tuple[str | None, str | None]:
		"""Extract meeting link from calendar event

		Args:
		    event (Dict[str, Any]): Calendar event

		Returns:
		    Tuple[Optional[str], Optional[str]]: Meeting link and link type
		"""
		link_type = None
		meeting_link = None

		# First check for hangoutLink (Google Meet)
		if event.get('hangoutLink'):
			print(f'Valid event: {event} because hangoutLink is present')
			meeting_link = event['hangoutLink']
			link_type = 'Google Meet'

		# Then check for conferenceData
		elif event.get('conferenceData') and event['conferenceData'].get('entryPoints'):
			print(f'Valid event: {event} because conferenceData is present')
			for entry_point in event['conferenceData']['entryPoints']:
				if entry_point.get('entryPointType') == 'video':
					meeting_link = entry_point.get('uri')
					link_type = 'Google Meet' if 'meet.google.com' in meeting_link else 'Video Conference'
					break

		# Finally check for location as last resort
		elif event.get('location') and ('zoom.us/' in event.get('location', '') or 'meet.google.com/' in event.get('location', '') or 'teams.microsoft.com/' in event.get('location', '')):
			meeting_link = event['location']
			print(f'Valid event: {event} because location is present')
			if 'zoom.us/' in meeting_link:
				link_type = 'Zoom'
			elif 'meet.google.com/' in meeting_link:
				link_type = 'Google Meet'
			elif 'teams.microsoft.com/' in meeting_link:
				link_type = 'Microsoft Teams'
			else:
				link_type = 'Online Meeting'
		return meeting_link, link_type

	def _process_event(self, user_id: str, event: Dict[str, Any], meeting_link: str, link_type: str) -> Tuple[bool, bool, bool]:
		"""Process a single calendar event

		Args:
		    user_id (str): User ID
		    event (Dict[str, Any]): Calendar event
		    meeting_link (str): Meeting link
		    link_type (str): Meeting link type

		Returns:
		    Tuple[bool, bool, bool]: (created, updated, linked) status flags
		"""
		event_id = event['id']
		meeting_created = False
		meeting_updated = False
		meeting_linked = False

		# Check if we already have this event in our database
		existing_event = self._find_event_in_db(user_id, event_id)
		# Extract event data for creating/updating meeting
		meeting_data = self._prepare_meeting_data(event, meeting_link, link_type)

		if existing_event:
			# Event exists in database
			logger.debug(f'Found existing calendar event: {event_id}')

			# If event is already linked to a meeting
			if existing_event.meeting_id:
				logger.debug(f'Event {event_id} is linked to meeting {existing_event.meeting_id}')

				# Update the meeting if needed
				meeting = self.meeting_dal.get_by_id(existing_event.meeting_id)
				if meeting and (
					meeting.meeting_link != meeting_link
					or meeting.title != meeting_data['title']
					or meeting.meeting_date != meeting_data['meeting_date']
					or meeting.platform != meeting_data['platform']
				):
					logger.debug(f'Updating meeting {meeting.id} with new data')
					self.meeting_dal.update(meeting.id, meeting_data)
					meeting_updated = True
			else:
				# Event exists but not linked to a meeting - create and link meeting
				try:
					with self.meeting_dal.transaction():
						meeting = self.meeting_repo.create_meeting(user_id, meeting_data)
					meeting_created = True

					# Link event to the meeting
					with self.calendar_event_dal.transaction():
						self.calendar_event_dal.update(existing_event.id, {'meeting_id': meeting.id})

					meeting_linked = True
					logger.debug(f'Created and linked meeting {meeting.id} to event {event_id}')
				except Exception as ex:
					logger.error(f'Failed to create meeting for event {event_id}: {ex}')
		else:
			# New event - create calendar event record first
			try:
				# Create the calendar event in our database
				calendar_event_data = self._prepare_calendar_event_data(user_id, event)
				calendar_event = self.calendar_event_dal.create(calendar_event_data)
				logger.debug(f'Created calendar event record: {calendar_event.id}')

				# Create a meeting
				meeting = self.meeting_repo.create_meeting(user_id, meeting_data)
				meeting_created = True

				# Link event to the meeting
				self.calendar_event_dal.update(calendar_event.id, {'meeting_id': meeting.id})
				meeting_linked = True
				logger.debug(f'Created and linked meeting {meeting.id} to event {event_id}')
			except Exception as ex:
				logger.error(f'Failed to process new event {event_id}: {ex}')

		return meeting_created, meeting_updated, meeting_linked

	def _find_event_in_db(self, user_id: str, external_event_id: str) -> CalendarEvent | None:
		"""Find a calendar event in the database by external ID

		Args:
		    user_id (str): User ID
		    external_event_id (str): External event ID from Google/other provider

		Returns:
		    Optional[CalendarEvent]: Calendar event if found, None otherwise
		"""
		# Get the user's calendar integrations
		integrations = self.calendar_integration_dal.get_user_integrations(user_id)

		# Check each integration for the event
		for integration in integrations:
			event = self.calendar_event_dal.get_event_by_external_id(integration.id, external_event_id)
			if event:
				return event

		return None

	def _prepare_calendar_event_data(self, user_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
		"""Prepare calendar event data for database

		Args:
		    user_id (str): User ID
		    event (Dict[str, Any]): Calendar event

		Returns:
		    Dict[str, Any]: Prepared calendar event data
		"""
		# Get the user's calendar integrations (assuming Google for now)
		with self.calendar_integration_dal.transaction():
			integration = self.calendar_integration_dal.get_integration_by_provider(user_id, 'google')
		if not integration:
			logger.warning(f'No Google calendar integration found for user {user_id}')
			# add new integration
			with self.calendar_integration_dal.transaction():
				integration = self.calendar_integration_dal.create_integration(user_id, 'google')

			logger.info(f'Created new Google calendar integration for user {user_id}')
			return {
				'user_id': user_id,
				'calendar_integration_id': integration.id,
				'external_event_id': event['id'],
				'title': event['summary'],
				'description': event.get('description', ''),
				'location': event.get('location', ''),
				'start_time': self._parse_event_datetime(event['start']),
				'end_time': self._parse_event_datetime(event['end']),
				'is_recurring': 'recurringEventId' in event,
				'status': event.get('status', 'confirmed'),
			}

		# Parse start and end times
		start_time = self._parse_event_datetime(event['start'])
		end_time = self._parse_event_datetime(event['end'])

		return {
			'user_id': user_id,
			'calendar_integration_id': integration.id,
			'external_event_id': event['id'],
			'title': event['summary'],
			'description': event.get('description', ''),
			'location': event.get('location', ''),
			'start_time': start_time,
			'end_time': end_time,
			'is_recurring': 'recurringEventId' in event,
			'status': event.get('status', 'confirmed'),
		}

	def _prepare_meeting_data(self, event: Dict[str, Any], meeting_link: str, link_type: str) -> Dict[str, Any]:
		"""Prepare meeting data from calendar event

		Args:
		    event (Dict[str, Any]): Calendar event
		    meeting_link (str): Meeting link
		    link_type (str): Meeting link type

		Returns:
		    Dict[str, Any]: Meeting data
		"""
		# Parse start and end times
		start_time = self._parse_event_datetime(event['start'])
		end_time = self._parse_event_datetime(event['end'])

		# Calculate duration in seconds
		duration_seconds = int((end_time - start_time).total_seconds())

		meeting_data = {
			'title': event['summary'],
			'description': event.get('description', ''),
			'meeting_date': start_time,
			'duration_seconds': duration_seconds,
			'meeting_type': 'Calendar Event',
			'status': MeetingStatusEnum.SCHEDULED.value,
			'is_recurring': 'recurringEventId' in event,
			'platform': link_type,
			'meeting_link': meeting_link,
		}

		# Add organizer information if available
		if 'organizer' in event and 'email' in event['organizer']:
			meeting_data['organizer_email'] = event['organizer']['email']
			meeting_data['organizer_name'] = event['organizer'].get('displayName', '')

		return meeting_data

	def _parse_event_datetime(self, datetime_obj: Dict[str, Any]) -> datetime:
		"""Parse date/time from calendar event

		Args:
		    datetime_obj (Dict[str, Any]): Date/time object from calendar event

		Returns:
		    datetime: Parsed datetime object
		"""
		if 'dateTime' in datetime_obj:
			# This is a datetime string in ISO format
			return datetime.fromisoformat(datetime_obj['dateTime'].replace('Z', '+00:00'))
		elif 'date' in datetime_obj:
			# This is a date string
			return datetime.fromisoformat(datetime_obj['date'])
		else:
			raise ValueError('Invalid datetime format in event')
