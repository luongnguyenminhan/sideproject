"""Meeting File API Routes"""

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile
from sqlalchemy.orm import Session


from app.core.base_model import APIResponse, PaginatedResponse, PagingInfo
from app.core.database import get_db
from app.enums.base_enums import BaseErrorCode
from app.enums.meeting_enums import FileTypeEnum
from app.exceptions.handlers import handle_exceptions
from app.http.oauth2 import get_current_user
from app.middleware.auth_middleware import verify_token
from app.middleware.translation_manager import _
from app.modules.meeting_files.repository.meeting_file_repo import MeetingFileRepo
from app.modules.meeting_files.schemas.meeting_file_schemas import (
	FileUploadResponse,
	MeetingFileResponse,
	SearchMeetingFileRequest,
	SearchMeetingFileResponse,
)

route = APIRouter(
	prefix='/meeting-files',
	tags=['Meeting Files'],
	dependencies=[Depends(verify_token)],
)


@route.get('/meeting/{meeting_id}', response_model=APIResponse)
@handle_exceptions
async def get_meeting_files(
	meeting_id: str,
	file_type: str | None = None,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get all files for a meeting

	Args:
	    meeting_id: Meeting ID
	    file_type: Optional file type filter

	Returns:
	    List of files
	"""
	file_repo = MeetingFileRepo(db)
	files = file_repo.get_meeting_files(meeting_id, current_user_payload['user_id'], file_type)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_files_success'),
		data=files,
	)


@route.get('/{file_id}', response_model=APIResponse)
@handle_exceptions
async def get_file(
	file_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get a specific file by ID

	Args:
	    file_id: File ID

	Returns:
	    File details
	"""
	file_repo = MeetingFileRepo(db)
	file = file_repo.get_file_by_id(file_id, current_user_payload['user_id'])

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_file_success'),
		data=file,
	)


@route.get('/meeting/{meeting_id}/audio', response_model=APIResponse)
@handle_exceptions
async def get_meeting_audio_files(
	meeting_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get all audio files for a meeting

	Args:
	    meeting_id: Meeting ID

	Returns:
	    List of audio files
	"""
	file_repo = MeetingFileRepo(db)
	files = file_repo.get_meeting_files(meeting_id, current_user_payload['user_id'], FileTypeEnum.AUDIO.value)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_audio_files_success'),
		data=files,
	)


@route.get('/meeting/{meeting_id}/transcript', response_model=APIResponse)
@handle_exceptions
async def get_meeting_transcript_files(
	meeting_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get all transcript files for a meeting

	Args:
	    meeting_id: Meeting ID

	Returns:
	    List of transcript files
	"""
	file_repo = MeetingFileRepo(db)
	files = file_repo.get_meeting_files(meeting_id, current_user_payload['user_id'], FileTypeEnum.TRANSCRIPT.value)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_transcript_files_success'),
		data=files,
	)


@route.post('/upload/{meeting_id}', response_model=FileUploadResponse)
@handle_exceptions
async def upload_file(
	meeting_id: str,
	file_type: str = Form(FileTypeEnum.AUDIO.value),
	file: UploadFile = File(...),
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Upload a file to a meeting

	Args:
	    meeting_id: Meeting ID
	    file_type: Type of file (audio, document, etc.)
	    file: File to upload

	Returns:
	    Uploaded file details
	"""
	file_repo = MeetingFileRepo(db)
	file_data = await file_repo.upload_meeting_file(
		meeting_id=meeting_id,
		user_id=current_user_payload['user_id'],
		file=file,
		file_type=file_type,
	)

	return FileUploadResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('file_upload_success'),
		data=file_data,
	)


@route.get('/download/{file_id}')
@handle_exceptions
async def download_file(
	file_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Download a file

	Args:
	    file_id: File ID

	Returns:
	    File content as a download
	"""
	file_repo = MeetingFileRepo(db)
	file_data = file_repo.download_file(file_id, current_user_payload['user_id'])

	return Response(
		content=file_data['content'],
		media_type=file_data['content_type'],
		headers={'Content-Disposition': f'attachment; filename={file_data["filename"]}'},
	)


@route.delete('/{file_id}', response_model=APIResponse)
@handle_exceptions
async def delete_file(
	file_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Delete a file

	Args:
	    file_id: File ID

	Returns:
	    Success message
	"""
	file_repo = MeetingFileRepo(db)
	result = file_repo.delete_file(file_id, current_user_payload['user_id'])

	if result:
		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
			message=_('file_deleted_successfully'),
			data={'success': True},
		)
	else:
		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_FAIL,
			message=_('delete_file_failed'),
			data={'success': False},
		)


@route.get('/search', response_model=SearchMeetingFileResponse)
@handle_exceptions
async def search_files_get(
	page: int = Query(1, ge=1),
	page_size: int = Query(10, ge=1),
	filters_json: str | None = Query(None, description='JSON string of filters'),
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Search meeting files with dynamic filtering and pagination

	Supports dynamic filtering through the filters_json parameter:

	Example with structured filters:
	GET /meeting-files/search?page=1&page_size=10&filters_json=[{"field":"file_type","operator":"eq","value":"AUDIO"}]

	To search across multiple fields:
	GET /meeting-files/search?filters_json=[{"field":"file_size_bytes","operator":"gt","value":1000000}]

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
	    List of meeting files with pagination info
	"""
	import json

	# Parse filters from JSON
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

	# Create request
	request = SearchMeetingFileRequest(page=page, page_size=page_size, filters=filters)

	# Search files
	file_repo = MeetingFileRepo(db)
	result = file_repo.search_files(current_user_payload['user_id'], request.model_dump())

	# Prepare response
	files = [MeetingFileResponse.model_validate(file.to_dict()) for file in result.items]

	return SearchMeetingFileResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('search_successful'),
		data=PaginatedResponse(
			items=files,
			paging=PagingInfo(
				total=result.total_count,
				total_pages=result.total_pages,
				page=page,
				page_size=page_size,
			),
		),
	)


@route.get('/note/{note_id}/pdf', response_model=None)
@handle_exceptions
async def download_note_as_pdf(
	note_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Generate and download a meeting note as PDF

	Args:
	    note_id: Note ID

	Returns:
	    PDF file as direct download
	"""
	file_repo = MeetingFileRepo(db)
	pdf_data, filename = file_repo.generate_note_pdf(note_id, current_user_payload['user_id'])

	return Response(
		content=pdf_data,
		media_type='application/pdf',
		headers={'Content-Disposition': f'attachment; filename={filename}'},
	)


@route.post('/note/{note_id}/save-as-pdf', response_model=APIResponse)
@handle_exceptions
async def save_note_as_pdf(
	note_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Convert a meeting note to PDF and save it as a file

	Args:
	    note_id: Note ID

	Returns:
	    Created file details
	"""
	file_repo = MeetingFileRepo(db)
	file_data = await file_repo.save_note_as_pdf(note_id, current_user_payload['user_id'])

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('note_pdf_saved_successfully'),
		data=file_data,
	)
