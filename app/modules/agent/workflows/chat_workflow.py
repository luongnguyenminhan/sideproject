from typing import Dict, Any, AsyncGenerator
from app.modules.agent.workflows.base_workflow import BaseWorkflow
from app.modules.agent.services.langgraph_service import LangGraphService


class ChatWorkflow(BaseWorkflow):
    """Conversational chat workflow implementation"""
    
    def __init__(self, config):
        super().__init__(config)
        self.workflow_type = "conversational"
        self.langgraph_service = LangGraphService()
    
    async def execute(self, context: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
        """Execute conversational workflow"""
        
        if not self.validate_context(context):
            raise ValueError("Invalid context for chat workflow")
        
        # Enhance context for conversational flow
        enhanced_context = self.prepare_context(context)
        enhanced_context['conversation_style'] = 'friendly_helpful'
        enhanced_context['focus'] = 'user_engagement'
        
        # Add conversation-specific enhancements
        if enhanced_context.get('conversation_history'):
            enhanced_context['context_awareness'] = True
            enhanced_context['conversation_length'] = len(enhanced_context['conversation_history'])
        
        # Execute through LangGraph service
        result = await self.langgraph_service.execute_workflow(
            agent_config=self.config,
            context=enhanced_context,
            api_key=api_key
        )
        
        # Add chat-specific metadata
        result['metadata']['workflow_type'] = self.workflow_type
        result['metadata']['conversation_style'] = 'friendly_helpful'
        
        return result
    
    async def execute_streaming(self, context: Dict[str, Any], 
                              api_key: str = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute streaming conversational workflow"""
        
        if not self.validate_context(context):
            yield {
                'type': 'error',
                'message': 'Invalid context for chat workflow'
            }
            return
        
        # Enhance context for conversational flow
        enhanced_context = self.prepare_context(context)
        enhanced_context['conversation_style'] = 'friendly_helpful'
        enhanced_context['focus'] = 'user_engagement'
        
        # Add conversation-specific enhancements
        if enhanced_context.get('conversation_history'):
            enhanced_context['context_awareness'] = True
            enhanced_context['conversation_length'] = len(enhanced_context['conversation_history'])
        
        # Execute streaming through LangGraph service
        async for chunk in self.langgraph_service.execute_streaming_workflow(
            agent_config=self.config,
            context=enhanced_context,
            api_key=api_key
        ):
            # Add chat-specific metadata to chunks
            if chunk.get('type') == 'metadata':
                chunk['data']['workflow_type'] = self.workflow_type
                chunk['data']['conversation_style'] = 'friendly_helpful'
            
            yield chunk
    
    def prepare_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context specifically for chat workflow"""
        enhanced_context = super().prepare_context(context)
        
        # Add chat-specific system prompt enhancement
        system_enhancement = """
        You are engaging in a friendly conversation. Focus on:
        1. Understanding the user's needs and context
        2. Providing helpful and accurate responses
        3. Maintaining a conversational and engaging tone
        4. Remembering previous context when relevant
        5. Asking clarifying questions when needed
        """
        
        enhanced_context['system_enhancement'] = system_enhancement
        enhanced_context['response_style'] = 'conversational'
        
        return enhanced_context
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get chat workflow capabilities"""
        return {
            'streaming': True,
            'memory': True,
            'tools': ['memory_retrieval', 'context_awareness'],
            'features': [
                'natural_conversation',
                'context_memory',
                'friendly_tone',
                'clarifying_questions'
            ],
            'max_context_length': 10,
            'response_style': 'conversational'
        }