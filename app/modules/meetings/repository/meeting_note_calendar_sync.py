"""Meeting note calendar synchronization module for integrating tasks with Google Calendar"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import status
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from app.exceptions.exception import CustomHTTPException, NotFoundException
from app.middleware.translation_manager import _
from app.modules.meetings.models.meeting import Meeting
from app.modules.meetings.models.meeting_note import MeetingItem, MeetingNote
from app.modules.users.models.users import User

logger = logging.getLogger(__name__)


class MeetingNoteCalendarSync:
	"""Class for synchronizing meeting note items with Google Calendar"""

	def __init__(self, repo):
		"""Initialize the MeetingNoteCalendarSync

		Args:
		    repo: The main MeetingNoteRepo instance
		"""
		self.repo = repo

	async def add_note_item_event(
		self,
		note_id: str,
		item_id: str,
		user_id: str,
		emails: list[str],
	) -> Dict[str, Any]:
		"""Add an event for a meeting note item (task)

		Creates a calendar event for the specified task item with the provided
		attendees and syncs it with Google Calendar.

		Args:
		    note_id (str): Meeting note ID
		    item_id (str): Meeting item ID
		    user_id (str): User ID
		    emails (List[str]): List of email addresses for attendees

		Returns:
		    Dict[str, Any]: Updated meeting item data

		Raises:
		    NotFoundException: If note or item not found
		    CustomHTTPException: If operation fails
		"""

		# Get the meeting note to verify access and meeting relationship
		note: MeetingNote = self.repo.meeting_note_dal.get_by_id(note_id)
		if not note or note.is_deleted:
			logger.error(f'Meeting note not found: {note_id}')
			raise CustomHTTPException(message=_('note_not_found'))

		# Get the meeting item
		item: MeetingItem = self.repo.meeting_item_dal.get_by_id(item_id)
		if not item or item.is_deleted:
			logger.error(f'Meeting item not found: {item_id}')
			raise CustomHTTPException(message=_('item_not_found'))

		# Verify that the item belongs to the note
		if item.meeting_note_id != note.id:
			logger.error(f'Item {item_id} does not belong to note {note_id}')
			raise CustomHTTPException(message=_('item_not_found'))

		# Get the meeting associated with this note
		meeting: Meeting = self.repo.meeting_dal.get_by_id(note.meeting_id)
		if not meeting:
			logger.error(f'Meeting not found for note: {note_id}')
			raise CustomHTTPException(message=_('meeting_not_found'))

		try:
			# First check if the item is a task
			if item.type.lower() != 'action_item':
				logger.error(f'Item is not a task: {item_id} (type: {item.type})')
				raise CustomHTTPException(
					message=_('item_not_task'),
				)

			# Get content of the task item
			task_content = item.content
			if isinstance(task_content, str):
				try:
					# Try to parse if content is a JSON string
					task_content = json.loads(task_content)
				except json.JSONDecodeError:
					logger.error(f'Invalid task content format: {task_content}')
					raise CustomHTTPException(
						message=_('invalid_task_content'),
					)

			# Create updated content with attendees
			task_content['attendees'] = emails

			with self.repo.meeting_item_dal.transaction():
				# Update item with attendees in the database
				updated_item = self.repo.meeting_item_dal.update(item_id, {'content': task_content})
				if not updated_item:
					raise CustomHTTPException(
						message=_('update_task_failed'),
					)

			# Now we'll sync this task to Google Calendar
			try:
				# Make sure user has Google credentials
				user: User = self.repo.user_dal.get_by_id(user_id)
				if not user or not user.google_credentials_json:
					logger.warning(f'User has no Google credentials: {user_id}')
					raise CustomHTTPException(
						message=_('google_calendar_not_connected'),
					)

				# Create Google Calendar service
				google_creds = user.get_google_credentials()

				if not google_creds or 'access_token' not in google_creds:
					logger.error(f'Missing or invalid Google credentials for user {user_id}')
					raise CustomHTTPException(
						message=_('google_calendar_not_connected'),
					)

				# Make sure we have all required fields
				credentials = Credentials(
					token=google_creds['access_token'],
					refresh_token=google_creds.get('refresh_token'),
					token_uri='https://oauth2.googleapis.com/token',
					client_id=GOOGLE_CLIENT_ID,
					client_secret=GOOGLE_CLIENT_SECRET,
					scopes=['https://www.googleapis.com/auth/calendar'],
				)

				# Check if token needs refresh
				if credentials.expired and credentials.refresh_token:
					request = Request()
					credentials.refresh(request)

					# Update stored credentials
					google_creds['access_token'] = credentials.token
					google_creds['expires_at'] = int((datetime.now() + timedelta(seconds=credentials.expires_in)).timestamp())

					# Update credentials in the user record
					self.repo.user_dal.update(
						user.id,
						{'google_credentials_json': json.dumps(google_creds)},
					)

				# Build Google Calendar service
				service = build('calendar', 'v3', credentials=credentials)

				# Extract task details for the event
				task_description = task_content.get('task', '')
				assignee = task_content.get('assignee', '')
				deadline_str = task_content.get('deadline', '')

				# Parse deadline if available or set default date
				event_date = None
				if deadline_str:
					try:
						# Try different date formats
						formats = [
							'%Y-%m-%d',
							'%d/%m/%Y',
							'%d-%m-%Y',
							'%d.%m.%Y',
							'%d %b %Y',
							'%d %B %Y',
						]

						for fmt in formats:
							try:
								event_date = datetime.strptime(deadline_str.strip(), fmt)
								break
							except ValueError:
								continue

						# If no format matched, try natural language parsing
						if not event_date:
							if 'today' in deadline_str.lower():
								event_date = datetime.now()
							elif 'tomorrow' in deadline_str.lower():
								event_date = datetime.now() + timedelta(days=1)
							elif 'next week' in deadline_str.lower():
								event_date = datetime.now() + timedelta(days=7)
					except Exception as ex:
						logger.warning(f'Failed to parse deadline: {ex}')
						# Default to tomorrow if parsing fails
						event_date = datetime.now() + timedelta(days=1)

				# If no date found, default to tomorrow
				if not event_date:
					event_date = datetime.now() + timedelta(days=1)

				# Set time to 9 AM if not specified
				if event_date.hour == 0 and event_date.minute == 0:
					event_date = event_date.replace(hour=9, minute=0)

				# Calculate end time (1 hour duration)
				end_time = event_date + timedelta(hours=1)

				# Prepare calendar event data
				event_title = f'Task: {task_description[:50]}' if task_description else 'New Task'
				if assignee:
					event_title += f' (Assignee: {assignee})'

				# Format description - Vietnamese version
				description = f'**Nhiệm vụ:** {task_description}\n\n'
				if assignee:
					description += f'**Người thực hiện:** {assignee}\n'
				if task_content.get('status'):
					description += f'**Trạng thái:** {task_content.get("status")}\n'
				if task_content.get('notes'):
					description += f'**Ghi chú:** {task_content.get("notes")}\n\n'

				# Add meeting information in Vietnamese
				description += f'\n**Từ cuộc họp:** {meeting.title}\n'
				description += f'**Ngày họp:** {meeting.meeting_date.strftime("%d-%m-%Y %H:%M")}\n'
				if meeting.meeting_link:
					description += f'**Đường dẫn cuộc họp:** {meeting.meeting_link}\n'

				# Prepare attendees
				attendees = []
				for email in emails:
					if email.strip():  # Skip empty emails
						attendees.append({'email': email.strip()})

				# Add the user as an attendee if not already included
				if user.email and user.email not in [a['email'] for a in attendees]:
					attendees.append({'email': user.email, 'responseStatus': 'accepted'})

				# Create event data
				event_data = {
					'summary': event_title,
					'description': description,
					'start': {
						'dateTime': event_date.isoformat(),
						'timeZone': 'Asia/Ho_Chi_Minh',
					},
					'end': {
						'dateTime': end_time.isoformat(),
						'timeZone': 'Asia/Ho_Chi_Minh',
					},
					'attendees': attendees,
					'reminders': {
						'useDefault': False,
						'overrides': [
							{'method': 'email', 'minutes': 24 * 60},  # 1 day before
							{'method': 'popup', 'minutes': 30},  # 30 minutes before
						],
					},
					# Use a distinct color for task events (red)
					'colorId': '11',
				}

				if task_content.get('googleCalendarEventId'):
					existed_envent = (
						service.events()
						.get(
							calendarId='primary',
							eventId=task_content['googleCalendarEventId'],
						)
						.execute()
					)
					if not existed_envent:
						created_event = (
							service.events()
							.insert(
								calendarId='primary',
								body=event_data,
								sendUpdates='all',  # Send emails to attendees
							)
							.execute()
						)
					else:
						created_event = (
							service.events()
							.update(
								calendarId='primary',
								eventId=task_content['googleCalendarEventId'],
								body=event_data,
								sendUpdates='all',  # Send emails to attendees
							)
							.execute()
						)
				else:
					# Send invitations to attendees
					created_event = (
						service.events()
						.insert(
							calendarId='primary',
							body=event_data,
							sendUpdates='all',  # Send emails to attendees
						)
						.execute()
					)

				if not created_event:
					logger.error('Failed to create Google Calendar event')
					raise CustomHTTPException(
						message=_('calendar_event_creation_failed'),
					)

				# Store the event ID in the task content for future reference
				task_content['googleCalendarEventId'] = created_event.get('id')
				task_content['id'] = created_event.get('id')
				task_content['eventCreated'] = True
				task_content['lastEventSync'] = datetime.now().isoformat()

				# Update the item with the event reference through the item manager
				item_manager = self.repo.get_item_manager()
				result = item_manager.update_note_item(note_id, item_id, user_id, {'content': task_content})

				self.repo.user_logs_dal.create({
					'user_id': user.id,
					'action': 'add_note_item_event',
					'details': f'Added event to item {item_id} in note {note_id}',
				})
				return result

			except HttpError as error:
				if error.resp.status == 401:
					logger.error(f'Google Calendar authentication error: {error}')
					raise CustomHTTPException(
						message=_('google_calendar_auth_error'),
					)

				else:
					logger.error(f'Google Calendar API error: {error}')
					raise CustomHTTPException(
						message=_('calendar_sync_failed'),
					)

			except Exception as ex:
				logger.error(f'Error creating calendar event: {ex}')
				raise CustomHTTPException(
					message=_('calendar_sync_failed'),
				)

		except Exception as ex:
			logger.error(f'Error adding note item event: {ex}')
			raise CustomHTTPException(
				message=_('add_note_item_event_failed'),
			)
