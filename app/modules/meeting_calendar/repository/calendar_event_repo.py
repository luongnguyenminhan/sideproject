"""Calendar event repository"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import Depends, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.base_repo import BaseRepo
from app.core.database import get_db
from app.core.event_hooks import EventHooks
from app.enums.calendar_enums import EventStatusEnum
from app.exceptions.exception import CustomHTTPException, NotFoundException
from app.middleware.translation_manager import _
from app.modules.meeting_calendar.dal.calendar_dal import (
	CalendarEventDAL,
	CalendarIntegrationDAL,
)
from app.modules.meeting_calendar.models.calendar import CalendarEvent
from app.modules.meeting_calendar.repository.calendar_event_sync_repo import (
	CalendarEventSyncRepo,
)
from app.modules.meeting_files.models.meeting_file import MeetingFile

logger = logging.getLogger(__name__)


class CalendarEventRepo(BaseRepo):
	"""Repository for handling calendar events

	This class is responsible for managing calendar events, including
	creation, retrieval, updating and deletion operations in the database.
	It also handles event hooks for calendar synchronization.
	"""

	def __init__(self, db: Session = Depends(get_db)):
		"""Initialize the CalendarEventRepo

		Args:
		    db (Session): Database session
		"""
		self.db = db
		self.calendar_event_dal = CalendarEventDAL(db)
		self.calendar_integration_dal = CalendarIntegrationDAL(db)
		self.calendar_event_sync_repo = CalendarEventSyncRepo(db)
		self.event_hooks = EventHooks()
		self._register_event_hooks()
		logger.debug('Initialized CalendarEventRepo')

	def _register_event_hooks(self):
		"""Register event hooks for calendar sync events"""
		self.event_hooks.register('meeting_created', self._handle_meeting_created)
		self.event_hooks.register('meeting_updated', self._handle_meeting_updated)
		self.event_hooks.register('transcript_created', self._handle_transcript_created)
		self.event_hooks.register('transcript_updated', self._handle_transcript_updated)
		self.event_hooks.register('meeting_file_created', self._handle_meeting_file_created)
		self.event_hooks.register('meeting_file_updated', self._handle_meeting_file_updated)
		logger.info('Calendar event hooks registered')

	def _handle_meeting_created(self, meeting_id: str):
		"""Handle meeting created event

		Args:
		    meeting_id (str): ID of the created meeting
		"""
		logger.info(f'Handling meeting created event for meeting: {meeting_id}')
		try:
			self.calendar_event_sync_repo.sync_meeting_to_calendar(meeting_id)
		except Exception as ex:
			logger.error(f'Error handling meeting created event: {ex}')

	def _handle_meeting_updated(self, meeting_id: str):
		"""Handle meeting updated event

		Args:
		    meeting_id (str): ID of the updated meeting
		"""
		logger.info(f'Handling meeting updated event for meeting: {meeting_id}')
		try:
			self.calendar_event_sync_repo.sync_meeting_to_calendar(meeting_id)
		except Exception as ex:
			logger.error(f'Error handling meeting updated event: {ex}')

	def _handle_transcript_created(self, transcript_id: str):
		"""Handle transcript created event

		Args:
		    transcript_id (str): ID of the created transcript
		"""
		logger.info(f'Handling transcript created event for transcript: {transcript_id}')
		try:
			self.calendar_event_sync_repo.update_event_with_transcript(transcript_id)
		except Exception as ex:
			logger.error(f'Error handling transcript created event: {ex}')

	def _handle_transcript_updated(self, transcript_id: str):
		"""Handle transcript updated event

		Args:
		    transcript_id (str): ID of the updated transcript
		"""
		logger.info(f'Handling transcript updated event for transcript: {transcript_id}')
		try:
			self.calendar_event_sync_repo.update_event_with_transcript(transcript_id)
		except Exception as ex:
			logger.error(f'Error handling transcript updated event: {ex}')

	def _handle_meeting_file_created(self, meeting_id: str):
		"""Handle meeting file created event

		Args:
		    meeting_id (str): ID of the meeting with new file
		"""
		logger.info(f'Handling meeting file created event for meeting: {meeting_id}')
		try:
			self.calendar_event_sync_repo.update_event_with_files(meeting_id)
		except Exception as ex:
			logger.error(f'Error handling meeting file created event: {ex}')

	def _handle_meeting_file_updated(self, meeting_id: str):
		"""Handle meeting file updated event

		Args:
		    meeting_id (str): ID of the meeting with updated file
		"""
		logger.info(f'Handling meeting file updated event for meeting: {meeting_id}')
		try:
			self.calendar_event_sync_repo.update_event_with_files(meeting_id)
		except Exception as ex:
			logger.error(f'Error handling meeting file updated event: {ex}')

	def sync_meeting_to_calendar(self, meeting_id: str) -> Dict[str, Any]:
		"""Sync a meeting to Google Calendar

		Args:
		    meeting_id (str): ID of the meeting to sync

		Returns:
		    Dict[str, Any]: Result of the sync operation

		Raises:
		    CustomHTTPException: If sync fails
		"""
		result = self.calendar_event_sync_repo.sync_meeting_to_calendar(meeting_id)

		if not result:
			logger.error(f'Failed to sync meeting {meeting_id} to Google Calendar')
			raise CustomHTTPException(
				message=_('calendar_sync_failed'),
			)

		return result

	def update_event_with_transcript(self, transcript_id: str) -> Dict[str, Any]:
		"""Update calendar event with transcript information

		Args:
		    transcript_id (str): ID of the transcript

		Returns:
		    Dict[str, Any]: Result of the update operation

		Raises:
		    CustomHTTPException: If update fails
		"""
		success = self.calendar_event_sync_repo.update_event_with_transcript(transcript_id)

		if not success:
			logger.error(f'Failed to update calendar event with transcript {transcript_id}')
			raise CustomHTTPException(
				message=_('calendar_sync_failed'),
			)

		return {'status': 'success', 'message': _('calendar_sync_success')}

	def update_event_with_files(self, meeting_id: str) -> Dict[str, Any]:
		"""Update calendar event with meeting files

		Args:
		    meeting_id (str): ID of the meeting

		Returns:
		    Dict[str, Any]: Result of the update operation

		Raises:
		    CustomHTTPException: If update fails
		"""
		success = self.calendar_event_sync_repo.update_event_with_files(meeting_id)

		if not success:
			logger.error(f'Failed to update calendar event with files for meeting {meeting_id}')
			raise CustomHTTPException(
				message=_('calendar_sync_failed'),
			)

		return {'status': 'success', 'message': _('calendar_sync_success')}

	def get_calendar_events(
		self,
		user_id: str,
		start_date: datetime | None = None,
		end_date: datetime | None = None,
	) -> List[Dict[str, Any]]:
		"""Get calendar events for a user within a date range

		Args:
		    user_id (str): User ID
		    start_date (Optional[datetime]): Start date for filtering
		    end_date (Optional[datetime]): End date for filtering

		Returns:
		    List[Dict[str, Any]]: List of calendar events
		"""
		try:
			events = self.calendar_event_dal.get_user_events(user_id)
			return [event.to_dict() for event in events]
		except Exception as ex:
			logger.error(f'[ERROR] Get calendar events failed: {ex}')
			raise CustomHTTPException(
				message=_('get_events_failed'),
			)

	def get_event_by_id(self, event_id: str) -> CalendarEvent:
		"""Get event by ID

		Args:
		    event_id (str): Event ID

		Returns:
		    CalendarEvent: Calendar event

		Raises:
		    NotFoundException: If event not found
		"""
		logger.debug(f'Getting event with ID {event_id}')
		event = self.calendar_event_dal.get_by_id(event_id)
		if not event or event.is_deleted:
			logger.warning(f'Event {event_id} not found or deleted')
			raise CustomHTTPException(message=_('event_not_found'))

		return event

	def validate_event_access(self, event_id: str, user_id: str) -> CalendarEvent:
		"""Validate that a user has access to an event

		Args:
		    event_id (str): Event ID
		    user_id (str): User ID

		Returns:
		    CalendarEvent: The event if accessible

		Raises:
		    NotFoundException: If event not found or not accessible
		"""
		event = self.get_event_by_id(event_id)

		if event.user_id != user_id:
			logger.warning(f'User {user_id} does not have access to event {event_id}')
			raise CustomHTTPException(message=_('event_not_found'))

		return event

	def create_event(self, event_data: Dict[str, Any]) -> CalendarEvent:
		"""Create a new calendar event in database

		Args:
		    event_data (Dict[str, Any]): Event data

		Returns:
		    CalendarEvent: Created calendar event

		Raises:
		    CustomHTTPException: If event creation fails
		"""
		try:
			logger.debug(f'Creating calendar event: {event_data.get("title", "Untitled")}')

			if 'status' not in event_data:
				event_data['status'] = EventStatusEnum.SCHEDULED.value

			event = self.calendar_event_dal.create(event_data)
			logger.info(f'Created calendar event with ID {event.id}')
			return event
		except Exception as ex:
			logger.error(f'[ERROR] Create calendar event failed: {ex}')
			raise CustomHTTPException(
				message=_('create_calendar_event_failed'),
			)

	def update_event(self, event_id: str, event_data: Dict[str, Any]) -> CalendarEvent:
		"""Update a calendar event in database

		Args:
		    event_id (str): Event ID
		    event_data (Dict[str, Any]): Event data to update

		Returns:
		    CalendarEvent: Updated calendar event

		Raises:
		    CustomHTTPException: If update fails
		"""
		try:
			logger.debug(f'Updating calendar event {event_id}')
			event = self.calendar_event_dal.update(event_id, event_data)

			if not event:
				logger.error(f'Failed to update event {event_id}')
				raise CustomHTTPException(
					message=_('update_calendar_event_failed'),
				)

			logger.info(f'Updated calendar event {event_id}')
			return event
		except Exception as ex:
			logger.error(f'[ERROR] Update calendar event failed: {ex}')
			raise CustomHTTPException(
				message=_('update_calendar_event_failed'),
			)

	def delete_event(self, event_id: str) -> bool:
		"""Soft delete a calendar event from database

		Args:
		    event_id (str): Event ID

		Returns:
		    bool: True if successful

		Raises:
		    CustomHTTPException: If deletion fails
		"""
		try:
			logger.debug(f'Soft deleting calendar event {event_id}')
			result = self.calendar_event_dal.update(event_id, {'is_deleted': True})

			if not result:
				logger.error(f'Failed to delete event {event_id}')
				raise CustomHTTPException(
					message=_('delete_calendar_event_failed'),
				)
			logger.info(f'Successfully deleted calendar event {event_id}')
			return True
		except Exception as ex:
			logger.error(f'[ERROR] Delete calendar event failed: {ex}')
			raise CustomHTTPException(
				message=_('delete_calendar_event_failed'),
			)

	def get_event_by_external_id(self, integration_id: str, external_id: str) -> CalendarEvent | None:
		"""Get event by external ID

		Args:
		    integration_id (str): Calendar integration ID
		    external_id (str): External event ID

		Returns:
		    Optional[CalendarEvent]: Calendar event or None if not found
		"""
		logger.debug(f'Getting event by external ID {external_id} for integration {integration_id}')
		event = self.calendar_event_dal.get_event_by_external_id(integration_id, external_id)

		if event:
			logger.debug(f'Found event {event.id} matching external ID {external_id}')
		else:
			logger.debug(f'No event found with external ID {external_id}')

		return event

	def generate_public_download_link(self, file_id: str) -> str:
		"""Generate a public download link with JWT token for a meeting file
		that does not require authentication when accessed

		Args:
		    file_id (str): Meeting file ID

		Returns:
		    str: Secure public download URL
		"""
		try:
			# Get the file to ensure it exists and validate it
			file = self.db.query(MeetingFile).filter(and_(MeetingFile.id == file_id, MeetingFile.is_deleted == False)).first()

			if not file or not file.object_name:
				logger.warning(f'Invalid file_id or missing object_name: {file_id}')
				return ''

			# Generate a JWT token containing the file information
			import time

			import jwt

			from app.core.config import get_settings

			settings = get_settings()

			# Create a token with the file information that expires in 30 days
			payload = {
				'file_id': file.id,
				'object_name': file.object_name,
				'exp': int(time.time()) + (30 * 24 * 60 * 60),  # 30 days expiration
			}

			# Sign the token with the app's secret key
			token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm='HS256')

			# Get the API base URL
			base_url = settings.API_BASE_URL or 'https://api.meobeo.ai'

			# Remove trailing slash if present
			if base_url.endswith('/'):
				base_url = base_url[:-1]

			# Construct the download URL to our public endpoint
			download_url = f'{base_url}/api/v1/calendar-events/files/public-download?token={token}'

			logger.debug(f'Generated public download URL for file {file_id}')
			return download_url

		except Exception as ex:
			logger.error(f'Error generating public download URL: {ex}')
			return ''
