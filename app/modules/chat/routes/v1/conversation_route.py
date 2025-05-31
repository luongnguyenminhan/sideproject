from fastapi import APIRouter, Depends
from app.enums.base_enums import BaseErrorCode
from app.http.oauth2 import get_current_user
from app.modules.chat.repository.conversation_repo import ConversationRepo
from app.modules.chat.schemas.conversation_request import (
	CreateConversationRequest,
	UpdateConversationRequest,
	ConversationListRequest,
)
from app.modules.chat.schemas.conversation_response import ConversationResponse
from app.modules.chat.schemas.message_response import MessageResponse
from app.core.base_model import APIResponse, PaginatedResponse, PagingInfo
from app.exceptions.handlers import handle_exceptions
from app.middleware.auth_middleware import verify_token
from app.middleware.translation_manager import _

route = APIRouter(
	prefix='/conversations',
	tags=['Conversations'],
	dependencies=[Depends(verify_token)],
)


@route.get('/', response_model=APIResponse)
@handle_exceptions
async def get_conversations(
	request: ConversationListRequest = Depends(),
	repo: ConversationRepo = Depends(),
	current_user: dict = Depends(get_current_user),
):
	"""Get user's conversations with pagination and filtering"""
	user_id = current_user.get('user_id')
	result = repo.get_user_conversations(user_id, request)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('conversations_retrieved_successfully'),
		data=PaginatedResponse(
			items=[ConversationResponse.model_validate(conv) for conv in result.items],
			paging=PagingInfo(
				total=result.total_count,
				total_pages=result.total_pages,
				page=result.page,
				page_size=result.page_size,
			),
		),
	)


@route.post('/', response_model=APIResponse)
@handle_exceptions
async def create_conversation(
	request: CreateConversationRequest,
	repo: ConversationRepo = Depends(),
	current_user: dict = Depends(get_current_user),
):
	"""Create a new conversation"""
	user_id = current_user.get('user_id')
	conversation = repo.create_conversation(
		user_id=user_id,
		name=request.name,
		initial_message=request.initial_message,
		system_prompt=request.system_prompt,
	)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('conversation_created_successfully'),
		data=ConversationResponse.model_validate(conversation),
	)


@route.get('/{conversation_id}', response_model=APIResponse)
@handle_exceptions
async def get_conversation(
	conversation_id: str,
	repo: ConversationRepo = Depends(),
	current_user: dict = Depends(get_current_user),
):
	"""Get a specific conversation"""
	user_id = current_user.get('user_id')
	conversation = repo.get_conversation_by_id(conversation_id, user_id)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('conversation_retrieved_successfully'),
		data=ConversationResponse.model_validate(conversation),
	)


@route.put('/{conversation_id}', response_model=APIResponse)
@handle_exceptions
async def update_conversation(
	conversation_id: str,
	request: UpdateConversationRequest,
	repo: ConversationRepo = Depends(),
	current_user: dict = Depends(get_current_user),
):
	"""Update conversation details"""
	user_id = current_user.get('user_id')
	conversation = repo.update_conversation(
		conversation_id=conversation_id,
		user_id=user_id,
		name=request.name,
		system_prompt=request.system_prompt,
	)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('conversation_updated_successfully'),
		data=ConversationResponse.model_validate(conversation),
	)


@route.delete('/{conversation_id}', response_model=APIResponse)
@handle_exceptions
async def delete_conversation(
	conversation_id: str,
	repo: ConversationRepo = Depends(),
	current_user: dict = Depends(get_current_user),
):
	"""Delete a conversation"""
	user_id = current_user.get('user_id')
	repo.delete_conversation(conversation_id, user_id)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('conversation_deleted_successfully'),
		data={'deleted': True},
	)


@route.get('/{conversation_id}/messages', response_model=APIResponse)
@handle_exceptions
async def get_conversation_messages(
	conversation_id: str,
	page: int = 1,
	page_size: int = 50,
	before_message_id: str = None,
	repo: ConversationRepo = Depends(),
	current_user: dict = Depends(get_current_user),
):
	"""Get messages for a conversation"""
	user_id = current_user.get('user_id')

	# Verify user has access to conversation
	repo.get_conversation_by_id(conversation_id, user_id)

	# Get messages
	result = repo.get_conversation_messages(
		conversation_id=conversation_id,
		page=page,
		page_size=page_size,
		before_message_id=before_message_id,
	)
	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('messages_retrieved_successfully'),
		data=PaginatedResponse(
			items=[MessageResponse.from_message(msg) for msg in result.items],
			paging=PagingInfo(
				total=result.total_count,
				total_pages=result.total_pages,
				page=result.page,
				page_size=result.page_size,
			),
		),
	)
