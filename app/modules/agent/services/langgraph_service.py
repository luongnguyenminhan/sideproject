from typing import Dict, Any, AsyncGenerator, Optional
import asyncio
import json
from app.modules.chat.agent.models.agent_config import AgentConfig, ModelProvider
from app.exceptions.exception import ValidationException
from app.middleware.translation_manager import _


class LangGraphService:
    """Service for LangGraph workflow execution and AI model integration"""
    
    def __init__(self):
        self.supported_providers = {
            ModelProvider.OPENAI: self._get_openai_model,
            ModelProvider.ANTHROPIC: self._get_anthropic_model,
            ModelProvider.GOOGLE: self._get_google_model,
            ModelProvider.GROQ: self._get_groq_model,
            ModelProvider.OLLAMA: self._get_ollama_model
        }
    
    async def execute_workflow(self, agent_config: AgentConfig, context: Dict[str, Any],
                             api_key: str = None) -> Dict[str, Any]:
        """Execute non-streaming workflow"""
        try:
            # Get LLM model
            llm = self._get_model(agent_config, api_key)
            
            # Create workflow based on agent type
            workflow = self._create_workflow(agent_config, llm)
            
            # Prepare input for workflow
            workflow_input = self._prepare_workflow_input(context)
            
            # Execute workflow
            result = await self._execute_langgraph_workflow(workflow, workflow_input)
            
            return {
                'content': result.get('content', ''),
                'metadata': {
                    'model_used': f"{agent_config.model_provider.value}:{agent_config.model_name}",
                    'tokens_used': result.get('tokens_used'),
                    'response_time_ms': result.get('response_time_ms'),
                    'workflow_type': agent_config.agent_type
                }
            }
            
        except Exception as e:
            raise ValidationException(f"{_('workflow_execution_error')}: {str(e)}")
    
    async def execute_streaming_workflow(self, agent_config: AgentConfig, 
                                       context: Dict[str, Any],
                                       api_key: str = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute streaming workflow"""
        try:
            # Get LLM model
            llm = self._get_model(agent_config, api_key)
            
            # Create streaming workflow
            workflow = self._create_streaming_workflow(agent_config, llm)
            
            # Prepare input
            workflow_input = self._prepare_workflow_input(context)
            
            # Execute streaming workflow
            async for chunk in self._execute_streaming_langgraph_workflow(workflow, workflow_input):
                yield chunk
                
        except Exception as e:
            yield {
                'type': 'error',
                'message': f"{_('workflow_execution_error')}: {str(e)}"
            }
    
    def _get_model(self, config: AgentConfig, api_key: str = None):
        """Get LLM model based on configuration"""
        if config.model_provider not in self.supported_providers:
            raise ValidationException(_('unsupported_model_provider'))
        
        model_getter = self.supported_providers[config.model_provider]
        return model_getter(config, api_key)
    
    def _get_openai_model(self, config: AgentConfig, api_key: str = None):
        """Get OpenAI model"""
        try:
            from langchain_openai import ChatOpenAI
            
            return ChatOpenAI(
                model=config.model_name,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=api_key,
                streaming=True
            )
        except ImportError:
            raise ValidationException(_('openai_not_installed'))
    
    def _get_anthropic_model(self, config: AgentConfig, api_key: str = None):
        """Get Anthropic model"""
        try:
            from langchain_anthropic import ChatAnthropic
            
            return ChatAnthropic(
                model=config.model_name,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=api_key,
                streaming=True
            )
        except ImportError:
            raise ValidationException(_('anthropic_not_installed'))
    
    def _get_google_model(self, config: AgentConfig, api_key: str = None):
        """Get Google model"""
        try:
            from langchain_google_vertexai import ChatVertexAI
            
            return ChatVertexAI(
                model=config.model_name,
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
                streaming=True
            )
        except ImportError:
            raise ValidationException(_('google_not_installed'))
    
    def _get_groq_model(self, config: AgentConfig, api_key: str = None):
        """Get Groq model"""
        try:
            from langchain_groq import ChatGroq
            
            return ChatGroq(
                model=config.model_name,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                api_key=api_key,
                streaming=True
            )
        except ImportError:
            raise ValidationException(_('groq_not_installed'))
    
    def _get_ollama_model(self, config: AgentConfig, api_key: str = None):
        """Get Ollama model"""
        try:
            from langchain_ollama import ChatOllama
            
            return ChatOllama(
                model=config.model_name,
                temperature=config.temperature,
                num_predict=config.max_tokens
            )
        except ImportError:
            raise ValidationException(_('ollama_not_installed'))
    
    def _create_workflow(self, config: AgentConfig, llm):
        """Create LangGraph workflow based on agent type"""
        try:
            from langgraph.prebuilt import create_react_agent
            from langgraph.checkpoint.memory import MemorySaver
            
            # Get tools based on configuration
            tools = self._get_tools(config.tools_config or {})
            
            # Create memory for workflow
            memory = MemorySaver()
            
            # Create agent
            workflow = create_react_agent(
                llm, 
                tools, 
                checkpointer=memory,
                state_modifier=config.system_prompt
            )
            
            return workflow
            
        except ImportError:
            raise ValidationException(_('langgraph_not_installed'))
    
    def _create_streaming_workflow(self, config: AgentConfig, llm):
        """Create streaming LangGraph workflow"""
        return self._create_workflow(config, llm)  # Same as regular for now
    
    def _get_tools(self, tools_config: Dict[str, Any]) -> list:
        """Get tools based on configuration"""
        tools = []
        
        # Add web search tool if enabled
        if tools_config.get('web_search', False):
            try:
                from langchain_community.tools.tavily_search import TavilySearchResults
                tools.append(TavilySearchResults(max_results=2))
            except ImportError:
                pass  # Skip if not available
        
        # Add memory retrieval tool if enabled
        if tools_config.get('memory_retrieval', False):
            tools.append(self._create_memory_tool())
        
        # Add custom tools from config
        custom_tools = tools_config.get('custom_tools', [])
        for tool_config in custom_tools:
            tool = self._create_custom_tool(tool_config)
            if tool:
                tools.append(tool)
        
        return tools
    
    def _create_memory_tool(self):
        """Create memory retrieval tool"""
        from langchain.tools import tool
        
        @tool
        def memory_search(query: str) -> str:
            """Search agent memory for relevant information"""
            # This would integrate with memory DAL
            return f"Memory search for: {query} (placeholder)"
        
        return memory_search
    
    def _create_custom_tool(self, tool_config: Dict[str, Any]):
        """Create custom tool from configuration"""
        # Implementation for custom tools
        return None
    
    def _prepare_workflow_input(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare input for LangGraph workflow"""
        from langchain_core.messages import HumanMessage, SystemMessage
        
        messages = []
        
        # Add system message if available
        if context['config'].get('system_prompt'):
            messages.append(SystemMessage(content=context['config']['system_prompt']))
        
        # Add conversation history
        for memory in context.get('conversation_history', []):
            if memory.get('role') == 'user':
                messages.append(HumanMessage(content=memory['content']))
            # AI messages would be added as AIMessage, but we'll keep it simple for now
        
        # Add current user message
        messages.append(HumanMessage(content=context['user_message']))
        
        return {
            "messages": messages,
            "context": context
        }
    
    async def _execute_langgraph_workflow(self, workflow, workflow_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LangGraph workflow (non-streaming)"""
        try:
            import time
            start_time = time.time()
            
            # Create thread config
            config = {"configurable": {"thread_id": workflow_input.get('context', {}).get('timestamp', 'default')}}
            
            # Execute workflow
            result = None
            for chunk in workflow.stream(workflow_input, config):
                if 'agent' in chunk:
                    result = chunk['agent']['messages'][-1]
            
            end_time = time.time()
            
            return {
                'content': result.content if result else _('no_response_generated'),
                'tokens_used': getattr(result, 'usage_metadata', {}).get('total_tokens', 0) if result else 0,
                'response_time_ms': int((end_time - start_time) * 1000)
            }
            
        except Exception as e:
            raise ValidationException(f"{_('workflow_execution_failed')}: {str(e)}")
    
    async def _execute_streaming_langgraph_workflow(self, workflow, 
                                                   workflow_input: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute LangGraph workflow with streaming"""
        try:
            import time
            start_time = time.time()
            
            # Create thread config
            config = {"configurable": {"thread_id": workflow_input.get('context', {}).get('timestamp', 'default')}}
            
            full_content = ""
            token_count = 0
            
            # Stream workflow execution
            for chunk in workflow.stream(workflow_input, config, stream_mode="values"):
                if 'agent' in chunk and 'messages' in chunk['agent']:
                    message = chunk['agent']['messages'][-1]
                    
                    if hasattr(message, 'content'):
                        # For incremental content
                        new_content = message.content[len(full_content):]
                        if new_content:
                            full_content = message.content
                            yield {
                                'type': 'content',
                                'content': new_content,
                                'total_content': full_content
                            }
                    
                    # Token usage if available
                    if hasattr(message, 'usage_metadata'):
                        token_count = message.usage_metadata.get('total_tokens', 0)
            
            # Send final metadata
            end_time = time.time()
            yield {
                'type': 'metadata',
                'data': {
                    'tokens_used': token_count,
                    'response_time_ms': int((end_time - start_time) * 1000),
                    'completed': True
                }
            }
            
        except Exception as e:
            yield {
                'type': 'error',
                'message': f"{_('streaming_workflow_failed')}: {str(e)}"
            }