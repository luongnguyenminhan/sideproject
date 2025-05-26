"""Transcript API Routes"""

import json

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.base_model import APIResponse, PaginatedResponse, PagingInfo
from app.core.database import get_db
from app.enums.base_enums import BaseErrorCode
from app.exceptions.handlers import handle_exceptions
from app.http.oauth2 import get_current_user
from app.middleware.auth_middleware import verify_token
from app.middleware.translation_manager import _
from app.modules.meeting_transcripts.repository.transcript_repo import TranscriptRepo
from app.modules.meeting_transcripts.schemas.transcript_schemas import (
	SearchTranscriptRequest,
	SearchTranscriptResponse,
	TranscriptCreate,
	TranscriptResponse,
)

route = APIRouter(prefix='/transcripts', tags=['Transcript'], dependencies=[Depends(verify_token)])


@route.get('/meeting/{meeting_id}', response_model=APIResponse)
@handle_exceptions
async def get_meeting_transcripts(
	meeting_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get all transcripts for a meeting

	Args:
	    meeting_id: Meeting ID

	Returns:
	    List of transcripts
	"""
	transcript_repo = TranscriptRepo(db)
	transcripts = transcript_repo.get_meeting_transcripts(meeting_id, current_user_payload['user_id'])

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_transcripts_success'),
		data=transcripts,
	)


@route.get('/{transcript_id}', response_model=APIResponse)
@handle_exceptions
async def get_transcript(
	transcript_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get a specific transcript by ID

	Args:
	    transcript_id: Transcript ID

	Returns:
	    Transcript details
	"""
	transcript_repo = TranscriptRepo(db)
	transcript = transcript_repo.get_transcript_by_id(transcript_id, current_user_payload['user_id'])

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_transcript_success'),
		data=transcript,
	)


@route.post('/text/{meeting_id}', response_model=APIResponse)
@handle_exceptions
async def create_transcript_from_uploaded_text(
	meeting_id: str,
	transcript_data: TranscriptCreate,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Create a new transcript from text data (manual upload)

	Args:
	    meeting_id: Meeting ID
	    transcript_data: Transcript data

	Returns:
	    Created transcript
	"""
	transcript_repo = TranscriptRepo(db)
	transcript = await transcript_repo.create_transcript_from_text(meeting_id, current_user_payload['user_id'], transcript_data.model_dump())

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('create_transcript_success'),
		data=transcript,
	)


@route.post('/text', response_model=APIResponse)
@handle_exceptions
async def create_transcript_from_text(
	transcript_data: TranscriptCreate,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Create a new transcript from text data (manual upload)

	Args:
	    meeting_id: Meeting ID
	    transcript_data: Transcript data

	Returns:
	    Created transcript
	"""
	transcript_repo = TranscriptRepo(db)
	transcript = await transcript_repo.create_new_transcript_from_text(current_user_payload['user_id'], transcript_data.model_dump())

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('create_transcript_success'),
		data=transcript,
	)


@route.post('/audio/{meeting_id}', response_model=APIResponse)
@handle_exceptions
async def create_transcript_from_audio(
	meeting_id: str,
	audio_file: UploadFile = File(...),
	language: str | None = Form(None),
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Create a new transcript from audio file using background task processing

	Args:
	    meeting_id: Meeting title alias
	    audio_file: Audio file
	    language: Language code for transcription (optional)

	Returns:
	    Created transcript placeholder with processing status
	"""
	# Process the audio file (save it temporarily)
	file_location = f'/tmp/{audio_file.filename}'
	with open(file_location, 'wb+') as file_object:
		file_object.write(await audio_file.read())

	transcript_repo = TranscriptRepo(db)
	transcript = await transcript_repo.create_transcript_from_audio(meeting_id, current_user_payload['user_id'], file_location, language)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('transcript_processing_started'),
		data={
			**transcript,
			'processing_message': 'Audio file is being processed in the background. Check back later for the results.',
		},
	)


@route.post('/audio', response_model=APIResponse)
@handle_exceptions
async def create_new_transcript_from_audio(
	audio_file: UploadFile = File(...),
	language: str | None = Form(None),
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Create a new transcript from audio file using background task processing

	Args:
	    audio_file: Audio file
	    language: Language code for transcription (optional)

	Returns:
	    Created transcript placeholder with processing status
	"""
	# Process the audio file (save it temporarily)
	file_location = f'/tmp/{audio_file.filename}'
	with open(file_location, 'wb+') as file_object:
		file_object.write(await audio_file.read())

	transcript_repo = TranscriptRepo(db)
	transcript = await transcript_repo.create_new_transcript_from_audio(current_user_payload['user_id'], file_location, language)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('transcript_processing_started'),
		data={
			**transcript,
			'processing_message': 'Audio file is being processed in the background. Check back later for the results.',
		},
	)


@route.delete('/{transcript_id}', response_model=APIResponse)
@handle_exceptions
async def delete_transcript(
	transcript_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Delete a transcript

	Args:
	    transcript_id: Transcript ID

	Returns:
	    Success message
	"""
	transcript_repo = TranscriptRepo(db)
	result = transcript_repo.delete_transcript(transcript_id, current_user_payload['user_id'])

	if result:
		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
			message=_('transcript_deleted_successfully'),
			data={'success': True},
		)
	else:
		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_FAIL,
			message=_('delete_transcript_failed'),
			data={'success': False},
		)


@route.get('/', response_model=SearchTranscriptResponse)
@handle_exceptions
async def search_transcripts(
	page: int = Query(1, ge=1),
	page_size: int = Query(10, ge=1),
	filters_json: str | None = Query(None, description='JSON string of filters'),
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Search transcripts with dynamic filtering and pagination

	Supports dynamic filtering through the filters_json parameter:

	Example with structured filters:
	GET /transcripts/?page=1&page_size=10&filters_json=[{"field":"language","operator":"eq","value":"en"}]

	To search across multiple fields:
	GET /transcripts/?filters_json=[{"field":"content","operator":"contains","value":"important topic"}]

	Available operators:
	- eq: Equal
	- ne: Not equal
	- lt: Less than
	- lte: Less than or equal
	- gt: Greater than
	- gte: Greater than or equal
	- contains: String contains
	- startswith: String starts with
	- endswith: String ends with
	- in_list: Value is in a list
	- not_in: Value is not in a list
	- is_null: Field is null
	- is_not_null: Field is not null

	Args:
	    page: Page number
	    page_size: Items per page
	    filters_json: JSON string of filters for dynamic filtering

	Returns:
	    List of transcripts with pagination info
	"""
	# Parse filters from JSON
	filters = []
	if filters_json:
		try:
			filters = json.loads(filters_json)
			if not isinstance(filters, list):
				filters = []
		except Exception:
			filters = []

	# Create request
	request = SearchTranscriptRequest(page=page, page_size=page_size, filters=filters)

	# Search transcripts
	transcript_repo = TranscriptRepo(db)
	result = transcript_repo.search_transcripts(current_user_payload['user_id'], request)

	# Prepare response
	transcripts = [TranscriptResponse.model_validate(transcript.to_dict()) for transcript in result.items]

	return SearchTranscriptResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('search_successful'),
		data=PaginatedResponse(
			items=transcripts,
			paging=PagingInfo(
				total=result.total_count,
				total_pages=result.total_pages,
				page=page,
				page_size=page_size,
			),
		),
	)
