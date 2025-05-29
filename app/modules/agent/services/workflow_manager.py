from typing import Dict, Any, Optional, AsyncGenerator
import asyncio
import time
from app.modules.agent.models.agent import Agent, AgentType
from app.modules.agent.models.agent_config import AgentConfig
from app.modules.agent.services.langgraph_service import LangGraphService
from app.exceptions.exception import ValidationException
from app.middleware.translation_manager import _


class WorkflowManager:
    """Manager for different workflow types and execution strategies"""
    
    def __init__(self):
        self.langgraph_service = LangGraphService()
        self.workflow_types = {
            AgentType.CHAT: self._execute_chat_workflow,
            AgentType.ANALYSIS: self._execute_analysis_workflow,
            AgentType.TASK: self._execute_task_workflow,
            AgentType.CUSTOM: self._execute_custom_workflow
        }
    
    async def execute_workflow(self, agent: Agent, config: AgentConfig,
                             context: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
        """Execute workflow based on agent type"""
        
        if agent.agent_type not in self.workflow_types:
            raise ValidationException(_('unsupported_workflow_type'))
        
        workflow_executor = self.workflow_types[agent.agent_type]
        
        try:
            start_time = time.time()
            
            result = await workflow_executor(config, context, api_key)
            
            end_time = time.time()
            
            # Add execution metadata
            result['metadata']['execution_time_ms'] = int((end_time - start_time) * 1000)
            result['metadata']['agent_id'] = agent.id
            result['metadata']['agent_name'] = agent.name
            result['metadata']['workflow_type'] = agent.agent_type.value
            
            return result
            
        except Exception as e:
            raise ValidationException(f"{_('workflow_execution_failed')}: {str(e)}")
    
    async def execute_streaming_workflow(self, agent: Agent, config: AgentConfig,
                                       context: Dict[str, Any], 
                                       api_key: str = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute streaming workflow based on agent type"""
        
        if agent.agent_type not in self.workflow_types:
            yield {
                'type': 'error',
                'message': _('unsupported_workflow_type')
            }
            return
        
        try:
            start_time = time.time()
            
            # For streaming, we'll use the LangGraph service directly
            # but add agent-specific preprocessing
            
            enhanced_context = self._enhance_context_for_agent_type(
                agent.agent_type, context, config
            )
            
            async for chunk in self.langgraph_service.execute_streaming_workflow(
                config, enhanced_context, api_key
            ):
                # Add agent metadata to chunks
                if chunk.get('type') == 'metadata':
                    chunk['data']['agent_id'] = agent.id
                    chunk['data']['agent_name'] = agent.name
                    chunk['data']['workflow_type'] = agent.agent_type.value
                    chunk['data']['execution_time_ms'] = int((time.time() - start_time) * 1000)
                
                yield chunk
                
        except Exception as e:
            yield {
                'type': 'error',
                'message': f"{_('streaming_workflow_failed')}: {str(e)}"
            }
    
    async def validate_workflow_config(self, agent_type: AgentType, 
                                     config: AgentConfig) -> bool:
        """Validate workflow configuration for agent type"""
        
        try:
            # Basic validation
            if not config.system_prompt:
                return False
            
            # Agent-specific validation
            if agent_type == AgentType.CHAT:
                return self._validate_chat_config(config)
            elif agent_type == AgentType.ANALYSIS:
                return self._validate_analysis_config(config)
            elif agent_type == AgentType.TASK:
                return self._validate_task_config(config)
            else:
                return True  # Custom agents have flexible configs
                
        except Exception:
            return False
    
    def get_workflow_capabilities(self, agent_type: AgentType) -> Dict[str, Any]:
        """Get capabilities and features for workflow type"""
        
        capabilities = {
            AgentType.CHAT: {
                'streaming': True,
                'memory': True,
                'tools': ['memory_retrieval'],
                'features': ['context_awareness', 'conversation_flow'],
                'max_context_length': 10
            },
            AgentType.ANALYSIS: {
                'streaming': True,
                'memory': True,
                'tools': ['web_search', 'memory_retrieval', 'data_analysis'],
                'features': ['data_processing', 'insight_generation', 'visualization'],
                'max_context_length': 20
            },
            AgentType.TASK: {
                'streaming': True,
                'memory': True,
                'tools': ['memory_retrieval', 'task_management'],
                'features': ['task_tracking', 'scheduling', 'reminders'],
                'max_context_length': 15
            },
            AgentType.CUSTOM: {
                'streaming': True,
                'memory': True,
                'tools': ['configurable'],
                'features': ['flexible_configuration'],
                'max_context_length': 'configurable'
            }
        }
        
        return capabilities.get(agent_type, {})
    
    async def _execute_chat_workflow(self, config: AgentConfig, context: Dict[str, Any],
                                   api_key: str = None) -> Dict[str, Any]:
        """Execute chat-specific workflow"""
        
        # Enhance context for conversational AI
        enhanced_context = context.copy()
        enhanced_context['workflow_type'] = 'conversational'
        
        # Add conversational prompts
        if config.system_prompt:
            enhanced_context['system_enhancement'] = (
                "Focus on maintaining natural conversation flow and context awareness. "
                "Provide helpful, engaging responses."
            )
        
        return await self.langgraph_service.execute_workflow(config, enhanced_context, api_key)
    
    async def _execute_analysis_workflow(self, config: AgentConfig, context: Dict[str, Any],
                                       api_key: str = None) -> Dict[str, Any]:
        """Execute analysis-specific workflow"""
        
        enhanced_context = context.copy()
        enhanced_context['workflow_type'] = 'analytical'
        
        # Add analytical prompts
        if config.system_prompt:
            enhanced_context['system_enhancement'] = (
                "Focus on data analysis, pattern recognition, and insight generation. "
                "Provide structured, evidence-based responses with clear reasoning."
            )
        
        return await self.langgraph_service.execute_workflow(config, enhanced_context, api_key)
    
    async def _execute_task_workflow(self, config: AgentConfig, context: Dict[str, Any],
                                   api_key: str = None) -> Dict[str, Any]:
        """Execute task-specific workflow"""
        
        enhanced_context = context.copy()
        enhanced_context['workflow_type'] = 'task_oriented'
        
        # Add task-oriented prompts
        if config.system_prompt:
            enhanced_context['system_enhancement'] = (
                "Focus on task management, organization, and actionable guidance. "
                "Provide structured, step-by-step responses."
            )
        
        return await self.langgraph_service.execute_workflow(config, enhanced_context, api_key)
    
    async def _execute_custom_workflow(self, config: AgentConfig, context: Dict[str, Any],
                                     api_key: str = None) -> Dict[str, Any]:
        """Execute custom workflow"""
        
        enhanced_context = context.copy()
        enhanced_context['workflow_type'] = 'custom'
        
        # Use custom workflow config if available
        workflow_config = config.workflow_config or {}
        enhanced_context['custom_config'] = workflow_config
        
        return await self.langgraph_service.execute_workflow(config, enhanced_context, api_key)
    
    def _enhance_context_for_agent_type(self, agent_type: AgentType, 
                                      context: Dict[str, Any],
                                      config: AgentConfig) -> Dict[str, Any]:
        """Enhance context based on agent type"""
        
        enhanced = context.copy()
        
        if agent_type == AgentType.CHAT:
            enhanced['focus'] = 'conversation'
            enhanced['style'] = 'friendly_helpful'
        elif agent_type == AgentType.ANALYSIS:
            enhanced['focus'] = 'analysis'
            enhanced['style'] = 'analytical_structured'
        elif agent_type == AgentType.TASK:
            enhanced['focus'] = 'tasks'
            enhanced['style'] = 'action_oriented'
        else:
            enhanced['focus'] = 'custom'
            enhanced['style'] = 'flexible'
        
        # Add workflow-specific configuration
        workflow_config = config.workflow_config or {}
        enhanced['workflow_settings'] = workflow_config
        
        return enhanced
    
    def _validate_chat_config(self, config: AgentConfig) -> bool:
        """Validate chat workflow configuration"""
        return (
            config.temperature >= 0.5 and  # More creative for conversation
            config.max_tokens >= 512 and   # Sufficient for responses
            'conversational' in config.system_prompt.lower() if config.system_prompt else True
        )
    
    def _validate_analysis_config(self, config: AgentConfig) -> bool:
        """Validate analysis workflow configuration"""
        return (
            config.temperature <= 0.5 and  # More precise for analysis
            config.max_tokens >= 1024 and  # More space for detailed analysis
            'analys' in config.system_prompt.lower() if config.system_prompt else True
        )
    
    def _validate_task_config(self, config: AgentConfig) -> bool:
        """Validate task workflow configuration"""
        return (
            config.temperature <= 0.7 and  # Balanced for task guidance
            config.max_tokens >= 512 and   # Sufficient for task instructions
            'task' in config.system_prompt.lower() if config.system_prompt else True
        )