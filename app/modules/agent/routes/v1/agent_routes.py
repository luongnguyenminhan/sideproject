from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.base_model import APIResponse, PaginatedResponse, PagingInfo
from app.modules.agent.repository.agent_repo import AgentRepo
from app.modules.agent.repository.agent_workflow_repo import AgentWorkflowRepo
from app.modules.agent.services.agent_factory import AgentFactory
from app.modules.agent.services.workflow_manager import WorkflowManager
from app.modules.agent.schemas.agent_request import *
from app.modules.agent.schemas.agent_response import *
from app.modules.agent.models.agent import AgentType
from app.modules.agent.models.agent_memory import MemoryType
from app.exceptions.handlers import handle_exceptions
from app.middleware.translation_manager import _
from typing import List
import asyncio

route = APIRouter(prefix="/agents", tags=["agents"])


@route.post("/", response_model=CreateAgentResponse)
@handle_exceptions
async def create_agent(
    request: CreateAgentRequest,
    db: Session = Depends(get_db),
    user_id: str = "default_user"  # TODO: Get from auth
):
    """Create new agent"""
    agent_repo = AgentRepo(db)
    
    # Use default config if none provided
    config_id = request.config_id
    if not config_id:
        default_config = agent_repo.config_dal.get_default_config_for_type(request.agent_type.value)
        if not default_config:
            # Create default config using factory
            agent = AgentFactory.create_default_agent(request.agent_type, user_id, agent_repo, request.name)
        else:
            agent = agent_repo.create_agent(
                user_id=user_id,
                name=request.name,
                agent_type=request.agent_type,
                config_id=default_config.id,
                description=request.description
            )
    else:
        agent = agent_repo.create_agent(
            user_id=user_id,
            name=request.name,
            agent_type=request.agent_type,
            config_id=config_id,
            description=request.description
        )
    
    return APIResponse(
        error_code=0,
        message=_('agent_created_successfully'),
        data=AgentResponse.model_validate(agent)
    )


@route.get("/", response_model=ListAgentsResponse)
@handle_exceptions
async def list_agents(
    request: SearchAgentsRequest = Depends(),
    db: Session = Depends(get_db),
    user_id: str = "default_user"  # TODO: Get from auth
):
    """List user's agents"""
    agent_repo = AgentRepo(db)
    
    agents = agent_repo.get_user_agents(user_id, request.is_active)
    
    # Apply filters
    if request.agent_type:
        agents = [a for a in agents if a.agent_type == request.agent_type]
    
    if request.search_term:
        search_lower = request.search_term.lower()
        agents = [a for a in agents if 
                 search_lower in a.name.lower() or 
                 (a.description and search_lower in a.description.lower())]
    
    # Apply pagination
    total = len(agents)
    start = (request.page - 1) * request.page_size
    end = start + request.page_size
    paginated_agents = agents[start:end]
    
    agent_responses = [AgentResponse.model_validate(agent) for agent in paginated_agents]
    
    return APIResponse(
        error_code=0,
        message=_('success'),
        data=PaginatedResponse(
            items=agent_responses,
            paging=PagingInfo(
                total=total,
                total_pages=(total + request.page_size - 1) // request.page_size,
                page=request.page,
                page_size=request.page_size
            )
        )
    )


@route.get("/{agent_id}", response_model=GetAgentResponse)
@handle_exceptions
async def get_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    user_id: str = "default_user"  # TODO: Get from auth
):
    """Get agent by ID"""
    agent_repo = AgentRepo(db)
    
    agent, config = agent_repo.get_agent_with_config(agent_id, user_id)
    
    agent_response = AgentResponse.model_validate(agent)
    agent_response.config = AgentConfigResponse.model_validate(config)
    
    return APIResponse(
        error_code=0,
        message=_('success'),
        data=agent_response
    )


@route.put("/{agent_id}", response_model=UpdateAgentResponse)
@handle_exceptions
async def update_agent(
    agent_id: str,
    request: UpdateAgentRequest,
    db: Session = Depends(get_db),
    user_id: str = "default_user"  # TODO: Get from auth
):
    """Update agent"""
    agent_repo = AgentRepo(db)
    
    updates = request.model_dump(exclude_unset=True)
    agent = agent_repo.update_agent(agent_id, user_id, updates)
    
    return APIResponse(
        error_code=0,
        message=_('agent_updated_successfully'),
        data=AgentResponse.model_validate(agent)
    )


@route.delete("/{agent_id}", response_model=DeleteAgentResponse)
@handle_exceptions
async def delete_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    user_id: str = "default_user"  # TODO: Get from auth
):
    """Delete agent"""
    agent_repo = AgentRepo(db)
    
    success = agent_repo.delete_agent(agent_id, user_id)
    
    return APIResponse(
        error_code=0,
        message=_('agent_deleted_successfully'),
        data={"deleted": success}
    )


@route.post("/{agent_id}/toggle", response_model=UpdateAgentResponse)
@handle_exceptions
async def toggle_agent_status(
    agent_id: str,
    db: Session = Depends(get_db),
    user_id: str = "default_user"  # TODO: Get from auth
):
    """Toggle agent active status"""
    agent_repo = AgentRepo(db)
    
    agent = agent_repo.toggle_agent_status(agent_id, user_id)
    
    return APIResponse(
        error_code=0,
        message=_('agent_status_updated'),
        data=AgentResponse.model_validate(agent)
    )


@route.post("/{agent_id}/chat", response_model=ChatExecutionResponse)
@handle_exceptions
async def execute_chat(
    agent_id: str,
    request: AgentChatRequest,
    db: Session = Depends(get_db),
    user_id: str = "default_user"  # TODO: Get from auth
):
    """Execute chat with agent"""
    workflow_repo = AgentWorkflowRepo(db)
    
    if request.streaming:
        # For streaming, we should use WebSocket
        raise HTTPException(
            status_code=400,
            detail=_('use_websocket_for_streaming')
        )
    
    result = await workflow_repo.execute_chat_workflow(
        agent_id=agent_id,
        user_id=user_id,
        conversation_id=request.conversation_id,
        user_message=request.message,
        api_key=request.api_key
    )
    
    return APIResponse(
        error_code=0,
        message=_('chat_executed_successfully'),
        data=AgentChatResponse(
            content=result['content'],
            metadata=result['metadata'],
            conversation_id=request.conversation_id,
            agent_id=agent_id,
            execution_time_ms=result['metadata'].get('execution_time_ms', 0),
            tokens_used=result['metadata'].get('tokens_used'),
            model_used=result['metadata'].get('model_used', '')
        )
    )


@route.get("/{agent_id}/memory", response_model=GetMemoryResponse)
@handle_exceptions
async def get_agent_memory(
    agent_id: str,
    request: GetAgentMemoryRequest = Depends(),
    db: Session = Depends(get_db),
    user_id: str = "default_user"  # TODO: Get from auth
):
    """Get agent memory"""
    workflow_repo = AgentWorkflowRepo(db)
    
    # Verify user owns agent
    agent_repo = AgentRepo(db)
    agent_repo.get_agent_by_id(agent_id, user_id)
    
    context = workflow_repo.get_agent_memory_context(
        agent_id=agent_id,
        conversation_id=request.conversation_id,
        limit=request.limit or 20
    )
    
    return APIResponse(
        error_code=0,
        message=_('success'),
        data=AgentMemoryContext(
            conversation_memories=context['conversation_memories'],
            important_memories=context['important_memories'],
            workflow_state=context['workflow_state'],
            memory_count=len(context['conversation_memories']) + len(context['important_memories'])
        )
    )


@route.post("/{agent_id}/memory/clear", response_model=ClearMemoryResponse)
@handle_exceptions
async def clear_agent_memory(
    agent_id: str,
    request: ClearAgentMemoryRequest,
    db: Session = Depends(get_db),
    user_id: str = "default_user"  # TODO: Get from auth
):
    """Clear agent memory"""
    workflow_repo = AgentWorkflowRepo(db)
    
    memory_type = None
    if request.memory_type:
        try:
            memory_type = MemoryType(request.memory_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=_('invalid_memory_type'))
    
    if request.conversation_id and memory_type is None:
        # Clear conversation-specific memory
        cleared = workflow_repo.memory_dal.clear_conversation_memories(agent_id, request.conversation_id)
    else:
        # Clear by type or all
        cleared = workflow_repo.clear_agent_memory(agent_id, user_id, memory_type)
    
    return APIResponse(
        error_code=0,
        message=_('memory_cleared_successfully'),
        data={"cleared_count": cleared}
    )


@route.post("/{agent_id}/test", response_model=TestAgentResponseWrapper)
@handle_exceptions
async def test_agent(
    agent_id: str,
    request: TestAgentRequest,
    db: Session = Depends(get_db),
    user_id: str = "default_user"  # TODO: Get from auth
):
    """Test agent with a message"""
    agent_repo = AgentRepo(db)
    workflow_manager = WorkflowManager()
    
    # Get agent and config
    agent, config = agent_repo.get_agent_with_config(agent_id, user_id)
    
    # Prepare test context
    context = {
        'agent': {
            'id': agent.id,
            'name': agent.name,
            'type': agent.agent_type.value
        },
        'config': {
            'model_provider': config.model_provider.value,
            'model_name': config.model_name,
            'temperature': config.temperature,
            'max_tokens': config.max_tokens,
            'system_prompt': config.system_prompt,
            'tools_config': config.tools_config or {},
            'workflow_config': config.workflow_config or {}
        },
        'user_message': request.test_message,
        'conversation_history': [],
        'important_context': [],
        'is_test': True
    }
    
    try:
        result = await workflow_manager.execute_workflow(
            agent=agent,
            config=config,
            context=context,
            api_key=request.api_key
        )
        
        return APIResponse(
            error_code=0,
            message=_('test_executed_successfully'),
            data=AgentTestResponse(
                test_message=request.test_message,
                response=result['content'],
                metadata=result['metadata'],
                execution_time_ms=result['metadata'].get('execution_time_ms', 0),
                success=True
            )
        )
        
    except Exception as e:
        return APIResponse(
            error_code=0,
            message=_('test_completed_with_error'),
            data=AgentTestResponse(
                test_message=request.test_message,
                response="",
                metadata={},
                execution_time_ms=0,
                success=False,
                error=str(e)
            )
        )


@route.get("/{agent_id}/capabilities", response_model=GetCapabilitiesResponse)
@handle_exceptions
async def get_agent_capabilities(
    agent_id: str,
    db: Session = Depends(get_db),
    user_id: str = "default_user"  # TODO: Get from auth
):
    """Get agent capabilities"""
    agent_repo = AgentRepo(db)
    workflow_manager = WorkflowManager()
    
    agent = agent_repo.get_agent_by_id(agent_id, user_id)
    capabilities = workflow_manager.get_workflow_capabilities(agent.agent_type)
    
    return APIResponse(
        error_code=0,
        message=_('success'),
        data=AgentCapabilities(**capabilities)
    )


@route.post("/create-default", response_model=CreateAgentResponse)
@handle_exceptions
async def create_default_agent(
    request: CreateDefaultAgentRequest,
    db: Session = Depends(get_db),
    user_id: str = "default_user"  # TODO: Get from auth
):
    """Create default agent for type"""
    agent_repo = AgentRepo(db)
    
    agent = AgentFactory.create_default_agent(
        agent_type=request.agent_type,
        user_id=user_id,
        agent_repo=agent_repo,
        custom_name=request.custom_name
    )
    
    return APIResponse(
        error_code=0,
        message=_('default_agent_created_successfully'),
        data=AgentResponse.model_validate(agent)
    )


@route.post("/create-custom", response_model=CreateAgentResponse)
@handle_exceptions
async def create_custom_agent(
    request: CreateCustomAgentRequest,
    db: Session = Depends(get_db),
    user_id: str = "default_user"  # TODO: Get from auth
):
    """Create custom agent with inline configuration"""
    agent_repo = AgentRepo(db)
    
    custom_config = {
        'name': f"custom_config_for_{request.name}",
        'description': request.description or f"Custom configuration for {request.name}",
        'model_provider': request.model_provider.value,
        'model_name': request.model_name,
        'temperature': request.temperature,
        'max_tokens': request.max_tokens,
        'system_prompt': request.system_prompt,
        'tools_config': request.tools_config,
        'workflow_config': request.workflow_config
    }
    
    agent = AgentFactory.create_custom_agent(
        agent_type=request.agent_type,
        user_id=user_id,
        agent_repo=agent_repo,
        custom_config=custom_config,
        agent_name=request.name
    )
    
    return APIResponse(
        error_code=0,
        message=_('custom_agent_created_successfully'),
        data=AgentResponse.model_validate(agent)
    )


@route.get("/models/available", response_model=GetModelsResponse)
@handle_exceptions
async def get_available_models():
    """Get available models by provider"""
    models = AgentFactory.list_available_models()
    
    model_info = [
        ModelInfo(provider=provider, models=model_list)
        for provider, model_list in models.items()
    ]
    
    return APIResponse(
        error_code=0,
        message=_('success'),
        data=AvailableModelsResponse(providers=model_info)
    )


@route.get("/templates/{agent_type}", response_model=GetDefaultTemplateResponse)
@handle_exceptions
async def get_default_template(agent_type: AgentType):
    """Get default configuration template for agent type"""
    
    template = AgentFactory.get_default_config_template(agent_type)
    
    use_cases = {
        AgentType.CHAT: ["General conversation", "Customer support", "Q&A assistance"],
        AgentType.ANALYSIS: ["Data analysis", "Report generation", "Pattern recognition"],
        AgentType.TASK: ["Task management", "Scheduling", "Productivity assistance"],
        AgentType.CUSTOM: ["Specialized workflows", "Custom business logic"]
    }
    
    return APIResponse(
        error_code=0,
        message=_('success'),
        data=DefaultConfigTemplate(
            agent_type=agent_type,
            template=template,
            description=template.get('description', ''),
            recommended_use_cases=use_cases.get(agent_type, [])
        )
    )