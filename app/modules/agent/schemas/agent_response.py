from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.core.base_model import ResponseSchema, APIResponse
from app.modules.agent.models.agent import AgentType
from app.modules.agent.models.agent_config import ModelProvider
from app.modules.agent.models.agent_memory import MemoryType


class AgentConfigResponse(ResponseSchema):
    """Response schema for agent configuration"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    description: Optional[str]
    agent_type: str
    model_provider: ModelProvider
    model_name: str
    temperature: float
    max_tokens: Optional[int]
    system_prompt: Optional[str]
    tools_config: Optional[Dict[str, Any]]
    workflow_config: Optional[Dict[str, Any]]
    memory_config: Optional[Dict[str, Any]]
    create_date: str
    update_date: str


class AgentResponse(ResponseSchema):
    """Response schema for agent"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    description: Optional[str]
    agent_type: AgentType
    config_id: str
    user_id: str
    is_active: bool
    created_by: str
    create_date: str
    update_date: str
    
    # Related data
    config: Optional[AgentConfigResponse] = None


class AgentMemoryResponse(ResponseSchema):
    """Response schema for agent memory"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    agent_id: str
    conversation_id: Optional[str]
    memory_type: MemoryType
    content: Dict[str, Any]
    importance_score: float
    session_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    create_date: str


class AgentChatResponse(BaseModel):
    """Response schema for agent chat execution"""
    content: str
    metadata: Dict[str, Any]
    conversation_id: str
    agent_id: str
    execution_time_ms: int
    tokens_used: Optional[int] = None
    model_used: str


class AgentStreamChunk(BaseModel):
    """Response schema for streaming chat chunks"""
    type: str  # 'content', 'metadata', 'error'
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    total_content: Optional[str] = None


class AgentMemoryContext(BaseModel):
    """Response schema for agent memory context"""
    conversation_memories: List[Dict[str, Any]]
    important_memories: List[Dict[str, Any]]
    workflow_state: Dict[str, Any]
    memory_count: int


class AgentCapabilities(BaseModel):
    """Response schema for agent capabilities"""
    streaming: bool
    memory: bool
    tools: List[str]
    features: List[str]
    max_context_length: Any  # int or str for 'configurable'


class ModelInfo(BaseModel):
    """Response schema for model information"""
    provider: str
    models: List[str]


class AvailableModelsResponse(BaseModel):
    """Response schema for available models"""
    providers: List[ModelInfo]


class AgentTestResponse(BaseModel):
    """Response schema for agent testing"""
    test_message: str
    response: str
    metadata: Dict[str, Any]
    execution_time_ms: int
    success: bool
    error: Optional[str] = None


class WorkflowValidationResponse(BaseModel):
    """Response schema for workflow validation"""
    is_valid: bool
    issues: List[str]
    suggestions: List[str]


class AgentStatsResponse(BaseModel):
    """Response schema for agent statistics"""
    total_conversations: int
    total_messages: int
    average_response_time_ms: float
    memory_usage: Dict[str, int]
    last_interaction: Optional[str]
    uptime_days: int


class DefaultConfigTemplate(BaseModel):
    """Response schema for default configuration template"""
    agent_type: AgentType
    template: Dict[str, Any]
    description: str
    recommended_use_cases: List[str]


# Compound responses using APIResponse
class CreateAgentResponse(APIResponse):
    """Response for agent creation"""
    pass


class UpdateAgentResponse(APIResponse):
    """Response for agent update"""
    pass


class GetAgentResponse(APIResponse):
    """Response for getting single agent"""
    pass


class ListAgentsResponse(APIResponse):
    """Response for listing agents"""
    pass


class DeleteAgentResponse(APIResponse):
    """Response for agent deletion"""
    pass


class CreateConfigResponse(APIResponse):
    """Response for config creation"""
    pass


class UpdateConfigResponse(APIResponse):
    """Response for config update"""
    pass


class GetConfigResponse(APIResponse):
    """Response for getting single config"""
    pass


class ListConfigsResponse(APIResponse):
    """Response for listing configs"""
    pass


class ChatExecutionResponse(APIResponse):
    """Response for chat execution"""
    pass


class ClearMemoryResponse(APIResponse):
    """Response for memory clearing"""
    pass


class GetMemoryResponse(APIResponse):
    """Response for getting memory"""
    pass


class TestAgentResponseWrapper(APIResponse):
    """Response wrapper for agent testing"""
    pass


class GetCapabilitiesResponse(APIResponse):
    """Response for getting agent capabilities"""
    pass


class GetModelsResponse(APIResponse):
    """Response for getting available models"""
    pass


class ValidateWorkflowResponse(APIResponse):
    """Response for workflow validation"""
    pass


class GetAgentStatsResponse(APIResponse):
    """Response for agent statistics"""
    pass


class GetDefaultTemplateResponse(APIResponse):
    """Response for default configuration template"""
    pass