from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.enums.base_enums import BaseErrorCode
from app.http.oauth2 import get_current_user
from app.modules.chat.repository.api_key_repo import ApiKeyRepo
from app.modules.chat.schemas.api_key_request import SaveApiKeyRequest
from app.modules.chat.schemas.api_key_response import ApiKeyResponse
from app.core.base_model import APIResponse
from app.exceptions.handlers import handle_exceptions
from app.middleware.auth_middleware import verify_token
from app.middleware.translation_manager import _

route = APIRouter(prefix='/api-keys', tags=['API Keys'], dependencies=[Depends(verify_token)])


@route.post('/', response_model=APIResponse)
@handle_exceptions
async def save_api_key(
	request: SaveApiKeyRequest,
	repo: ApiKeyRepo = Depends(),
	current_user: dict = Depends(get_current_user),
):
	"""Save user's API key for AI services"""
	user_id = current_user.get('user_id')
	api_key = repo.save_api_key(
		user_id=user_id,
		provider=request.provider,
		api_key=request.api_key,
		is_default=request.is_default,
		key_name=request.key_name,
	)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('api_key_saved_successfully'),
		data=ApiKeyResponse.model_validate(api_key),
	)


@route.get('/', response_model=APIResponse)
@handle_exceptions
async def get_api_keys(repo: ApiKeyRepo = Depends(), current_user: dict = Depends(get_current_user)):
	"""Get user's API keys"""
	user_id = current_user.get('user_id')
	api_keys = repo.get_user_api_keys(user_id)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('api_keys_retrieved_successfully'),
		data=[ApiKeyResponse.model_validate(key) for key in api_keys],
	)


@route.delete('/{key_id}', response_model=APIResponse)
@handle_exceptions
async def delete_api_key(
	key_id: str,
	repo: ApiKeyRepo = Depends(),
	current_user: dict = Depends(get_current_user),
):
	"""Delete an API key"""
	user_id = current_user.get('user_id')
	repo.delete_api_key(key_id, user_id)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('api_key_deleted_successfully'),
		data={'deleted': True},
	)


@route.put('/{key_id}/set-default', response_model=APIResponse)
@handle_exceptions
async def set_default_api_key(
	key_id: str,
	repo: ApiKeyRepo = Depends(),
	current_user: dict = Depends(get_current_user),
):
	"""Set an API key as default for its provider"""
	user_id = current_user.get('user_id')
	api_key = repo.set_default_api_key(key_id, user_id)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('api_key_set_as_default'),
		data=ApiKeyResponse.model_validate(api_key),
	)
