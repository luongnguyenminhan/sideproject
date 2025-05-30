from app.modules.agent.dal.agent_config_dal import AgentConfigDAL
from app.modules.agent.dal.agent_dal import AgentDAL
from app.modules.agent.dal.agent_memory_dal import AgentMemoryDAL
from app.modules.agent.models.agent import Agent, AgentType
from app.modules.agent.models.agent_config import AgentConfig
from app.modules.agent.models.agent_memory import MemoryType
from app.modules.agent.services.agent_factory import AgentFactory
from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db

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

	def create_agent(self, user_id: str, name: str, agent_type: AgentType, config_id: str, description: str = None) -> Agent:
		"""Create new agent with validation"""
		# Verify config exists
		config = self.config_dal.get_by_id(config_id)
		if not config:
			raise NotFoundException(_('agent_config_not_found'))

		# Verify config type matches agent type
		if config.agent_type != agent_type.value:
			raise ValidationException(_('agent_type_config_mismatch'))

		# Create agent
		agent_data = {'name': name, 'description': description, 'agent_type': agent_type, 'config_id': config_id, 'user_id': user_id, 'created_by': user_id, 'is_active': True}

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
		try:
			# First try to get existing default agent
			agent = self.agent_dal.get_default_agent_for_user(user_id)

			if agent:
				return agent

			# No existing agent found, create one using AgentFactory
			# This will automatically create default config if it doesn't exist
			agent = AgentFactory.create_default_agent(agent_type=AgentType.CHAT, user_id=user_id, agent_repo=self, custom_name='Default Assistant')

			if not agent:
				raise ValidationException(_('failed_to_create_default_agent'))

			return agent

		except ValidationException:
			# Re-raise validation exceptions
			raise
		except Exception as e:
			# Handle unexpected errors
			raise ValidationException(f'{_("error_getting_or_creating_default_agent")}: {str(e)}')

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
		initial_state = {'initialized': True, 'conversation_count': 0, 'last_interaction': None, 'preferences': {}}

		self.memory_dal.create_memory(agent_id=agent_id, memory_type=MemoryType.WORKFLOW_STATE, content=initial_state, importance_score=1.0, meta_data={'type': 'initialization'})

	def initialize_user_agents(self, user_id: str) -> Dict[str, Agent]:
		"""Initialize default agents for a new user"""
		agents = {}

		try:
			# Ensure default configs exist
			self.ensure_default_configs_exist()

			# Create default chat agent (primary)
			chat_agent = AgentFactory.create_default_agent(agent_type=AgentType.CHAT, user_id=user_id, agent_repo=self, custom_name=f'Default Assistant')
			agents['chat'] = chat_agent

			# Optionally create other default agents
			# analysis_agent = AgentFactory.create_default_agent(
			#     agent_type=AgentType.ANALYSIS,
			#     user_id=user_id,
			#     agent_repo=self,
			#     custom_name=f'Data Analyst'
			# )
			# agents['analysis'] = analysis_agent

			return agents

		except Exception as e:
			raise ValidationException(f'{_("failed_to_initialize_user_agents")}: {str(e)}')

	def ensure_default_configs_exist(self) -> bool:
		"""Ensure default configurations exist for all agent types"""
		try:
			for agent_type in [AgentType.CHAT, AgentType.ANALYSIS, AgentType.TASK]:
				config_name = f'default_{agent_type.value}_config'
				existing_config = self.config_dal.get_config_by_name(config_name)

				if not existing_config:
					# Use AgentFactory to create missing default config
					default_config = AgentFactory.get_default_config_template(agent_type)
					AgentFactory._get_or_create_default_config(agent_type, default_config, self)

			return True
		except Exception as e:
			# Log error but don't fail completely
			print(f'Warning: Could not ensure all default configs exist: {e}')
			return False

	def create_agent_with_default_config(self, user_id: str, agent_type: AgentType, name: str = None, description: str = None) -> Agent:
		"""Create agent with automatic default config creation if needed"""
		try:
			# Ensure default config exists for this agent type
			self.ensure_default_configs_exist()

			# Use AgentFactory to create agent with default settings
			agent = AgentFactory.create_default_agent(agent_type=agent_type, user_id=user_id, agent_repo=self, custom_name=name or f'Default {agent_type.value.title()} Agent')

			# Update description if provided
			if description and description != agent.description:
				agent = self.agent_dal.update(agent.id, {'description': description})

			return agent

		except Exception as e:
			raise ValidationException(f'{_("failed_to_create_agent_with_default_config")}: {str(e)}')
