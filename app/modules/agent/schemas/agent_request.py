from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from app.core.base_model import RequestSchema, FilterableRequestSchema
from app.modules.chat.agent.models.agent import AgentType
from app.modules.chat.agent.models.agent_config import ModelProvider


class CreateAgentRequest(RequestSchema):
    """Request schema for creating new agent"""
    name: str
    description: Optional[str] = None
    agent_type: AgentType
    config_id: Optional[str] = None  # If None, use default config for type
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Agent name cannot be empty')
        return v.strip()


class UpdateAgentRequest(RequestSchema):
    """Request schema for updating agent"""
    name: Optional[str] = None
    description: Optional[str] = None
    config_id: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Agent name cannot be empty')
        return v.strip() if v else v


class SearchAgentsRequest(FilterableRequestSchema):
    """Request schema for searching agents"""
    agent_type: Optional[AgentType] = None
    is_active: Optional[bool] = None
    search_term: Optional[str] = None


class CreateAgentConfigRequest(RequestSchema):
    """Request schema for creating agent configuration"""
    name: str
    description: Optional[str] = None
    agent_type: str
    model_provider: ModelProvider
    model_name: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    system_prompt: Optional[str] = None
    tools_config: Optional[Dict[str, Any]] = None
    workflow_config: Optional[Dict[str, Any]] = None
    memory_config: Optional[Dict[str, Any]] = None
    
    @validator('temperature')
    def temperature_range(cls, v):
        if v is not None and not 0 <= v <= 2:
            raise ValueError('Temperature must be between 0 and 2')
        return v
    
    @validator('max_tokens')
    def max_tokens_range(cls, v):
        if v is not None and not 1 <= v <= 32000:
            raise ValueError('Max tokens must be between 1 and 32000')
        return v


class UpdateAgentConfigRequest(RequestSchema):
    """Request schema for updating agent configuration"""
    name: Optional[str] = None
    description: Optional[str] = None
    model_provider: Optional[ModelProvider] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    tools_config: Optional[Dict[str, Any]] = None
    workflow_config: Optional[Dict[str, Any]] = None
    memory_config: Optional[Dict[str, Any]] = None
    
    @validator('temperature')
    def temperature_range(cls, v):
        if v is not None and not 0 <= v <= 2:
            raise ValueError('Temperature must be between 0 and 2')
        return v
    
    @validator('max_tokens')
    def max_tokens_range(cls, v):
        if v is not None and not 1 <= v <= 32000:
            raise ValueError('Max tokens must be between 1 and 32000')
        return v


class AgentChatRequest(RequestSchema):
    """Request schema for agent chat execution"""
    message: str
    conversation_id: str
    api_key: Optional[str] = None
    streaming: Optional[bool] = True
    
    @validator('message')
    def message_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()


class ClearAgentMemoryRequest(RequestSchema):
    """Request schema for clearing agent memory"""
    memory_type: Optional[str] = None  # If None, clear all non-essential memory
    conversation_id: Optional[str] = None  # If provided, clear only conversation memory


class TestAgentRequest(RequestSchema):
    """Request schema for testing agent response"""
    test_message: str
    api_key: Optional[str] = None
    include_memory: Optional[bool] = False
    
    @validator('test_message')
    def test_message_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Test message cannot be empty')
        return v.strip()


class CreateDefaultAgentRequest(RequestSchema):
    """Request schema for creating default agent"""
    agent_type: AgentType
    custom_name: Optional[str] = None


class CreateCustomAgentRequest(RequestSchema):
    """Request schema for creating custom agent with inline config"""
    name: str
    description: Optional[str] = None
    agent_type: AgentType
    model_provider: ModelProvider
    model_name: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    system_prompt: Optional[str] = None
    tools_config: Optional[Dict[str, Any]] = None
    workflow_config: Optional[Dict[str, Any]] = None
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Agent name cannot be empty')
        return v.strip()
    
    @validator('temperature')
    def temperature_range(cls, v):
        if v is not None and not 0 <= v <= 2:
            raise ValueError('Temperature must be between 0 and 2')
        return v
    
    @validator('max_tokens')
    def max_tokens_range(cls, v):
        if v is not None and not 1 <= v <= 32000:
            raise ValueError('Max tokens must be between 1 and 32000')
        return v


class GetAgentMemoryRequest(RequestSchema):
    """Request schema for getting agent memory"""
    memory_type: Optional[str] = None
    conversation_id: Optional[str] = None
    limit: Optional[int] = 20
    
    @validator('limit')
    def limit_range(cls, v):
        if v is not None and not 1 <= v <= 100:
            raise ValueError('Limit must be between 1 and 100')
        return v