"""File API Routes"""

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session


from app.core.base_model import APIResponse
from app.core.database import get_db
from app.enums.base_enums import BaseErrorCode
from app.enums.meeting_enums import FileTypeEnum
from app.exceptions.handlers import handle_exceptions
from app.http.oauth2 import get_current_user
from app.middleware.auth_middleware import verify_token
from app.middleware.translation_manager import _
from app.modules.meeting_files.repository.file_repo import FileRepo

route = APIRouter(prefix='/files', tags=['Files'], dependencies=[Depends(verify_token)])


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
	file_repo = FileRepo(db)
	files = file_repo.get_meeting_files(meeting_id, current_user_payload['user_id'], file_type)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_files_success'),
		data=files,
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
	file_repo = FileRepo(db)
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
	file_repo = FileRepo(db)
	files = file_repo.get_meeting_files(meeting_id, current_user_payload['user_id'], FileTypeEnum.TRANSCRIPT.value)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('get_transcript_files_success'),
		data=files,
	)


@route.post('/meeting/{meeting_id}', response_model=APIResponse)
@handle_exceptions
async def upload_meeting_file(
	meeting_id: str,
	file: UploadFile = File(...),
	file_type: str = Form(FileTypeEnum.AUDIO.value),
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Upload a file for a meeting

	Args:
	    meeting_id: Meeting ID
	    file: File to upload
	    file_type: Type of file (audio, transcript, etc.)

	Returns:
	    Uploaded file metadata
	"""
	file_repo = FileRepo(db)
	file_metadata = await file_repo.upload_meeting_file(meeting_id, current_user_payload['user_id'], file, file_type)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('file_uploaded_successfully'),
		data=file_metadata,
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
	file_repo = FileRepo(db)
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
