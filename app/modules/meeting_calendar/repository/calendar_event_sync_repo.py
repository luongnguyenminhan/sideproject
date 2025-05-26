"""Repository for syncing meetings to Google Calendar events"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import Depends
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.core.base_repo import BaseRepo
from app.core.database import get_db
from app.enums.calendar_enums import EventStatusEnum
from app.modules.meeting_calendar.dal.calendar_dal import (
	CalendarEventDAL,
	CalendarIntegrationDAL,
)
from app.modules.meeting_calendar.models.calendar import (
	CalendarEvent,
	CalendarIntegration,
)
from app.modules.meeting_calendar.utils.calendar_event_builder import prepare_event_data
from app.modules.meeting_calendar.utils.calendar_event_finder import check_existing_event_on_calendar
from app.modules.meeting_calendar.utils.calendar_event_formatter import format_event_description
from app.modules.meeting_calendar.utils.calendar_google_service import create_google_calendar_service, get_or_create_calendar_integration
from app.modules.meeting_files.dal.meeting_file_dal import MeetingFileDAL
from app.modules.meeting_transcripts.dal.transcript_dal import TranscriptDAL
from app.modules.meetings.dal.meeting_dal import MeetingDAL
from app.modules.meetings.dal.meeting_note_dal import MeetingNoteDAL
from app.modules.meetings.models.meeting import Meeting
from app.modules.users.dal.user_dal import UserDAL
from app.modules.users.models.users import User

logger = logging.getLogger(__name__)


class CalendarEventSyncRepo(BaseRepo):
	"""Repository for syncing meetings to Google Calendar events

	This class handles syncing from meetings to Google Calendar events, including
	creating new events, updating existing events, and updating event descriptions
	when transcripts or files are updated.
	"""

	def __init__(self, db: Session = Depends(get_db)):
		"""Initialize the CalendarEventSyncRepo

		Args:
		    db (Session): Database session
		"""
		self.db = db
		self.calendar_event_dal = CalendarEventDAL(db)
		self.calendar_integration_dal = CalendarIntegrationDAL(db)
		self.meeting_dal = MeetingDAL(db)
		self.user_dal = UserDAL(db)
		self.meeting_file_dal = MeetingFileDAL(db)
		self.transcript_dal = TranscriptDAL(db)
		self.meeting_note_dal = MeetingNoteDAL(db)

	def sync_meeting_to_calendar(self, meeting_id: str) -> Dict[str, Any] | None:
		"""Sync a meeting to Google Calendar

		Creates or updates a Google Calendar event based on meeting details.

		Args:
		    meeting_id (str): ID of the meeting to sync

		Returns:
		    Optional[Dict[str, Any]]: Result of sync operation or None if failed
		"""
		try:
			# Get the meeting
			meeting: Meeting = self.meeting_dal.get_by_id(meeting_id)
			if not meeting or meeting.is_deleted:
				logger.warning(f'Meeting not found or deleted: {meeting_id}')
				return None

			# Get the user
			user: User = self.user_dal.get_by_id(meeting.user_id)
			if not user or user.is_deleted:
				logger.warning(f'User not found or deleted: {meeting.user_id}')
				return None

			# Check if user has Google credentials
			google_credentials = user.get_google_credentials()
			if not google_credentials:
				logger.warning(f'No Google credentials found for user {meeting.user_id}')
				return None

			# Get or create Google Calendar integration
			integration = get_or_create_calendar_integration(meeting.user_id, self.calendar_integration_dal)
			if not integration:
				logger.error(f'Failed to get or create calendar integration for user {meeting.user_id}')
				return None

			# Create Google Calendar service
			service = create_google_calendar_service(user, integration, self.calendar_integration_dal)
			if not service:
				logger.error('Failed to create Google Calendar service')
				return None

			# Check if meeting already has a calendar event
			existing_events = self.calendar_event_dal.get_events_by_meeting(meeting_id)

			if existing_events:
				# Update existing calendar event
				result = self._update_calendar_event(meeting, existing_events[0], service)
			else:
				# Create new calendar event
				result = self._create_calendar_event(meeting, integration, service)

			return result

		except Exception as ex:
			logger.error(f'Error syncing meeting to calendar: {ex}')
			return None

	def update_event_with_transcript(self, transcript_id: str) -> bool:
		"""Update calendar event with transcript information

		Args:
		    transcript_id (str): ID of the transcript

		Returns:
		    bool: True if successful, False otherwise
		"""
		try:
			# Get the transcript
			transcript = self.transcript_dal.get_by_id(transcript_id)
			if not transcript or transcript.is_deleted:
				logger.warning(f'Transcript not found or deleted: {transcript_id}')
				return False

			# Get the meeting
			meeting = self.meeting_dal.get_by_id(transcript.meeting_id)
			if not meeting or meeting.is_deleted:
				logger.warning(f'Meeting not found or deleted: {transcript.meeting_id}')
				return False

			# Get calendar events for this meeting
			events = self.calendar_event_dal.get_events_by_meeting(meeting.id)
			if not events:
				logger.warning(f'No calendar events found for meeting: {meeting.id}')
				return False

			# Get the user
			user = self.user_dal.get_by_id(meeting.user_id)
			if not user:
				logger.warning(f'User not found: {meeting.user_id}')
				return False

			# Create Google Calendar service
			service = create_google_calendar_service(user, None, self.calendar_integration_dal)
			if not service:
				logger.error('Failed to create Google Calendar service')
				return False

			# Update the description for each event
			for event in events:
				self._update_event_description(meeting, event, service)

			return True

		except Exception as ex:
			logger.error(f'Error updating event with transcript: {ex}')
			return False

	def update_event_with_files(self, meeting_id: str) -> bool:
		"""Update calendar event with meeting files information

		Args:
		    meeting_id (str): ID of the meeting

		Returns:
		    bool: True if successful, False otherwise
		"""
		try:
			# Get the meeting
			meeting = self.meeting_dal.get_by_id(meeting_id)
			if not meeting or meeting.is_deleted:
				logger.warning(f'Meeting not found or deleted: {meeting_id}')
				return False

			# Get calendar events for this meeting
			events = self.calendar_event_dal.get_events_by_meeting(meeting.id)
			if not events:
				logger.warning(f'No calendar events found for meeting: {meeting.id}')
				return False

			# Get the user
			user = self.user_dal.get_by_id(meeting.user_id)
			if not user:
				logger.warning(f'User not found: {meeting.user_id}')
				return False

			# Create Google Calendar service
			service = create_google_calendar_service(user, None, self.calendar_integration_dal)
			if not service:
				logger.error('Failed to create Google Calendar service')
				return False

			# Update the description for each event
			for event in events:
				self._update_event_description(meeting, event, service)

			return True

		except Exception as ex:
			logger.error(f'Error updating event with files: {ex}')
			return False

	def _create_calendar_event(self, meeting: Meeting, integration: CalendarIntegration, service: Any) -> Dict[str, Any] | None:
		"""Create a new Google Calendar event for a meeting

		Args:
			meeting (Meeting): Meeting object
			integration (CalendarIntegration): Calendar integration
			service: Google Calendar service

		Returns:
			Optional[Dict[str, Any]]: Created event info or None if failed
		"""
		try:
			logger.info(f'Creating new Google Calendar event for meeting {meeting.id}')
			print(f'Attempting to create calendar event for meeting: {meeting.id}, title: {meeting.title}')

			# Check if event already exists on Google Calendar
			existing_event_id = check_existing_event_on_calendar(meeting, service)
			if existing_event_id:
				print(f'Found existing Google Calendar event with ID: {existing_event_id}')
				logger.info(f'Found existing Google Calendar event {existing_event_id} for meeting {meeting.id}')

				# Get details of the existing event
				existing_event = service.events().get(calendarId='primary', eventId=existing_event_id).execute()
				print(f'Retrieved existing event details: {json.dumps(existing_event, indent=2)}')

				# Format the description with additional information
				description = format_event_description(meeting, self.transcript_dal, self.meeting_file_dal, self.meeting_note_dal, self.db)

				# Prepare event data for update
				event_data = prepare_event_data(meeting, description)
				print(f'Updating existing event with new data: {json.dumps(event_data, indent=2)}')

				# Update the existing event
				updated_event = (
					service.events()
					.update(
						calendarId='primary',
						eventId=existing_event_id,
						body=event_data,
					)
					.execute()
				)

				print(f'Successfully updated existing Google Calendar event with ID: {existing_event_id}')

				# Create calendar_event record in our database (if it doesn't exist)
				calendar_event = self.calendar_event_dal.get_event_by_external_id(integration.id, existing_event_id)
				if not calendar_event:
					print('Creating new database record for existing calendar event')
					# Create a new record to track this event
					with self.calendar_event_dal.transaction():
						calendar_event = self.calendar_event_dal.create({
							'user_id': meeting.user_id,
							'calendar_integration_id': integration.id,
							'external_event_id': existing_event_id,
							'title': meeting.title,
							'description': description,
							'location': updated_event.get('location', ''),
							'start_time': meeting.meeting_date,
							'end_time': meeting.meeting_date + timedelta(seconds=meeting.duration_seconds or 3600),
							'meeting_id': meeting.id,
							'is_recurring': meeting.is_recurring,
							'status': EventStatusEnum.SCHEDULED.value,
						})
					logger.info(f'Linked and updated existing Google Calendar event {existing_event_id} with meeting {meeting.id}')
					print(f'Successfully linked meeting {meeting.id} with existing calendar event')
				else:
					# Update the existing calendar event record
					self.calendar_event_dal.update(
						calendar_event.id,
						{
							'title': meeting.title,
							'description': description,
							'location': updated_event.get('location', ''),
							'start_time': meeting.meeting_date,
							'end_time': meeting.meeting_date + timedelta(seconds=meeting.duration_seconds or 3600),
							'is_recurring': meeting.is_recurring,
							'status': EventStatusEnum.SCHEDULED.value,
						},
					)
					logger.info(f'Updated existing Google Calendar event {existing_event_id} for meeting {meeting.id}')
					print(f'Successfully updated calendar event record for meeting {meeting.id}')

				return {
					'event_id': existing_event_id,
					'calendar_event_id': calendar_event.id,
					'title': meeting.title,
					'status': 'updated_existing',
				}

			# Format the description with additional information
			print('No existing event found, creating new calendar event')
			description = format_event_description(meeting, self.transcript_dal, self.meeting_file_dal, self.meeting_note_dal, self.db)

			# Prepare event data
			event_data = prepare_event_data(meeting, description)
			print(f'Prepared event data: {json.dumps(event_data, indent=2)}')

			# Create event
			print('Sending create event request to Google Calendar API')
			created_event = service.events().insert(calendarId='primary', body=event_data).execute()
			if not created_event:
				print('Failed to create Google Calendar event - API returned empty response')
				logger.error(f'Failed to create Google Calendar event for meeting {meeting.id}')
				return None

			print(f'Successfully created event in Google Calendar with ID: {created_event.get("id")}')

			# Save calendar event in our database
			print('Saving new calendar event to database')
			calendar_event = self.calendar_event_dal.create({
				'user_id': meeting.user_id,
				'calendar_integration_id': integration.id,
				'external_event_id': created_event.get('id'),
				'title': meeting.title,
				'description': description,
				'location': created_event.get('location', ''),
				'start_time': meeting.meeting_date,
				'end_time': meeting.meeting_date + timedelta(seconds=meeting.duration_seconds or 3600),
				'meeting_id': meeting.id,
				'is_recurring': meeting.is_recurring,
				'status': EventStatusEnum.SCHEDULED.value,
			})

			logger.info(f'Created Google Calendar event {created_event.get("id")} for meeting {meeting.id}')
			print(f'Calendar event creation complete for meeting {meeting.id}')

			return {
				'event_id': created_event.get('id'),
				'calendar_event_id': calendar_event.id,
				'title': meeting.title,
				'status': 'created_new',
			}

		except HttpError as error:
			if error.resp.status == 401:
				logger.error(f'Authentication error creating Google Calendar event: {error}')
				# Could indicate token expired - handled by service creation
			else:
				logger.error(f'Google Calendar API error creating event: {error}')
			return None
		except Exception as ex:
			logger.error(f'Error creating calendar event: {ex}')
			return None

	def _update_calendar_event(self, meeting: Meeting, calendar_event: CalendarEvent, service: Any) -> Dict[str, Any] | None:
		"""Update an existing Google Calendar event for a meeting

		Args:
		    meeting (Meeting): Meeting object
		    calendar_event (CalendarEvent): Existing calendar event
		    service: Google Calendar service

		Returns:
		    Optional[Dict[str, Any]]: Updated event info or None if failed
		"""
		try:
			logger.info(f'Updating Google Calendar event {calendar_event.external_event_id} for meeting {meeting.id}')

			# Format the description with additional information
			description = format_event_description(meeting, self.transcript_dal, self.meeting_file_dal, self.meeting_note_dal, self.db)

			# Prepare event data
			event_data = prepare_event_data(meeting, description)

			# Update event
			updated_event = (
				service.events()
				.update(
					calendarId='primary',
					eventId=calendar_event.external_event_id,
					body=event_data,
				)
				.execute()
			)

			if not updated_event:
				logger.error(f'Failed to update Google Calendar event for meeting {meeting.id}')
				return None

			# Update calendar event in our database
			end_time = meeting.meeting_date + timedelta(seconds=meeting.duration_seconds or 3600)
			self.calendar_event_dal.update(
				calendar_event.id,
				{
					'title': meeting.title,
					'description': description,
					'location': updated_event.get('location', ''),
					'start_time': meeting.meeting_date,
					'end_time': end_time,
					'is_recurring': meeting.is_recurring,
					'status': meeting.status,
				},
			)

			logger.info(f'Updated Google Calendar event {calendar_event.external_event_id} for meeting {meeting.id}')

			return {
				'event_id': updated_event.get('id'),
				'calendar_event_id': calendar_event.id,
				'title': meeting.title,
			}

		except HttpError as error:
			if error.resp.status == 401:
				logger.error(f'Authentication error updating Google Calendar event: {error}')
				# Could indicate token expired - handled by service creation
			elif error.resp.status == 404:
				logger.error(f'Google Calendar event not found: {calendar_event.external_event_id}')
				# Event was deleted in Google Calendar but still exists in our database
				# Consider recreating it
				return self._recreate_deleted_calendar_event(meeting, calendar_event, service)
			else:
				logger.error(f'Google Calendar API error updating event: {error}')
			return None
		except Exception as ex:
			logger.error(f'Error updating calendar event: {ex}')
			return None

	def _recreate_deleted_calendar_event(self, meeting: Meeting, calendar_event: CalendarEvent, service: Any) -> Dict[str, Any] | None:
		"""Recreate a Google Calendar event that was deleted externally

		Args:
		    meeting (Meeting): Meeting object
		    calendar_event (CalendarEvent): Existing calendar event record
		    service: Google Calendar service

		Returns:
		    Optional[Dict[str, Any]]: Recreated event info or None if failed
		"""
		try:
			logger.info(f'Recreating deleted Google Calendar event for meeting {meeting.id}')

			# Format the description with additional information
			description = format_event_description(meeting, self.transcript_dal, self.meeting_file_dal, self.meeting_note_dal, self.db)

			# Prepare event data
			event_data = prepare_event_data(meeting, description)

			# Create new event
			created_event = service.events().insert(calendarId='primary', body=event_data).execute()

			if not created_event:
				logger.error(f'Failed to recreate Google Calendar event for meeting {meeting.id}')
				return None

			# Update calendar event in our database with new external ID
			self.calendar_event_dal.update(
				calendar_event.id,
				{
					'external_event_id': created_event.get('id'),
					'title': meeting.title,
					'description': description,
					'location': created_event.get('location', ''),
					'start_time': meeting.meeting_date,
					'end_time': meeting.meeting_date + timedelta(seconds=meeting.duration_seconds or 3600),
					'is_recurring': meeting.is_recurring,
				},
			)

			logger.info(f'Recreated Google Calendar event {created_event.get("id")} for meeting {meeting.id}')

			return {
				'event_id': created_event.get('id'),
				'calendar_event_id': calendar_event.id,
				'title': meeting.title,
			}

		except Exception as ex:
			logger.error(f'Error recreating calendar event: {ex}')
			return None

	def _update_event_description(self, meeting: Meeting, calendar_event: CalendarEvent, service: Any) -> bool:
		"""Update Google Calendar event description

		Args:
		    meeting (Meeting): Meeting object
		    calendar_event (CalendarEvent): Calendar event
		    service: Google Calendar service

		Returns:
		    bool: True if successful, False otherwise
		"""
		try:
			# Get the current event to preserve other fields
			try:
				current_event = service.events().get(calendarId='primary', eventId=calendar_event.external_event_id).execute()
			except HttpError as error:
				if error.resp.status == 404:
					logger.error(f'Event not found in Google Calendar: {calendar_event.external_event_id}')
					return False
				else:
					raise

			# Update the description
			current_event['description'] = format_event_description(meeting, self.transcript_dal, self.meeting_file_dal, self.meeting_note_dal, self.db)

			# Update event
			(
				service.events()
				.update(
					calendarId='primary',
					eventId=calendar_event.external_event_id,
					body=current_event,
				)
				.execute()
			)

			# Update local calendar event
			self.calendar_event_dal.update(calendar_event.id, {'description': current_event['description']})

			return True

		except Exception as ex:
			logger.error(f'Error updating event description: {ex}')
			return False
