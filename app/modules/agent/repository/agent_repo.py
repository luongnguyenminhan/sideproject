from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db
from app.modules.chat.agent.dal.agent_dal import AgentDAL
from app.modules.chat.agent.dal.agent_config_dal import AgentConfigDAL
from app.modules.chat.agent.dal.agent_memory_dal import AgentMemoryDAL
from app.modules.chat.agent.models.agent import Agent, AgentType
from app.modules.chat.agent.models.agent_config import AgentConfig
from app.modules.chat.agent.models.agent_memory import AgentMemory, MemoryType
from app.exceptions.exception import NotFoundException, ValidationException, ForbiddenException
from app.middleware.translation_manager import _
from typing import List, Optional, Dict, Any
import uuid


class AgentRepo:
    """Repository for Agent business logic and orchestration"""
    
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.agent_dal = AgentDAL(db)
        self.config_dal = AgentConfigDAL(db)
        self.memory_dal = AgentMemoryDAL(db)
    
    def create_agent(self, user_id: str, name: str, agent_type: AgentType, 
                    config_id: str, description: str = None) -> Agent:
        """Create new agent with validation"""
        # Verify config exists
        config = self.config_dal.get_by_id(config_id)
        if not config:
            raise NotFoundException(_('agent_config_not_found'))
        
        # Verify config type matches agent type
        if config.agent_type != agent_type.value:
            raise ValidationException(_('agent_type_config_mismatch'))
        
        # Create agent
        agent_data = {
            'name': name,
            'description': description,
            'agent_type': agent_type,
            'config_id': config_id,
            'user_id': user_id,
            'created_by': user_id,
            'is_active': True
        }
        
        agent = self.agent_dal.create(agent_data)
        
        # Initialize default memories
        self._initialize_agent_memory(agent.id)
        
        return agent
    
    def get_user_agents(self, user_id: str, is_active: bool = None) -> List[Agent]:
        """Get all agents for user"""
        return self.agent_dal.get_agents_by_user(user_id, is_active)
    
    def get_agent_by_id(self, agent_id: str, user_id: str) -> Agent:
        """Get agent by ID with user validation"""
        agent = self.agent_dal.get_agent_by_user_and_id(user_id, agent_id)
        if not agent:
            raise NotFoundException(_('agent_not_found'))
        return agent
    
    def update_agent(self, agent_id: str, user_id: str, updates: Dict[str, Any]) -> Agent:
        """Update agent with validation"""
        agent = self.get_agent_by_id(agent_id, user_id)
        
        # If config is being updated, validate it
        if 'config_id' in updates:
            config = self.config_dal.get_by_id(updates['config_id'])
            if not config:
                raise NotFoundException(_('agent_config_not_found'))
            
            # Check type compatibility
            if 'agent_type' in updates and config.agent_type != updates['agent_type'].value:
                raise ValidationException(_('agent_type_config_mismatch'))
            elif config.agent_type != agent.agent_type.value:
                raise ValidationException(_('agent_type_config_mismatch'))
        
        return self.agent_dal.update(agent_id, updates)
    
    def delete_agent(self, agent_id: str, user_id: str) -> bool:
        """Delete agent with validation"""
        agent = self.get_agent_by_id(agent_id, user_id)
        
        # Clear all memories first
        self.memory_dal.clear_memories_by_type(agent_id, MemoryType.SHORT_TERM)
        self.memory_dal.clear_memories_by_type(agent_id, MemoryType.LONG_TERM)
        self.memory_dal.clear_memories_by_type(agent_id, MemoryType.CONTEXT)
        self.memory_dal.clear_memories_by_type(agent_id, MemoryType.WORKFLOW_STATE)
        
        return self.agent_dal.delete(agent_id)
    
    def get_or_create_default_agent(self, user_id: str) -> Agent:
        """Get user's default agent or create one if none exists"""
        agent = self.agent_dal.get_default_agent_for_user(user_id)
        
        if not agent:
            # Create default agent with default config
            default_config = self.config_dal.get_default_config_for_type('chat')
            if not default_config:
                raise ValidationException(_('no_default_config_available'))
            
            agent = self.create_agent(
                user_id=user_id,
                name=f"Default Assistant",
                agent_type=AgentType.CHAT,
                config_id=default_config.id,
                description="Default AI assistant for conversations"
            )
        
        return agent
    
    def get_agent_with_config(self, agent_id: str, user_id: str) -> tuple[Agent, AgentConfig]:
        """Get agent with its configuration"""
        agent = self.get_agent_by_id(agent_id, user_id)
        config = self.config_dal.get_by_id(agent.config_id)
        if not config:
            raise NotFoundException(_('agent_config_not_found'))
        return agent, config
    
    def toggle_agent_status(self, agent_id: str, user_id: str) -> Agent:
        """Toggle agent active status"""
        agent = self.get_agent_by_id(agent_id, user_id)
        success = self.agent_dal.update_agent_status(agent_id, not agent.is_active)
        if not success:
            raise ValidationException(_('failed_to_update_agent_status'))
        
        # Refresh agent data
        return self.agent_dal.get_by_id(agent_id)
    
    def _initialize_agent_memory(self, agent_id: str):
        """Initialize default memory for new agent"""
        # Create initial workflow state memory
        initial_state = {
            'initialized': True,
            'conversation_count': 0,
            'last_interaction': None,
            'preferences': {}
        }
        
        self.memory_dal.create_memory(
            agent_id=agent_id,
            memory_type=MemoryType.WORKFLOW_STATE,
            content=initial_state,
            importance_score=1.0,
            metadata={'type': 'initialization'}
        )