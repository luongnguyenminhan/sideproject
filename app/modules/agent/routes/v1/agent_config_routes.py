from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.base_model import APIResponse, PaginatedResponse, PagingInfo
from app.enums.base_enums import BaseErrorCode
from app.http.oauth2 import get_current_user
from app.modules.agent.repository.agent_config_repo import AgentConfigRepo
from app.modules.agent.schemas.agent_request import (
	CreateAgentConfigRequest,
	UpdateAgentConfigRequest,
	SearchAgentsRequest,
)
from app.modules.agent.schemas.agent_response import (
	CreateConfigResponse,
	UpdateConfigResponse,
	GetConfigResponse,
	ListConfigsResponse,
	AgentConfigResponse,
)
from app.exceptions.handlers import handle_exceptions
from app.middleware.translation_manager import _
from typing import List, Optional

route = APIRouter(prefix='/agents/configs', tags=['agent-configs'])


@route.post('/', response_model=CreateConfigResponse)
@handle_exceptions
async def create_agent_config(
	request: CreateAgentConfigRequest,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Create new agent configuration"""
	config_repo = AgentConfigRepo(db)

	# Create config data
	config_data = {
		'name': request.name,
		'description': request.description,
		'agent_type': request.agent_type,
		'model_provider': request.model_provider,
		'model_name': request.model_name,
		'temperature': request.temperature,
		'max_tokens': request.max_tokens,
		'system_prompt': request.system_prompt,
		'tools_config': request.tools_config,
		'workflow_config': request.workflow_config,
		'memory_config': request.memory_config,
	}

	# Create the configuration
	config = config_repo.create_config(config_data)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('agent_config_created_successfully'),
		data=AgentConfigResponse.model_validate(config),
	)


@route.get('/', response_model=ListConfigsResponse)
@handle_exceptions
async def list_agent_configs(
	page: int = 1,
	page_size: int = 10,
	agent_type: Optional[str] = None,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""List agent configurations with pagination and filtering"""
	config_repo = AgentConfigRepo(db)

	# Get configurations with optional type filter and pagination
	if agent_type:
		configs = config_repo.get_configs_by_type(agent_type, page=page, page_size=page_size)
	else:
		configs = config_repo.get_all_configs(page=page, page_size=page_size)

	# Convert to response models
	config_responses = [AgentConfigResponse.model_validate(config) for config in configs]

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('agent_configs_retrieved_successfully'),
		data=PaginatedResponse(
			items=config_responses,
			paging=PagingInfo(
				page=page,
				page_size=page_size,
				total=len(config_responses),
				total_pages=(len(config_responses) + page_size - 1) // page_size,
			),
		),
	)


@route.get('/{config_id}', response_model=GetConfigResponse)
@handle_exceptions
async def get_agent_config(
	config_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get agent configuration by ID"""
	config_repo = AgentConfigRepo(db)

	# Get configuration
	config = config_repo.get_config_by_id(config_id)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('agent_config_retrieved_successfully'),
		data=AgentConfigResponse.model_validate(config),
	)


@route.put('/{config_id}', response_model=UpdateConfigResponse)
@handle_exceptions
async def update_agent_config(
	config_id: str,
	request: UpdateAgentConfigRequest,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Update agent configuration"""
	config_repo = AgentConfigRepo(db)

	# Prepare update data (only include non-None values)
	update_data = {}
	if request.name is not None:
		update_data['name'] = request.name
	if request.description is not None:
		update_data['description'] = request.description
	if request.model_provider is not None:
		update_data['model_provider'] = request.model_provider
	if request.model_name is not None:
		update_data['model_name'] = request.model_name
	if request.temperature is not None:
		update_data['temperature'] = request.temperature
	if request.max_tokens is not None:
		update_data['max_tokens'] = request.max_tokens
	if request.system_prompt is not None:
		update_data['system_prompt'] = request.system_prompt
	if request.tools_config is not None:
		update_data['tools_config'] = request.tools_config
	if request.workflow_config is not None:
		update_data['workflow_config'] = request.workflow_config
	if request.memory_config is not None:
		update_data['memory_config'] = request.memory_config

	# Update the configuration
	updated_config = config_repo.update_config(config_id, update_data)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('agent_config_updated_successfully'),
		data=AgentConfigResponse.model_validate(updated_config),
	)


@route.delete('/{config_id}', response_model=APIResponse)
@handle_exceptions
async def delete_agent_config(
	config_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Delete agent configuration"""
	config_repo = AgentConfigRepo(db)

	# Delete the configuration (includes validation checks)
	config_repo.delete_config(config_id)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('agent_config_deleted_successfully'),
		data=None,
	)


@route.post('/search', response_model=ListConfigsResponse)
@handle_exceptions
async def search_agent_configs(
	request: SearchAgentsRequest,
	page: int = 1,
	page_size: int = 10,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Search agent configurations by name, description, type, and provider"""
	config_repo = AgentConfigRepo(db)

	# Search configurations with multiple filters
	configs = config_repo.search_configs(
		search_term=request.query if hasattr(request, 'query') else None,
		agent_type=request.agent_type if hasattr(request, 'agent_type') else None,
		provider='google',
		limit=page_size * page,  # Apply limit based on pagination
	)

	# Apply pagination to results
	start_idx = (page - 1) * page_size
	paginated_configs = configs[start_idx : start_idx + page_size]
	total = len(configs)

	# Convert to response models
	config_responses = [AgentConfigResponse.model_validate(config) for config in paginated_configs]

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('agent_configs_searched_successfully'),
		data=PaginatedResponse(
			items=config_responses,
			paging=PagingInfo(
				page=page,
				page_size=page_size,
				total=total,
				total_pages=(total + page_size - 1) // page_size,
			),
		),
	)


@route.get('/provider/{provider}', response_model=ListConfigsResponse)
@handle_exceptions
async def get_configs_by_provider(
	provider: str,
	page: int = 1,
	page_size: int = 10,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get agent configurations by model provider"""
	config_repo = AgentConfigRepo(db)

	# Get configurations by provider
	configs, total = config_repo.get_configs_by_provider(provider=provider, page=page, page_size=page_size)

	# Convert to response models
	config_responses = [AgentConfigResponse.model_validate(config) for config in configs]

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('agent_configs_by_provider_retrieved_successfully'),
		data=PaginatedResponse(
			items=config_responses,
			paging=PagingInfo(
				page=page,
				page_size=page_size,
				total=total,
				total_pages=(total + page_size - 1) // page_size,
			),
		),
	)


@route.get('/{config_id}/stats', response_model=APIResponse)
@handle_exceptions
async def get_config_usage_stats(
	config_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get usage statistics for an agent configuration"""
	config_repo = AgentConfigRepo(db)

	# Get usage statistics
	stats = config_repo.get_config_usage_stats(config_id)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('config_usage_stats_retrieved_successfully'),
		data=stats,
	)


@route.post('/{config_id}/duplicate', response_model=CreateConfigResponse)
@handle_exceptions
async def duplicate_agent_config(
	config_id: str,
	new_name: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Duplicate an existing agent configuration with a new name"""
	config_repo = AgentConfigRepo(db)

	# Duplicate the configuration
	duplicated_config = config_repo.duplicate_config(config_id, new_name)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('agent_config_duplicated_successfully'),
		data=AgentConfigResponse.model_validate(duplicated_config),
	)
