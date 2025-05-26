"""Google Calendar API adapter"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pytz import timezone

from app.core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from app.exceptions.exception import CustomHTTPException
from app.middleware.translation_manager import _
from app.modules.meeting_calendar.schemas.calendar_schemas import CalendarEvent
from app.modules.users.dal.user_dal import UserDAL

logger = logging.getLogger(__name__)


class GoogleCalendarAdapter:
	def __init__(self, user, db=None):
		"""Initialize with user object containing Google credentials

		Args:
		    user: User object with Google credentials
		    db: Optional database session for updating credentials
		"""
		self.user = user
		self.db = db
		self.user_dal = None
		if db:
			# Import here to avoid circular imports

			self.user_dal = UserDAL(db)

		creds_dict = user.get_google_credentials()
		if not creds_dict:
			raise ValueError('No Google credentials found for user')

		# Check if the user has granted necessary calendar permissions
		self._check_calendar_permissions(creds_dict)

		# Determine appropriate scope based on granted permissions
		calendar_scope = self._get_appropriate_calendar_scope(creds_dict)

		self.creds = Credentials(
			token=creds_dict['access_token'],
			refresh_token=creds_dict.get('refresh_token'),
			token_uri='https://oauth2.googleapis.com/token',
			client_id=GOOGLE_CLIENT_ID,
			client_secret=GOOGLE_CLIENT_SECRET,
			scopes=[calendar_scope],
		)

		# Check if token needs refresh
		if self.creds.expired and self.creds.refresh_token:
			self._refresh_credentials()

		self.service = build('calendar', 'v3', credentials=self.creds)

	def _check_calendar_permissions(self, creds_dict: dict) -> None:
		"""
		Kiểm tra xem người dùng đã cấp quyền calendar cần thiết chưa

		Args:
		    creds_dict: Dictionary chứa thông tin xác thực và phạm vi

		Raises:
		    CustomHTTPException: Nếu không có quyền calendar nào được cấp
		"""
		granted_scopes = []

		# Phân tích các phạm vi (scopes) theo nhiều định dạng có thể có
		if isinstance(creds_dict.get('scope'), str):
			granted_scopes = creds_dict.get('scope', '').split(' ')
		elif isinstance(creds_dict.get('scope'), list):
			granted_scopes = creds_dict.get('scope', [])
		elif isinstance(creds_dict.get('granted_scopes'), list):
			granted_scopes = creds_dict.get('granted_scopes', [])

		# Kiểm tra xem có bất kỳ quyền calendar nào không
		calendar_scopes = [
			'https://www.googleapis.com/auth/calendar',
			'https://www.googleapis.com/auth/calendar.readonly',
			'https://www.googleapis.com/auth/calendar.events',
			'https://www.googleapis.com/auth/calendar.events.readonly',
		]

		if not any(scope in granted_scopes for scope in calendar_scopes):
			logger.error(f'User {self.user.id} has not granted any calendar permissions')
			raise CustomHTTPException(
				message=_('google_calendar_permission_denied'),
			)

	def _get_appropriate_calendar_scope(self, creds_dict: dict) -> str:
		"""
		Xác định phạm vi calendar thích hợp dựa trên quyền được cấp

		Args:
		    creds_dict: Dictionary chứa thông tin xác thực và phạm vi

		Returns:
		    str: Phạm vi calendar thích hợp để sử dụng
		"""
		granted_scopes = []

		# Phân tích các phạm vi được cấp
		if isinstance(creds_dict.get('scope'), str):
			granted_scopes = creds_dict.get('scope', '').split(' ')
		elif isinstance(creds_dict.get('scope'), list):
			granted_scopes = creds_dict.get('scope', [])
		elif isinstance(creds_dict.get('granted_scopes'), list):
			granted_scopes = creds_dict.get('granted_scopes', [])

		# Kiểm tra từ quyền cao nhất đến thấp nhất
		if 'https://www.googleapis.com/auth/calendar' in granted_scopes:
			return 'https://www.googleapis.com/auth/calendar'
		elif 'https://www.googleapis.com/auth/calendar.events' in granted_scopes:
			return 'https://www.googleapis.com/auth/calendar.events'
		elif 'https://www.googleapis.com/auth/calendar.readonly' in granted_scopes:
			return 'https://www.googleapis.com/auth/calendar.readonly'
		elif 'https://www.googleapis.com/auth/calendar.events.readonly' in granted_scopes:
			return 'https://www.googleapis.com/auth/calendar.events.readonly'
		else:
			# Mặc định, sử dụng phạm vi chỉ đọc (ít quyền nhất)
			return 'https://www.googleapis.com/auth/calendar.readonly'

	def _refresh_credentials(self) -> bool:
		"""Refresh expired credentials and update user record if DB is available

		Returns:
		    bool: True if refresh was successful, False otherwise
		"""
		try:
			logger.info(f'Refreshing expired Google credentials for user {self.user.id}')

			# Perform the refresh
			request = Request()
			self.creds.refresh(request)

			# If we have DB access, update the stored credentials
			if self.db and self.user_dal:
				# Update the credentials in the user's google_credentials_json
				creds_dict = self.user.get_google_credentials()
				creds_dict['access_token'] = self.creds.token
				creds_dict['expires_at'] = int((datetime.now(timezone('Asia/Ho_Chi_Minh')) + timedelta(seconds=self.creds.expires_in)).timestamp())

				# Update the user record
				self.user_dal.update(self.user.id, {'google_credentials_json': json.dumps(creds_dict)})
				logger.info(f'Updated Google credentials for user {self.user.id}')

			return True
		except Exception as e:
			logger.error(f'Failed to refresh Google credentials: {e}')
			return False

	def _execute_with_refresh(self, api_call):
		"""Execute an API call with automatic token refresh if needed

		Args:
		    api_call: Function that makes the actual API call

		Returns:
		    The result of the API call

		Raises:
		    HttpError: If the API call fails even after token refresh
		"""
		try:
			return api_call()
		except HttpError as error:
			if error.resp.status == 401:
				# Token expired, try to refresh
				logger.info('Received 401, attempting to refresh token')
				if self._refresh_credentials():
					# Re-create service with new credentials
					self.service = build('calendar', 'v3', credentials=self.creds)
					# Retry the API call
					return api_call()
				else:
					# Unable to refresh token
					raise ValueError(_('google_calendar_token_expired'))
			else:
				# Other HTTP error
				raise

	def list_events(self, days: int = 30) -> List[Dict[str, Any]]:
		"""List upcoming calendar events

		Args:
		    days (int): Number of days to look ahead

		Returns:
		    List[Dict[str, Any]]: The raw event dictionaries from Google Calendar API

		Raises:
		    ValueError: If token refresh fails
		"""
		try:
			# Create datetime with timezone information for Asia/Ho_Chi_Minh
			tz = timezone('Asia/Ho_Chi_Minh')
			now = datetime.now(tz) - timedelta(days=300)  # Adjust to UTC+7
			future = now + timedelta(days=days + 300)

			# Format according to RFC3339 standards
			time_min = now.isoformat()
			time_max = future.isoformat()

			def api_call():
				return (
					self.service.events()
					.list(
						calendarId='primary',
						singleEvents=True,
						timeMin=time_min,
						timeMax=time_max,
						orderBy='startTime',
						maxResults=200,
					)
					.execute()
				)

			events_result = self._execute_with_refresh(api_call)

			# Return raw events from Google Calendar API
			return events_result.get('items', [])
		except ValueError as ve:
			# Token refresh failed
			logger.error(f'Token refresh error: {ve}')
			raise
		except HttpError as error:
			logger.error(f'Error listing events: {error}')
			return []
		except Exception as ex:
			logger.error(f'Unexpected error listing events: {ex}')
			return []

	def get_calendar_event_objects(self, days: int = 30) -> List[CalendarEvent]:
		"""Get calendar events as CalendarEvent objects (for API responses)

		Args:
		    days (int): Number of days to look ahead

		Returns:
		    List[CalendarEvent]: List of calendar events

		This method converts raw Google Calendar events to CalendarEvent objects
		"""
		raw_events = self.list_events(days)
		return [self._convert_event(event) for event in raw_events]

	def create_event(self, event_data: dict) -> CalendarEvent | None:
		"""Create a new calendar event

		Args:
		    event_data (dict): Event data

		Returns:
		    Optional[CalendarEvent]: The created calendar event or None if failed

		Raises:
		    ValueError: If token refresh fails
		    CustomHTTPException: If user doesn't have write permission
		"""
		try:
			# Kiểm tra quyền ghi (write) trước khi thực hiện thao tác tạo
			if self.creds.scopes[0] in [
				'https://www.googleapis.com/auth/calendar.readonly',
				'https://www.googleapis.com/auth/calendar.events.readonly',
			]:
				logger.error(f'User {self.user.id} tried to create event but only has read permission')
				raise CustomHTTPException(
					message=_('google_calendar_write_permission_denied'),
				)

			def api_call():
				return self.service.events().insert(calendarId='primary', body=self._prepare_event_body(event_data)).execute()

			event = self._execute_with_refresh(api_call)
			return self._convert_event(event)
		except ValueError as ve:
			# Token refresh failed
			logger.error(f'Token refresh error: {ve}')
			raise
		except HttpError as error:
			logger.error(f'Error creating event: {error}')
			return None

	def update_event(self, event_id: str, event_data: dict) -> CalendarEvent | None:
		"""Update an existing calendar event

		Args:
		    event_id (str): Event ID
		    event_data (dict): Event data

		Returns:
		    Optional[CalendarEvent]: The updated calendar event or None if failed

		Raises:
		    ValueError: If token refresh fails
		    CustomHTTPException: If user doesn't have write permission
		"""
		try:
			# Kiểm tra quyền ghi (write) trước khi thực hiện thao tác cập nhật
			if self.creds.scopes[0] in [
				'https://www.googleapis.com/auth/calendar.readonly',
				'https://www.googleapis.com/auth/calendar.events.readonly',
			]:
				logger.error(f'User {self.user.id} tried to update event but only has read permission')
				raise CustomHTTPException(
					message=_('google_calendar_write_permission_denied'),
				)

			def api_call():
				return (
					self.service.events()
					.update(
						calendarId='primary',
						eventId=event_id,
						body=self._prepare_event_body(event_data),
					)
					.execute()
				)

			event = self._execute_with_refresh(api_call)
			return self._convert_event(event)
		except ValueError as ve:
			# Token refresh failed
			logger.error(f'Token refresh error: {ve}')
			raise
		except HttpError as error:
			logger.error(f'Error updating event: {error}')
			return None

	def delete_event(self, event_id: str) -> bool:
		"""Delete a calendar event

		Args:
		    event_id (str): Event ID

		Returns:
		    bool: True if successful, False otherwise

		Raises:
		    ValueError: If token refresh fails
		    CustomHTTPException: If user doesn't have write permission
		"""
		try:
			# Kiểm tra quyền ghi (write) trước khi thực hiện thao tác xóa
			if self.creds.scopes[0] in [
				'https://www.googleapis.com/auth/calendar.readonly',
				'https://www.googleapis.com/auth/calendar.events.readonly',
			]:
				logger.error(f'User {self.user.id} tried to delete event but only has read permission')
				raise CustomHTTPException(
					message=_('google_calendar_write_permission_denied'),
				)

			def api_call():
				return self.service.events().delete(calendarId='primary', eventId=event_id).execute()

			self._execute_with_refresh(api_call)
			return True
		except ValueError as ve:
			# Token refresh failed
			logger.error(f'Token refresh error: {ve}')
			raise
		except HttpError as error:
			logger.error(f'Error deleting event: {error}')
			return False

	def get_event(self, event_id: str) -> CalendarEvent | None:
		"""Get a calendar event by ID

		Args:
		    event_id (str): Event ID

		Returns:
		    Optional[CalendarEvent]: The calendar event or None if not found

		Raises:
		    ValueError: If token refresh fails
		"""
		try:

			def api_call():
				return self.service.events().get(calendarId='primary', eventId=event_id).execute()

			event = self._execute_with_refresh(api_call)
			return self._convert_event(event)
		except ValueError as ve:
			# Token refresh failed
			logger.error(f'Token refresh error: {ve}')
			raise
		except HttpError as error:
			if error.resp.status == 404:
				logger.warning(f'Event not found: {event_id}')
				return None
			logger.error(f'Error getting event: {error}')
			return None

	def _prepare_event_body(self, data: dict) -> dict:
		"""Prepare event body for Google Calendar API

		Args:
		    data (dict): Event data

		Returns:
		    dict: Formatted event body for Google Calendar API
		"""
		# Ensure dates have timezone information
		start_time = data['start_time']
		end_time = data['end_time']

		# If no timezone info, add Asia/Ho_Chi_Minh timezone
		if start_time.tzinfo is None:
			tz = timezone('Asia/Ho_Chi_Minh')
			start_time = tz.localize(start_time)
			end_time = tz.localize(end_time)

		event_body = {
			'summary': data.get('title'),
			'description': data.get('description'),
			'start': {
				'dateTime': start_time.isoformat(),
				'timeZone': 'Asia/Ho_Chi_Minh',
			},
			'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Asia/Ho_Chi_Minh'},
		}

		# Add location if provided
		if data.get('location'):
			event_body['location'] = data.get('location')

		# Add attendees if provided
		if data.get('attendees'):
			event_body['attendees'] = data.get('attendees')

		# Add recurrence if provided
		if data.get('recurrence'):
			event_body['recurrence'] = data.get('recurrence')

		# Add conference data if it's a Google Meet
		if data.get('is_google_meet', False):
			event_body['conferenceData'] = {
				'createRequest': {
					'requestId': f'meobeo-{data.get("id", uuid.uuid4().hex)}',
					'conferenceSolutionKey': {'type': 'hangoutsMeet'},
				}
			}

		return event_body

	def _convert_event(self, google_event: dict) -> CalendarEvent:
		"""Convert Google Calendar event to our schema

		Args:
		    google_event (dict): Google Calendar event

		Returns:
		    CalendarEvent: Converted calendar event
		"""
		start = google_event['start'].get('dateTime', google_event['start'].get('date'))
		end = google_event['end'].get('dateTime', google_event['end'].get('date'))

		return CalendarEvent(
			id=google_event['id'],
			title=google_event.get('summary'),
			description=google_event.get('description'),
			start_time=start,
			end_time=end,
			location=google_event.get('location'),
			meeting_id=None,  # Can be linked to meeting if needed
		)
