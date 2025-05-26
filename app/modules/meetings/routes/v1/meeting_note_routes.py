"""Meeting API Routes"""

import json
from typing import List

from fastapi import APIRouter, Depends, Path, Query
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
from app.modules.meetings.models.meeting_note import MeetingNote
from app.modules.meetings.repository.meeting_note_repo import MeetingNoteRepo
from app.modules.meetings.schemas.meeting_note_schemas import (
	AttendeesRequest,
	MeetingNoteResponse,
	SearchMeetingNoteRequest,
)

route = APIRouter(prefix='/notes', tags=['Meeting Notes'], dependencies=[Depends(verify_token)])


@route.get('/', response_model=APIResponse)
@handle_exceptions
async def get_meeting_notes(
	page: int = Query(1, ge=1),
	page_size: int = Query(10, ge=1, le=100),
	filters_json: str | None = Query(None, description='JSON string of filters'),
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get all meeting notes for the current user with filtering and pagination

	Supports dynamic filtering through the filters_json parameter:

	Example with structured filters:
	GET /notes/?page=1&page_size=10&filters_json=[{"field":"title","operator":"contains","value":"Weekly"}]

	To filter by date range:
	GET /notes/?filters_json=[{"field":"meeting_date","operator":"gte","value":"2023-01-01T00:00:00"},{"field":"meeting_date","operator":"lte","value":"2023-12-31T23:59:59"}]

	To filter by other properties:
	GET /notes/?filters_json=[{"field":"is_recurring","operator":"eq","value":true},{"field":"language","operator":"eq","value":"en"}]

	Args:
	    page: Page number
	    page_size: Items per page
	    filters_json: JSON string of filters for dynamic filtering

	Returns:
	    List of meetings with pagination info
	"""
	# get current user
	meeting_note_repo = MeetingNoteRepo(db)

	# Parse dynamic filters if provided
	filters = []
	if filters_json:
		try:
			filters = json.loads(filters_json)
			if not isinstance(filters, list):
				filters = []
		except Exception:
			filters = []

	# Create request object compatible with repository
	request = SearchMeetingNoteRequest(page=page, page_size=page_size, filters=filters)

	result = meeting_note_repo.get_meeting_notes(current_user_payload['user_id'], request.model_dump())

	meetings = [MeetingNoteResponse.model_validate(meeting.to_dict()) for meeting in result.items]

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


@route.get('/meeting/{meeting_id}', response_model=APIResponse)
@handle_exceptions
async def get_meeting_note(
	meeting_id: str = Path(..., description='Meeting ID'),
	include_all_versions: bool = Query(False, description='Include all versions instead of just the latest'),
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get all notes for a specific meeting

	Args:
	    meeting_id: The ID of the meeting to get notes for
	    include_all_versions: Whether to include all versions or only the latest

	Returns:
	    List of meeting notes
	"""
	meeting_note_repo = MeetingNoteRepo(db)

	notes = meeting_note_repo.get_meeting_notes(
		meeting_id,
		current_user_payload['user_id'],
		include_all_versions=include_all_versions,
	)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_meeting_notes_success'),
		data=notes,
	)


@route.get('/{note_id}', response_model=APIResponse)
@handle_exceptions
async def get_note_by_id(
	note_id: str = Path(..., description='Note ID'),
	include_items: bool = Query(False, description='Include meeting items'),
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get a specific meeting note by ID

	Args:
	    note_id: Note ID
	    include_items: Whether to include meeting items (decisions, action items, etc.)

	Returns:
	    Meeting note data
	"""
	meeting_note_repo = MeetingNoteRepo(db)

	note = meeting_note_repo.get_note_by_id(note_id, current_user_payload['user_id'], include_items=include_items)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_note_success'),
		data=note,
	)


@route.post('/generate/{meeting_id}/transcripts/{transcript_id}', response_model=APIResponse)
@handle_exceptions
async def generate_meeting_note(
	meeting_id: str = Path(..., description='Meeting ID'),
	transcript_id: str = Path(..., description='Transcript ID to generate note from'),
	meeting_type: str = Query(..., description='Type of the meeting'),
	custom_prompt: str | None = Query(None, description='Custom prompt for note generation'),
	language: str | None = Query(None, description='Language code for note generation'),
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Generate a meeting note from a transcript

	Args:
	    meeting_id: Meeting ID
	    transcript_id: Transcript ID to use for note generation
	    language: Optional language code for note generation

	Returns:
	    Generated meeting note with items
	"""
	meeting_note_repo = MeetingNoteRepo(db)

	note = await meeting_note_repo.generate_meeting_note(
		meeting_id,
		current_user_payload['user_id'],
		transcript_id,
		language,
		meeting_type,
		custom_prompt,
	)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('generate_note_success'),
		data=note,
	)


@route.delete('/{note_id}', response_model=APIResponse)
@handle_exceptions
async def delete_note(
	note_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Delete a meeting note

	Args:
	    note_id: Note ID to delete

	Returns:
	    Success message
	"""
	meeting_note_repo = MeetingNoteRepo(db)

	result = meeting_note_repo.delete_note(note_id, current_user_payload['user_id'])

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('delete_note_success'),
		data={'success': result},
	)


@route.get('/transcript/{transcript_id}', response_model=APIResponse)
@handle_exceptions
async def get_notes_by_transcript_id(
	transcript_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get a specific meeting note by transcript ID

	Args:
	    transcript_id: Transcript ID

	Returns:
	    Transcript details
	"""
	meeting_note_repo = MeetingNoteRepo(db)
	meeting_notes: List[MeetingNote] = meeting_note_repo.get_meeting_transcript_notes(transcript_id, current_user_payload['user_id'])
	if not meeting_notes:
		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_FAIL,
			message=_('transcript_not_found'),
			data=None,
		)
	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_transcripts_success'),
		data=meeting_notes,
	)


@route.get('/{note_id}/items', response_model=APIResponse)
@handle_exceptions
async def get_note_items(
	note_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get all items for a specific note

	Args:
	    note_id: Note ID

	Returns:
	    List of note items
	"""
	meeting_note_repo = MeetingNoteRepo(db)

	items = meeting_note_repo.get_note_items(note_id, current_user_payload['user_id'])

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_note_items_success'),
		data=items,
	)


@route.get('/{note_id}/items/{item_id}', response_model=APIResponse)
@handle_exceptions
async def get_note_item(
	note_id: str,
	item_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get a specific note item by ID

	Args:
	    note_id: Note ID
	    item_id: Item ID

	Returns:
	    Note item details
	"""
	meeting_note_repo = MeetingNoteRepo(db)

	item = meeting_note_repo.get_note_item(note_id, item_id, current_user_payload['user_id'])

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_note_item_success'),
		data=item,
	)


@route.put('/{note_id}/items/{item_id}', response_model=APIResponse)
@handle_exceptions
async def update_note_item(
	note_id: str,
	item_id: str,
	item_data: dict,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Update a specific note item

	Args:
	    note_id: Note ID
	    item_id: Item ID
	    item_data: Updated item data

	Returns:
	    Updated note item details
	"""
	meeting_note_repo = MeetingNoteRepo(db)

	updated_item = meeting_note_repo.update_note_item(note_id, item_id, current_user_payload['user_id'], item_data)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('update_note_item_success'),
		data=updated_item,
	)


@route.delete('/{note_id}/items/{item_id}', response_model=APIResponse)
@handle_exceptions
async def delete_note_item(
	note_id: str,
	item_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Delete a specific note item

	Args:
	    note_id: Note ID
	    item_id: Item ID

	Returns:
	    Success message
	"""
	meeting_note_repo = MeetingNoteRepo(db)

	result = meeting_note_repo.delete_note_item(note_id, item_id, current_user_payload['user_id'])

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('delete_note_item_success'),
		data={'success': result},
	)


@route.post('/{note_id}/items/{item_id}/events', response_model=APIResponse)
@handle_exceptions
async def add_note_item_event(
	note_id: str,
	item_id: str,
	emails: AttendeesRequest,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Add an event to a specific note item and sync to calendar

	This endpoint adds calendar event to a meeting note item (task)
	and creates a corresponding event in Google Calendar with attendees.

	Args:
	    note_id: Note ID
	    item_id: Item ID
	    emails: List of email addresses to add as attendees

	Returns:
	    Updated item with calendar event details
	"""
	meeting_note_repo = MeetingNoteRepo(db)

	added_event = await meeting_note_repo.add_note_item_event(note_id, item_id, current_user_payload['user_id'], emails.emails)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('add_note_item_event_success'),
		data=added_event,
	)
