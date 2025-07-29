from fastapi import APIRouter, Depends, Query
from app.enums.base_enums import BaseErrorCode
from app.http.oauth2 import get_current_user
from app.modules.chat.repository.conversation_repo import ConversationRepo
from app.modules.chat.schemas.conversation_request import (
	CreateConversationRequest,
	UpdateConversationRequest,
	ConversationListRequest,
	CountConversationsRequest,
)
from app.modules.chat.schemas.conversation_response import ConversationResponse, CountConversationsResponse
from app.modules.chat.schemas.message_response import MessageResponse
from app.core.base_model import APIResponse, PaginatedResponse, PagingInfo
from app.exceptions.handlers import handle_exceptions
from app.middleware.auth_middleware import verify_token
from app.middleware.translation_manager import _
import json

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


@route.get('/count', response_model=APIResponse)
@handle_exceptions
async def count_conversations(
	filters_json: str | None = Query(None, description='JSON string of filters'),
	include_user_filter: bool = Query(True, description='Whether to filter conversations for current user only'),
	current_user: dict = Depends(get_current_user),
	repo: ConversationRepo = Depends(),
):
	"""
	Count total number of conversations with optional filtering

	Supports filtering using a JSON string of filters with field, operator, and value.
	By default, only counts conversations for the current user.
	
	Example with structured filters:
	GET /conversations/count?filters_json=[{"field":"name","operator":"contains","value":"work"}]
	
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
	"""
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

	filter_params = {'filters': filters} if filters else {}
	
	# Get user_id if include_user_filter is True
	user_id = current_user.get('user_id') if include_user_filter else None
	
	total_count = repo.count_conversations(user_id, filter_params)
	
	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('operation_successful'),
		data=CountConversationsResponse(total_count=total_count),
	)
