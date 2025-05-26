"""Meeting API Routes"""

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.base_model import (
	APIResponse,
	PaginatedResponse,
	PagingInfo,
)
from app.core.database import get_db
from app.enums.base_enums import BaseErrorCode
from app.exceptions.handlers import handle_exceptions
from app.http.oauth2 import get_current_user
from app.middleware.auth_middleware import verify_token
from app.middleware.translation_manager import _
from app.modules.meeting_transcripts.repository.transcript_repo import TranscriptRepo
from app.modules.meetings.repository.meeting_note_repo import MeetingNoteRepo
from app.modules.meetings.repository.meeting_repo import MeetingRepo
from app.modules.meetings.schemas.meeting_schemas import (
	JoinMeetingRequest,
	MeetingCreate,
	MeetingResponse,
	MeetingUpdate,
	SearchMeetingRequest,
)

route = APIRouter(prefix='/meetings', tags=['Meeting'], dependencies=[Depends(verify_token)])


@route.get('/', response_model=APIResponse)
@handle_exceptions
async def get_meetings(
	page: int = Query(1, ge=1),
	page_size: int = Query(10, ge=1, le=100),
	filters_json: str | None = Query(None, description='JSON string of filters'),
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get all meetings for the current user with filtering and pagination

	Supports dynamic filtering through the filters_json parameter:

	Example with structured filters:
	GET /meetings/?page=1&page_size=10&filters_json=[{"field":"title","operator":"contains","value":"Weekly"}]

	To filter by date range:
	GET /meetings/?filters_json=[{"field":"meeting_date","operator":"gte","value":"2023-01-01T00:00:00"},{"field":"meeting_date","operator":"lte","value":"2023-12-31T23:59:59"}]

	To filter by other properties:
	GET /meetings/?filters_json=[{"field":"is_recurring","operator":"eq","value":true},{"field":"language","operator":"eq","value":"en"}]

	Args:
	    page: Page number
	    page_size: Items per page
	    filters_json: JSON string of filters for dynamic filtering

	Returns:
	    List of meetings with pagination info
	"""
	# get current user
	meeting_repo = MeetingRepo(db)

	# Parse dynamic filters if provided
	filters = []
	if filters_json:
		try:
			filters = json.loads(filters_json)
			if not isinstance(filters, list):
				filters = []
		except json.JSONDecodeError:
			filters = []
		except Exception:
			filters = []

	# Create request object compatible with repository
	request = SearchMeetingRequest(page=page, page_size=page_size, filters=filters)

	result = meeting_repo.get_user_meetings(current_user_payload['user_id'], request.model_dump())

	meetings = [MeetingResponse.model_validate(meeting.to_dict()) for meeting in result.items]

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_meetings_success'),
		data=PaginatedResponse(
			items=meetings,
			paging=PagingInfo(
				total=result.total_count,
				total_pages=result.total_pages,
				page=page,
				page_size=page_size,
			),
		),
	)


@route.get('/{meeting_id}', response_model=APIResponse)
@handle_exceptions
async def get_meeting(
	meeting_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get a specific meeting by ID

	Args:
	    meeting_id: Meeting ID

	Returns:
	    Meeting details
	"""
	meeting_repo = MeetingRepo(db)
	meeting = meeting_repo.get_meeting_by_id(meeting_id, current_user_payload['user_id'])
	meeting_data = MeetingResponse.model_validate(meeting.to_dict())

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_meeting_success'),
		data=meeting_data,
	)


@route.get('/{meeting_id}/contents', response_model=APIResponse)
@handle_exceptions
async def get_meeting_notes_and_transcripts(
	meeting_id: str,
	include_items: bool = Query(False, description='Include meeting items in notes'),
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get meeting notes and transcripts for a specific meeting

	This endpoint retrieves all notes and transcripts associated with a meeting.

	Args:
	    meeting_id: Meeting ID
	    include_items: Whether to include meeting items (decisions, action items, etc.) in the response

	Returns:
	    Meeting notes and transcripts data
	"""
	# Initialize repositories
	meeting_repo = MeetingRepo(db)
	meeting_note_repo = MeetingNoteRepo(db)
	transcript_repo = TranscriptRepo(db)

	# Verify meeting exists and belongs to user
	meeting = meeting_repo.get_meeting_by_id(meeting_id, current_user_payload['user_id'])

	# Get meeting notes
	notes = meeting_note_repo.get_meeting_notes(meeting_id, current_user_payload['user_id'], include_all_versions=False)

	# Get latest note with items and chunks if requested
	latest_note = None
	if notes:
		latest_note_id = notes[0]['id']  # First note is the latest since we sort by creation date desc
		latest_note = meeting_note_repo.get_note_by_id(
			latest_note_id,
			current_user_payload['user_id'],
			include_items=include_items,
		)

	# Get transcripts
	transcripts = transcript_repo.get_meeting_transcripts(meeting_id, current_user_payload['user_id'])
	latest_transcript = None
	if transcripts:
		latest_transcript_id = transcripts[0]['id']
		latest_transcript = transcript_repo.get_transcript_by_id(latest_transcript_id, current_user_payload['user_id'])
	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_meeting_notes_transcripts_success'),
		data={
			'meeting': MeetingResponse.model_validate(meeting.to_dict()),
			'latest_note': latest_note,
			'transcripts': transcripts,
			'notes': notes,
			'latest_transcript': latest_transcript,
		},
	)


@route.post('/', response_model=APIResponse)
@handle_exceptions
async def create_meeting(
	meeting_data: MeetingCreate,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Create a new meeting

	Args:
	    meeting_data: Meeting data

	Returns:
	    Created meeting details
	"""
	meeting_repo = MeetingRepo(db)
	tags = meeting_data.tags
	meeting_dict = meeting_data.model_dump(exclude={'tags'})
	meeting = meeting_repo.create_meeting(current_user_payload['user_id'], meeting_dict, tags)
	meeting_response = MeetingResponse.model_validate(meeting.to_dict())

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('create_meeting_success'),
		data=meeting_response,
	)


@route.put('/{meeting_id}', response_model=APIResponse)
@handle_exceptions
async def update_meeting(
	meeting_id: str,
	meeting_data: MeetingUpdate,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Update an existing meeting

	Args:
	    meeting_id: Meeting ID
	    meeting_data: Updated meeting data

	Returns:
	    Updated meeting details
	"""

	meeting_repo = MeetingRepo(db)
	meeting_dict = meeting_data.model_dump(exclude_unset=True)
	meeting = meeting_repo.update_meeting(meeting_id, current_user_payload['user_id'], meeting_dict)
	meeting_response = MeetingResponse.model_validate(meeting.to_dict())

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('update_meeting_success'),
		data=meeting_response,
	)


@route.delete('/{meeting_id}', response_model=APIResponse)
@handle_exceptions
async def delete_meeting(
	meeting_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Delete a meeting

	Args:
	    meeting_id: Meeting ID

	Returns:
	    Success message
	"""
	meeting_repo = MeetingRepo(db)
	result = meeting_repo.delete_meeting(meeting_id, current_user_payload['user_id'])

	if result:
		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
			message=_('meeting_deleted_successfully'),
			data={'success': True},
		)
	else:
		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_FAIL,
			message=_('delete_meeting_failed'),
			data={'success': False},
		)


@route.post('/join', response_model=APIResponse)
@handle_exceptions
async def join_meeting(
	join_data: JoinMeetingRequest,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Record when a user joins a meeting

	Args:
	    join_data: Join meeting data including title, platform, and timestamp

	Returns:
	    Updated or newly created meeting details
	"""
	meeting_repo = MeetingRepo(db)
	meeting_dict = join_data.model_dump()
	meeting = meeting_repo.join_meeting(current_user_payload['user_id'], meeting_dict)
	meeting_response = MeetingResponse.model_validate(meeting.to_dict())

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('join_meeting_success'),
		data=meeting_response,
	)
