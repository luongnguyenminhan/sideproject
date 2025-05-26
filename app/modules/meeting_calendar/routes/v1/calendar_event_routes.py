"""Calendar event controller for manually triggering sync operations"""

import logging
from datetime import datetime

import jwt
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.core.base_model import APIResponse
from app.core.config import get_settings
from app.core.database import get_db
from app.enums.base_enums import BaseErrorCode
from app.exceptions.exception import CustomHTTPException, NotFoundException
from app.exceptions.handlers import handle_exceptions
from app.http.oauth2 import get_current_user
from app.middleware.translation_manager import _
from app.modules.meeting_calendar.repository.calendar_event_repo import (
	CalendarEventRepo,
)
from app.modules.meeting_files.dal.meeting_file_dal import MeetingFileDAL
from app.modules.meeting_files.models.meeting_file import MeetingFile
from app.utils.minio.minio_handler import minio_handler

# Create router for calendar events
route = APIRouter(prefix='/calendar-events', tags=['Calendar Events'])
logger = logging.getLogger(__name__)


@route.get('/', response_model=APIResponse)
@handle_exceptions
async def list_calendar_events(
	start_date: datetime | None = Query(None, description='Start date for filtering events'),
	end_date: datetime | None = Query(None, description='End date for filtering events'),
	calendar_repo: CalendarEventRepo = Depends(CalendarEventRepo),
	current_user=Depends(get_current_user),
):
	"""List all calendar events for the current user

	This endpoint returns all calendar events that have been synchronized
	for the current user.

	Args:
	    start_date (Optional[datetime]): Start date for filtering
	    end_date (Optional[datetime]): End date for filtering

	Returns:
	    List of calendar events
	"""
	events = calendar_repo.get_calendar_events(current_user['user_id'], start_date, end_date)
	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_events_success'),
		data=events,
	)


@route.post('/meetings/{meeting_id}/sync-to-calendar', response_model=APIResponse)
async def sync_meeting_to_calendar(
	meeting_id: str = Path(..., description='Meeting ID to sync'),
	calendar_repo: CalendarEventRepo = Depends(CalendarEventRepo),
	current_user=Depends(get_current_user),
):
	"""Manually sync a meeting to Google Calendar

	Args:
	    meeting_id (str): Meeting ID to sync

	Returns:
	    Dict[str, Any]: Result of sync operation
	"""
	response = calendar_repo.sync_meeting_to_calendar(meeting_id)
	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('sync_meeting_success'),
		data=[response],
	)


@route.post('/transcripts/{transcript_id}/update-calendar', response_model=APIResponse)
async def update_calendar_with_transcript(
	transcript_id: str = Path(..., description='Transcript ID'),
	calendar_repo: CalendarEventRepo = Depends(CalendarEventRepo),
	current_user=Depends(get_current_user),
):
	"""Update calendar event with transcript information

	Args:
	    transcript_id (str): Transcript ID

	Returns:
	    Dict[str, Any]: Result of update operation
	"""
	response = calendar_repo.update_event_with_transcript(transcript_id)
	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('update_transcript_success'),
		data=response,
	)


@route.post('/meetings/{meeting_id}/update-calendar-with-files', response_model=APIResponse)
async def update_calendar_with_files(
	meeting_id: str = Path(..., description='Meeting ID'),
	calendar_repo: CalendarEventRepo = Depends(CalendarEventRepo),
	current_user=Depends(get_current_user),
):
	"""Update calendar event with meeting files

	Args:
	    meeting_id (str): Meeting ID

	Returns:
	    Dict[str, Any]: Result of update operation
	"""
	result = calendar_repo.update_event_with_files(meeting_id)
	if not result:
		return NotFoundException(_('meeting_not_found'))
	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('update_files_success'),
		data=result,
	)


@route.get('/files/public-download')
async def download_file_public(
	token: str = Query(..., description='JWT token for file access'),
	db: Session = Depends(get_db),
):
	"""Public endpoint for downloading files without authentication.
	Uses JWT tokens for secure access.

	Args:
	    token: Secure JWT token containing file information

	Returns:
	    File as downloadable attachment
	"""
	try:
		# Get settings
		settings = get_settings()

		# Validate the token
		try:
			payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
			logger.debug(f'Valid download token received: {payload}')
		except jwt.ExpiredSignatureError:
			logger.warning('Expired download token')
			raise CustomHTTPException(status_code=status.HTTP_401_UNAUTHORIZED, message=_('token_expired'))
		except jwt.InvalidTokenError as e:
			logger.warning(f'Invalid download token: {e}')
			raise CustomHTTPException(status_code=status.HTTP_401_UNAUTHORIZED, message=_('invalid_token'))

		# Extract file information
		file_id = payload.get('file_id')
		object_name = payload.get('object_name')

		if not file_id or not object_name:
			logger.warning('Missing file_id or object_name in token payload')
			raise CustomHTTPException(
				message=_('missing_file_info'),
			)

		# Get file from database to verify it exists
		meeting_file_dal = MeetingFileDAL(db)
		file: MeetingFile = meeting_file_dal.get_by_id(file_id)

		if not file or file.is_deleted or file.object_name != object_name:
			logger.warning(f'File not found or mismatch: id={file_id}, object_name={object_name}')
			raise CustomHTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				message=_('file_not_found'),
			)

		logger.info(f'Serving file: {file.object_name} (ID: {file.id})')

		try:
			# Download the file from MinIO
			file_content, filename = minio_handler.download_file(object_name)

			# Return the file as an attachment
			return Response(
				content=file_content,
				media_type=file.mime_type or 'application/octet-stream',
				headers={
					'Content-Disposition': f'attachment; filename="{filename}"',
					'Content-Length': str(len(file_content)),
				},
			)
		except Exception as e:
			logger.error(f'Error serving file {file.id}: {str(e)}')
			raise CustomHTTPException(
				message=_('error_retrieving_file'),
			)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f'Unexpected error in public file download: {str(e)}')
		raise CustomHTTPException(
			message=_('error_processing_download_request'),
		)
