"""Calendar API Routes"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.enums.base_enums import BaseErrorCode
from app.exceptions.exception import CustomHTTPException
from app.exceptions.handlers import handle_exceptions
from app.http.oauth2 import get_current_user
from app.middleware.translation_manager import _
from app.modules.meeting_calendar.repository.calendar_repo import CalendarRepo
from app.modules.meeting_calendar.repository.calendar_sync_repo import CalendarSyncRepo
from app.modules.meeting_calendar.schemas.calendar_schemas import (
	CalendarEventCreate,
	CalendarResponse,
	CalendarSyncRequest,
	CalendarSyncResponse,
	CalendarSyncStats,
)
from app.modules.users.models.users import User
from app.modules.users.repository.user_repo import UserRepo
from fastapi import status

route = APIRouter(prefix='/calendar', tags=['Calendar'])


async def get_current_user_with_calendar(db: Session = Depends(get_db), current_user_dict: dict = Depends(get_current_user)):
	"""Get current user with calendar integration"""
	user_repo = UserRepo(db)
	user = user_repo.get_user_by_id(current_user_dict['user_id'])
	if not user or not user.google_credentials_json:
		raise CustomHTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			message=_('invalid_calendar_credentials'),
		)
	return user


@route.get('/events', response_model=CalendarSyncResponse)
@handle_exceptions
async def list_calendar_events(
	db: Session = Depends(get_db),
	current_user=Depends(get_current_user_with_calendar),
	auto_sync: bool = Query(True, description='Whether to automatically sync calendar events to meetings'),
):
	"""Get calendar events for the current user and optionally sync with meetings

	This endpoint fetches events from the user's calendar provider and can
	automatically sync them with the meetings table when auto_sync is True.
	Events with meeting links (like Google Meet links) will be converted to meetings.

	Args:
	    auto_sync: If True, automatically sync calendar events to meetings

	Returns:
	    Calendar events and sync statistics if auto_sync is True
	"""
	calendar_repo = CalendarRepo(db)
	days = 30

	# Get calendar events for response (as CalendarEvent objects)
	event_objects = calendar_repo.get_calendar_event_objects(current_user, days=days)

	# If auto_sync is enabled, sync events to meetings
	if auto_sync:
		# Get raw event dictionaries for syncing
		raw_events = calendar_repo.get_calendar_events(current_user, days=days)

		# Initialize sync repository
		sync_repo = CalendarSyncRepo(db)

		# Perform sync with raw events data
		sync_stats = sync_repo.sync_events_to_meetings(current_user.id, raw_events)

		# Return event objects with sync stats
		return CalendarSyncResponse(
			error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
			message=_('calendar_events_synced'),
			data=event_objects,
			sync_stats=CalendarSyncStats(**sync_stats),
		)

	# Return events without sync if auto_sync is False
	return CalendarSyncResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_events_success'),
		data=event_objects,
	)


@route.post('/events', response_model=CalendarResponse)
@handle_exceptions
async def create_calendar_event(
	event: CalendarEventCreate,
	db: Session = Depends(get_db),
	current_user=Depends(get_current_user_with_calendar),
):
	"""Create a new calendar event"""
	calendar_repo = CalendarRepo(db)
	created_event = calendar_repo.create_event_in_calendar(current_user, event)
	if not created_event:
		raise CustomHTTPException(message=_('calendar_sync_failed'))

	return CalendarResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('create_calendar_event_success'),
		data=[created_event],
	)


@route.put('/events/{event_id}', response_model=CalendarResponse)
@handle_exceptions
async def update_calendar_event(
	event_id: str,
	event: CalendarEventCreate,
	db: Session = Depends(get_db),
	current_user=Depends(get_current_user_with_calendar),
):
	"""Update an existing calendar event"""
	calendar_repo = CalendarRepo(db)
	updated_event = calendar_repo.update_event_in_calendar(current_user, event_id, event)
	if not updated_event:
		raise CustomHTTPException(status_code=status.HTTP_404_NOT_FOUND, message=_('calendar_event_not_found'))

	return CalendarResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('update_calendar_event_success'),
		data=[updated_event],
	)


@route.delete('/events/{event_id}', response_model=CalendarResponse)
@handle_exceptions
async def delete_calendar_event(
	event_id: str,
	db: Session = Depends(get_db),
	current_user=Depends(get_current_user_with_calendar),
):
	"""Delete a calendar event"""
	calendar_repo = CalendarRepo(db)
	success = calendar_repo.delete_event_from_calendar(current_user, event_id)
	if not success:
		raise CustomHTTPException(status_code=status.HTTP_404_NOT_FOUND, message=_('calendar_event_not_found'))

	return CalendarResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('delete_calendar_event_success'),
		data=[],
	)


@route.post('/sync', response_model=CalendarSyncResponse)
@handle_exceptions
async def sync_calendar(
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user_with_calendar),
	sync_request: CalendarSyncRequest = None,
):
	"""Manually trigger calendar events synchronization with meetings

	This endpoint will fetch calendar events and synchronize them with meetings,
	creating or updating meetings for events that contain meeting links.

	Args:
	    sync_request: Optional parameters for the sync operation

	Returns:
	    Sync statistics and synced events
	"""
	if sync_request is None:
		sync_request = CalendarSyncRequest()

	# Fetch calendar events for response (as CalendarEvent objects)
	calendar_repo = CalendarRepo(db)
	event_objects = calendar_repo.get_calendar_event_objects(current_user, days=sync_request.days_range)

	# Get raw events for syncing
	raw_events = calendar_repo.get_calendar_events(current_user, days=sync_request.days_range)

	# Sync events to meetings
	sync_repo = CalendarSyncRepo(db)
	sync_stats = sync_repo.sync_events_to_meetings(current_user.id, raw_events)

	return CalendarSyncResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('calendar_sync_success'),
		data=event_objects,
		sync_stats=CalendarSyncStats(**sync_stats),
	)
