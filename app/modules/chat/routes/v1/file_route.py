from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.enums.base_enums import BaseErrorCode
from app.http.oauth2 import get_current_user
from app.modules.chat.repository.file_repo import FileRepo
from app.modules.chat.schemas.file_request import FileListRequest
from app.modules.chat.schemas.file_response import FileResponse, UploadFileResponse
from app.core.base_model import APIResponse, PaginatedResponse, PagingInfo
from app.exceptions.handlers import handle_exceptions
from app.middleware.auth_middleware import verify_token
from app.middleware.translation_manager import _
from typing import List, Optional
import io

route = APIRouter(prefix='/files', tags=['Files'], dependencies=[Depends(verify_token)])


@route.post('/upload', response_model=APIResponse)
@handle_exceptions
async def upload_files(
	files: List[UploadFile] = File(...),
	conversation_id: Optional[str] = Form(None),
	repo: FileRepo = Depends(),
	current_user: dict = Depends(get_current_user),
):
	"""Upload multiple files"""
	user_id = current_user.get('user_id')
	uploaded_files = await repo.upload_files(files=files, user_id=user_id, conversation_id=conversation_id)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('files_uploaded_successfully'),
		data=UploadFileResponse(
			uploaded_files=[FileResponse.model_validate(file) for file in uploaded_files],
			failed_files=[],  # Handle failed files in repo if needed
		),
	)


@route.get('/', response_model=APIResponse)
@handle_exceptions
async def get_files(
	request: FileListRequest = Depends(),
	repo: FileRepo = Depends(),
	current_user: dict = Depends(get_current_user),
):
	"""Get user's files with pagination and filtering"""
	user_id = current_user.get('user_id')
	result = repo.get_user_files(user_id, request)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('files_retrieved_successfully'),
		data=PaginatedResponse(
			items=[FileResponse.model_validate(file) for file in result.items],
			paging=PagingInfo(
				total=result.total_count,
				total_pages=result.total_pages,
				page=result.page,
				page_size=result.page_size,
			),
		),
	)


@route.get('/conversation/{conversation_id}', response_model=APIResponse)
@handle_exceptions
async def get_files_by_conversation(
	conversation_id: str,
	page: int = 1,
	page_size: int = 10,
	file_type: Optional[str] = None,
	search: Optional[str] = None,
	repo: FileRepo = Depends(),
	current_user: dict = Depends(get_current_user),
):
	"""Get files for a specific conversation with pagination and filtering"""
	user_id = current_user.get('user_id')

	# Create request object with conversation_id
	request = FileListRequest(
		page=page,
		page_size=page_size,
		file_type=file_type,
		search=search,
		conversation_id=conversation_id,
	)

	result = repo.get_files_by_conversation(user_id, conversation_id, request)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('conversation_files_retrieved_successfully'),
		data=PaginatedResponse(
			items=[FileResponse.model_validate(file) for file in result.items],
			paging=PagingInfo(
				total=result.total_count,
				total_pages=result.total_pages,
				page=result.page,
				page_size=result.page_size,
			),
		),
	)


@route.get('/{file_id}', response_model=APIResponse)
@handle_exceptions
async def get_file(
	file_id: str,
	repo: FileRepo = Depends(),
	current_user: dict = Depends(get_current_user),
):
	"""Get file information"""
	user_id = current_user.get('user_id')
	file = repo.get_file_by_id(file_id, user_id)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('file_retrieved_successfully'),
		data=FileResponse.model_validate(file),
	)


@route.get('/{file_id}/url', response_model=APIResponse)
@handle_exceptions
async def get_file_download_url(
	file_id: str,
	expires: int = 3600,
	repo: FileRepo = Depends(),
	current_user: dict = Depends(get_current_user),
):
	"""Get temporary download URL for file"""
	user_id = current_user.get('user_id')
	download_url = repo.get_file_download_url(file_id, user_id, expires)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('download_url_generated'),
		data={'download_url': download_url, 'expires_in': expires},
	)


@route.get('/{file_id}/download')
@handle_exceptions
async def download_file(
	file_id: str,
	repo: FileRepo = Depends(),
	current_user: dict = Depends(get_current_user),
):
	"""Download file directly"""
	user_id = current_user.get('user_id')
	file = repo.get_file_by_id(file_id, user_id)

	# Get file content from MinIO
	from app.utils.minio.minio_handler import minio_handler

	file_content, filename = minio_handler.download_file(file.file_path)

	# Return as streaming response
	return StreamingResponse(
		io.BytesIO(file_content),
		media_type=file.type,
		headers={'Content-Disposition': f'attachment; filename={file.original_name}'},
	)


@route.delete('/{file_id}', response_model=APIResponse)
@handle_exceptions
async def delete_file(
	file_id: str,
	repo: FileRepo = Depends(),
	current_user: dict = Depends(get_current_user),
):
	"""Delete a file"""
	user_id = current_user.get('user_id')
	await repo.delete_file(file_id, user_id)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('file_deleted_successfully'),
		data={'deleted': True},
	)
