from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.base_model import APIResponse
from app.enums.base_enums import BaseErrorCode
from app.http.oauth2 import get_current_user
from app.modules.agent.repository.system_agent_repo import SystemAgentRepo
from app.modules.agent.repository.conversation_workflow_repo import (
	ConversationWorkflowRepo,
)
from app.modules.agent.schemas.agent_request import *
from app.modules.agent.schemas.agent_response import *
from app.exceptions.handlers import handle_exceptions
from app.middleware.translation_manager import _

route = APIRouter(prefix='/chat', tags=['chat'])


@route.post('/', response_model=ConversationChatExecutionResponse)
@handle_exceptions
async def execute_conversation_chat(
	request: ConversationChatRequest,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Execute chat with system agent (embedded config and API key)"""
	workflow_repo = ConversationWorkflowRepo(db)

	result = await workflow_repo.execute_chat_workflow(
		conversation_id=request.conversation_id,
		user_message=request.message,
		conversation_system_prompt=request.system_prompt,
	)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('chat_executed_successfully'),
		data=ConversationChatResponse(
			content=result['content'],
			metadata=result['metadata'],
			conversation_id=request.conversation_id,
			execution_time_ms=result['metadata'].get('execution_time_ms', 0),
			tokens_used=result['metadata'].get('tokens_used'),
			model_used=result['metadata'].get('model_used', ''),
		),
	)


@route.get('/agent', response_model=GetSystemAgentResponse)
@handle_exceptions
async def get_system_agent(
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get system agent with embedded configuration"""
	agent_repo = SystemAgentRepo(db)
	agent = agent_repo.get_system_agent()

	# Create response with API key status but not actual key
	response_data = SystemAgentResponse.model_validate(agent)
	response_data.has_api_key = bool(agent.api_key)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('success'),
		data=response_data,
	)


@route.put('/agent/config', response_model=UpdateSystemAgentResponse)
@handle_exceptions
async def update_system_agent_config(
	request: UpdateSystemAgentRequest,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Update system agent configuration (admin only)"""
	agent_repo = SystemAgentRepo(db)
	print(f'Received updates: {request.model_dump(exclude_unset=True)}')

	updates = request.model_dump(exclude_unset=True)
	agent = agent_repo.update_system_agent_config(updates)

	response_data = SystemAgentResponse.model_validate(agent)
	response_data.has_api_key = bool(agent.api_key)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('system_agent_updated_successfully'),
		data=response_data,
	)


@route.put('/agent/api-key', response_model=UpdateSystemAgentApiKeyResponse)
@handle_exceptions
async def update_system_agent_api_key(
	request: UpdateSystemAgentApiKeyRequest,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Update system agent API key (admin only)"""
	agent_repo = SystemAgentRepo(db)

	agent = agent_repo.update_system_agent_api_key(api_key=request.api_key, api_provider=request.api_provider)

	response_data = SystemAgentResponse.model_validate(agent)
	response_data.has_api_key = bool(agent.api_key)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('api_key_updated_successfully'),
		data=response_data,
	)


@route.get('/models', response_model=GetModelsResponse)
@handle_exceptions
async def get_available_models():
	"""Get available AI models by provider"""
	agent_repo = SystemAgentRepo()
	models = agent_repo.get_available_models()

	model_info = [ModelInfo(provider=provider, models=model_list) for provider, model_list in models.items()]

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('success'),
		data=AvailableModelsResponse(providers=model_info),
	)


@route.post('/validate', response_model=ValidateSystemAgentResponse)
@handle_exceptions
async def validate_system_agent(
	request: ValidateSystemAgentRequest,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Validate system agent with test message"""
	import time

	workflow_repo = ConversationWorkflowRepo(db)

	try:
		start_time = time.time()

		# Use a simple test conversation ID
		test_conversation_id = f'validation_{int(time.time())}'

		# Execute simple validation without API key override
		result = await workflow_repo.execute_chat_workflow(
			conversation_id=test_conversation_id,
			user_message=request.test_message,
		)

		execution_time = int((time.time() - start_time) * 1000)

		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
			message=_('agent_validation_successful'),
			data=SystemAgentValidationResponse(
				is_valid=True,
				test_response=result['content'],
				execution_time_ms=execution_time,
			),
		)

	except Exception as e:
		execution_time = int((time.time() - start_time) * 1000)

		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
			message=_('agent_validation_completed'),
			data=SystemAgentValidationResponse(
				is_valid=False,
				error_message=str(e),
				execution_time_ms=execution_time,
			),
		)
