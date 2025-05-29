from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db
from app.modules.agent.dal.agent_dal import AgentDAL
from app.modules.agent.dal.agent_config_dal import AgentConfigDAL
from app.modules.agent.dal.agent_memory_dal import AgentMemoryDAL
from app.modules.agent.models.agent import Agent
from app.modules.agent.models.agent_config import AgentConfig
from app.modules.agent.models.agent_memory import MemoryType
from app.exceptions.exception import NotFoundException, ValidationException
from app.middleware.translation_manager import _
from typing import Dict, Any, List, Optional, AsyncGenerator
import json
import uuid
import asyncio


class AgentWorkflowRepo:
    """Repository for Agent workflow execution and LangGraph integration"""
    
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.agent_dal = AgentDAL(db)
        self.config_dal = AgentConfigDAL(db)
        self.memory_dal = AgentMemoryDAL(db)
    
    async def execute_chat_workflow(self, agent_id: str, user_id: str, 
                                  conversation_id: str, user_message: str,
                                  api_key: str = None) -> Dict[str, Any]:
        """Execute chat workflow for agent"""
        
        # Get agent and config
        agent = self.agent_dal.get_agent_by_user_and_id(user_id, agent_id)
        if not agent:
            raise NotFoundException(_('agent_not_found'))
        
        config = self.config_dal.get_by_id(agent.config_id)
        if not config:
            raise NotFoundException(_('agent_config_not_found'))
        
        # Get conversation memories for context
        conversation_memories = self.memory_dal.get_conversation_memories(
            agent_id, conversation_id
        )
        
        # Get important memories for context
        important_memories = self.memory_dal.get_important_memories(
            agent_id, min_importance=0.7, limit=10
        )
        
        # Prepare context
        context = self._prepare_workflow_context(
            agent, config, conversation_memories, important_memories, user_message
        )
        
        # Store user message in memory
        self._store_user_message_memory(agent_id, conversation_id, user_message)
        
        try:
            # Execute workflow using LangGraph service
            from app.modules.agent.services.langgraph_service import LangGraphService
            
            langgraph_service = LangGraphService()
            response = await langgraph_service.execute_workflow(
                agent_config=config,
                context=context,
                api_key=api_key
            )
            
            # Store AI response in memory
            self._store_ai_response_memory(
                agent_id, conversation_id, response['content'], response.get('metadata', {})
            )
            
            # Update workflow state
            self._update_workflow_state(agent_id, conversation_id, response)
            
            return response
            
        except Exception as e:
            # Store error in memory for debugging
            self._store_error_memory(agent_id, conversation_id, str(e))
            raise ValidationException(_('workflow_execution_failed'))
    
    async def execute_streaming_workflow(self, agent_id: str, user_id: str,
                                       conversation_id: str, user_message: str,
                                       api_key: str = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute streaming chat workflow"""
        
        # Get agent and config
        agent = self.agent_dal.get_agent_by_user_and_id(user_id, agent_id)
        if not agent:
            raise NotFoundException(_('agent_not_found'))
        
        config = self.config_dal.get_by_id(agent.config_id)
        if not config:
            raise NotFoundException(_('agent_config_not_found'))
        
        # Prepare context (same as regular workflow)
        conversation_memories = self.memory_dal.get_conversation_memories(
            agent_id, conversation_id
        )
        important_memories = self.memory_dal.get_important_memories(
            agent_id, min_importance=0.7, limit=10
        )
        
        context = self._prepare_workflow_context(
            agent, config, conversation_memories, important_memories, user_message
        )
        
        # Store user message
        self._store_user_message_memory(agent_id, conversation_id, user_message)
        
        # Execute streaming workflow
        from app.modules.agent.services.langgraph_service import LangGraphService
        
        langgraph_service = LangGraphService()
        
        try:
            full_response = ""
            metadata = {}
            
            async for chunk in langgraph_service.execute_streaming_workflow(
                agent_config=config,
                context=context,
                api_key=api_key
            ):
                if chunk.get('type') == 'content':
                    full_response += chunk.get('content', '')
                elif chunk.get('type') == 'metadata':
                    metadata.update(chunk.get('data', {}))
                
                yield chunk
            
            # Store complete response in memory
            if full_response:
                self._store_ai_response_memory(
                    agent_id, conversation_id, full_response, metadata
                )
                
                # Update workflow state
                self._update_workflow_state(agent_id, conversation_id, {
                    'content': full_response,
                    'metadata': metadata
                })
                
        except Exception as e:
            self._store_error_memory(agent_id, conversation_id, str(e))
            yield {
                'type': 'error',
                'message': _('workflow_execution_failed'),
                'error': str(e)
            }
    
    def get_agent_memory_context(self, agent_id: str, conversation_id: str = None,
                               limit: int = 20) -> Dict[str, Any]:
        """Get memory context for agent"""
        context = {
            'conversation_memories': [],
            'important_memories': [],
            'workflow_state': {}
        }
        
        if conversation_id:
            context['conversation_memories'] = [
                memory.content for memory in 
                self.memory_dal.get_conversation_memories(agent_id, conversation_id)
            ]
        
        context['important_memories'] = [
            memory.content for memory in
            self.memory_dal.get_important_memories(agent_id, limit=limit)
        ]
        
        # Get latest workflow state
        workflow_memories = self.memory_dal.get_memories_by_agent(
            agent_id, MemoryType.WORKFLOW_STATE, limit=1
        )
        if workflow_memories:
            context['workflow_state'] = workflow_memories[0].content
        
        return context
    
    def clear_agent_memory(self, agent_id: str, user_id: str, 
                          memory_type: MemoryType = None) -> int:
        """Clear agent memory with validation"""
        # Verify user owns agent
        agent = self.agent_dal.get_agent_by_user_and_id(user_id, agent_id)
        if not agent:
            raise NotFoundException(_('agent_not_found'))
        
        if memory_type:
            return self.memory_dal.clear_memories_by_type(agent_id, memory_type)
        else:
            # Clear all non-essential memories
            total_cleared = 0
            total_cleared += self.memory_dal.clear_memories_by_type(agent_id, MemoryType.SHORT_TERM)
            total_cleared += self.memory_dal.clear_memories_by_type(agent_id, MemoryType.CONTEXT)
            return total_cleared
    
    def _prepare_workflow_context(self, agent: Agent, config: AgentConfig,
                                conversation_memories: List, important_memories: List,
                                user_message: str) -> Dict[str, Any]:
        """Prepare context for workflow execution"""
        context = {
            'agent': {
                'id': agent.id,
                'name': agent.name,
                'type': agent.agent_type.value,
                'description': agent.description
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
            'user_message': user_message,
            'conversation_history': [memory.content for memory in conversation_memories],
            'important_context': [memory.content for memory in important_memories],
            'timestamp': str(uuid.uuid4())  # Session ID for this execution
        }
        
        return context
    
    def _store_user_message_memory(self, agent_id: str, conversation_id: str, message: str):
        """Store user message in memory"""
        self.memory_dal.create_memory(
            agent_id=agent_id,
            conversation_id=conversation_id,
            memory_type=MemoryType.CONTEXT,
            content={
                'role': 'user',
                'content': message,
                'timestamp': str(uuid.uuid4())
            },
            importance_score=0.5
        )
    
    def _store_ai_response_memory(self, agent_id: str, conversation_id: str, 
                                response: str, meta_data: Dict[str, Any]):
        """Store AI response in memory"""
        self.memory_dal.create_memory(
            agent_id=agent_id,
            conversation_id=conversation_id,
            memory_type=MemoryType.CONTEXT,
            content={
                'role': 'assistant',
                'content': response,
                'meta_data': meta_data,
                'timestamp': str(uuid.uuid4())
            },
            importance_score=0.6
        )
    
    def _store_error_memory(self, agent_id: str, conversation_id: str, error: str):
        """Store error in memory for debugging"""
        self.memory_dal.create_memory(
            agent_id=agent_id,
            conversation_id=conversation_id,
            memory_type=MemoryType.SHORT_TERM,
            content={
                'type': 'error',
                'error': error,
                'timestamp': str(uuid.uuid4())
            },
            importance_score=0.3
        )
    
    def _update_workflow_state(self, agent_id: str, conversation_id: str, 
                             response: Dict[str, Any]):
        """Update workflow state after execution"""
        # Get current state
        current_state_memories = self.memory_dal.get_memories_by_agent(
            agent_id, MemoryType.WORKFLOW_STATE, limit=1
        )
        
        current_state = current_state_memories[0].content if current_state_memories else {}
        
        # Update state
        updated_state = {
            **current_state,
            'last_interaction': str(uuid.uuid4()),
            'conversation_count': current_state.get('conversation_count', 0) + 1,
            'last_response_metadata': response.get('metadata', {}),
            'last_conversation_id': conversation_id
        }
        
        # Store updated state
        self.memory_dal.create_memory(
            agent_id=agent_id,
            memory_type=MemoryType.WORKFLOW_STATE,
            content=updated_state,
            importance_score=1.0
        )