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
		print('\033[92m[DEBUG] AgentRepo.__init__() - ENTRY\033[0m')
		self.db = db
		self.agent_dal = AgentDAL(db)
		self.config_dal = AgentConfigDAL(db)
		self.memory_dal = AgentMemoryDAL(db)
		print('\033[92m[DEBUG] AgentRepo.__init__() - EXIT\033[0m')

	def create_agent(self, user_id: str, name: str, agent_type: AgentType, config_id: str, description: str = None) -> Agent:
		"""Create new agent with validation"""
		print('\033[92m[DEBUG] AgentRepo.create_agent() - ENTRY\033[0m')

		# Verify config exists
		print('\033[93m[DEBUG] Verifying config exists\033[0m')
		config = self.config_dal.get_by_id(config_id)
		if not config:
			print('\033[91m[DEBUG] Config not found, raising NotFoundException\033[0m')
			raise NotFoundException(_('agent_config_not_found'))
		print(f'\033[96m[DEBUG] Config found: {config.id}, type: {config.agent_type}\033[0m')

		# Verify config type matches agent type
		print('\033[93m[DEBUG] Verifying config type matches agent type\033[0m')
		if config.agent_type != agent_type.value:
			print(f'\033[91m[DEBUG] Type mismatch: config.agent_type={config.agent_type}, agent_type.value={agent_type.value}\033[0m')
			raise ValidationException(_('agent_type_config_mismatch'))
		print('\033[96m[DEBUG] Config type validation passed\033[0m')

		# Create agent
		print('\033[93m[DEBUG] Creating agent data\033[0m')
		agent_data = {'name': name, 'description': description, 'agent_type': agent_type, 'config_id': config_id, 'user_id': user_id, 'created_by': user_id, 'is_active': True}
		print(f'\033[94m[DEBUG] Agent data: {agent_data}\033[0m')

		print('\033[93m[DEBUG] Calling agent_dal.create()\033[0m')
		agent = self.agent_dal.create(agent_data)
		self.db.commit()
		# refresh the agent to get the ID
		self.db.refresh(agent)
		print(f'\033[96m[DEBUG] Agent created with ID: {agent.id}\033[0m')

		# Initialize default memories
		print('\033[93m[DEBUG] Initializing agent memory\033[0m')
		self._initialize_agent_memory(agent.id)
		print('\033[96m[DEBUG] Agent memory initialized\033[0m')

		print('\033[92m[DEBUG] AgentRepo.create_agent() - EXIT\033[0m')
		return agent

	def get_user_agents(self, user_id: str, is_active: bool = None) -> List[Agent]:
		"""Get all agents for user"""
		print('\033[92m[DEBUG] AgentRepo.get_user_agents() - ENTRY\033[0m')
		print(f'\033[94m[DEBUG] Parameters: user_id={user_id}, is_active={is_active}\033[0m')

		agents = self.agent_dal.get_agents_by_user(user_id, is_active)
		print(f'\033[96m[DEBUG] Found {len(agents)} agents for user\033[0m')

		print('\033[92m[DEBUG] AgentRepo.get_user_agents() - EXIT\033[0m')
		return agents

	def get_agent_by_id(self, agent_id: str, user_id: str) -> Agent:
		"""Get agent by ID with user validation"""
		print('\033[92m[DEBUG] AgentRepo.get_agent_by_id() - ENTRY\033[0m')
		print(f'\033[94m[DEBUG] Parameters: agent_id={agent_id}, user_id={user_id}\033[0m')

		agent = self.agent_dal.get_agent_by_user_and_id(user_id, agent_id)
		if not agent:
			print('\033[91m[DEBUG] Agent not found, raising NotFoundException\033[0m')
			raise NotFoundException(_('agent_not_found'))

		print(f'\033[96m[DEBUG] Agent found: {agent.id}, name: {agent.name}\033[0m')
		print('\033[92m[DEBUG] AgentRepo.get_agent_by_id() - EXIT\033[0m')
		return agent

	def update_agent(self, agent_id: str, user_id: str, updates: Dict[str, Any]) -> Agent:
		"""Update agent with validation"""
		print('\033[92m[DEBUG] AgentRepo.update_agent() - ENTRY\033[0m')
		print(f'\033[94m[DEBUG] Parameters: agent_id={agent_id}, user_id={user_id}, updates={updates}\033[0m')

		print('\033[93m[DEBUG] Getting agent for validation\033[0m')
		agent = self.get_agent_by_id(agent_id, user_id)
		print(f'\033[96m[DEBUG] Agent retrieved: {agent.id}\033[0m')

		# If config is being updated, validate it
		if 'config_id' in updates:
			print('\033[93m[DEBUG] Config update detected, validating new config\033[0m')
			config = self.config_dal.get_by_id(updates['config_id'])
			if not config:
				print('\033[91m[DEBUG] New config not found, raising NotFoundException\033[0m')
				raise NotFoundException(_('agent_config_not_found'))

			# Check type compatibility
			print('\033[93m[DEBUG] Checking type compatibility\033[0m')
			if 'agent_type' in updates and config.agent_type != updates['agent_type'].value:
				print(f'\033[91m[DEBUG] Type mismatch with updates: config.agent_type={config.agent_type}, updates.agent_type={updates["agent_type"].value}\033[0m')
				raise ValidationException(_('agent_type_config_mismatch'))
			elif config.agent_type != agent.agent_type.value:
				print(f'\033[91m[DEBUG] Type mismatch with existing: config.agent_type={config.agent_type}, agent.agent_type={agent.agent_type.value}\033[0m')
				raise ValidationException(_('agent_type_config_mismatch'))
			print('\033[96m[DEBUG] Config type validation passed\033[0m')

		print('\033[93m[DEBUG] Calling agent_dal.update()\033[0m')
		updated_agent = self.agent_dal.update(agent_id, updates)
		print(f'\033[96m[DEBUG] Agent updated successfully\033[0m')

		print('\033[92m[DEBUG] AgentRepo.update_agent() - EXIT\033[0m')
		return updated_agent

	def delete_agent(self, agent_id: str, user_id: str) -> bool:
		"""Delete agent with validation"""
		print('\033[92m[DEBUG] AgentRepo.delete_agent() - ENTRY\033[0m')
		print(f'\033[94m[DEBUG] Parameters: agent_id={agent_id}, user_id={user_id}\033[0m')

		print('\033[93m[DEBUG] Getting agent for validation\033[0m')
		agent = self.get_agent_by_id(agent_id, user_id)
		print(f'\033[96m[DEBUG] Agent retrieved: {agent.id}\033[0m')

		# Clear all memories first
		print('\033[93m[DEBUG] Clearing agent memories\033[0m')
		print('\033[95m[DEBUG] Clearing SHORT_TERM memories\033[0m')
		self.memory_dal.clear_memories_by_type(agent_id, MemoryType.SHORT_TERM)
		print('\033[95m[DEBUG] Clearing LONG_TERM memories\033[0m')
		self.memory_dal.clear_memories_by_type(agent_id, MemoryType.LONG_TERM)
		print('\033[95m[DEBUG] Clearing CONTEXT memories\033[0m')
		self.memory_dal.clear_memories_by_type(agent_id, MemoryType.CONTEXT)
		print('\033[95m[DEBUG] Clearing WORKFLOW_STATE memories\033[0m')
		self.memory_dal.clear_memories_by_type(agent_id, MemoryType.WORKFLOW_STATE)
		print('\033[96m[DEBUG] All memories cleared\033[0m')

		print('\033[93m[DEBUG] Calling agent_dal.delete()\033[0m')
		result = self.agent_dal.delete(agent_id)
		print(f'\033[96m[DEBUG] Agent deletion result: {result}\033[0m')

		print('\033[92m[DEBUG] AgentRepo.delete_agent() - EXIT\033[0m')
		return result

	def get_or_create_default_agent(self, user_id: str) -> Agent:
		"""Get user's default agent or create one if none exists"""
		print('\033[92m[DEBUG] AgentRepo.get_or_create_default_agent() - ENTRY\033[0m')
		print(f'\033[94m[DEBUG] Parameters: user_id={user_id}\033[0m')

		try:
			# First try to get existing default agent
			print('\033[93m[DEBUG] Trying to get existing default agent\033[0m')
			agent = self.agent_dal.get_default_agent_for_user(user_id)

			if agent:
				print(f'\033[96m[DEBUG] Existing default agent found: {agent.id}\033[0m')
				print('\033[92m[DEBUG] AgentRepo.get_or_create_default_agent() - EXIT (existing)\033[0m')
				return agent

			# No existing agent found, create one using AgentFactory
			print('\033[93m[DEBUG] No existing agent found, creating new default agent\033[0m')
			# This will automatically create default config if it doesn't exist
			print('\033[93m[DEBUG] Calling AgentFactory.create_default_agent()\033[0m')
			agent = AgentFactory.create_default_agent(agent_type=AgentType.CHAT, user_id=user_id, agent_repo=self, custom_name='Default Assistant')

			if not agent:
				print('\033[91m[DEBUG] AgentFactory returned None, raising ValidationException\033[0m')
				raise ValidationException(_('failed_to_create_default_agent'))

			print(f'\033[96m[DEBUG] New default agent created: {agent.id}\033[0m')
			print('\033[92m[DEBUG] AgentRepo.get_or_create_default_agent() - EXIT (new)\033[0m')
			return agent

		except ValidationException:
			print('\033[91m[DEBUG] ValidationException caught, re-raising\033[0m')
			# Re-raise validation exceptions
			raise
		except Exception as e:
			print(f'\033[91m[DEBUG] Unexpected exception caught: {str(e)}\033[0m')
			# Handle unexpected errors
			raise ValidationException(f'{_("error_getting_or_creating_default_agent")}: {str(e)}')

	def get_agent_with_config(self, agent_id: str, user_id: str) -> tuple[Agent, AgentConfig]:
		"""Get agent with its configuration"""
		print('\033[92m[DEBUG] AgentRepo.get_agent_with_config() - ENTRY\033[0m')
		print(f'\033[94m[DEBUG] Parameters: agent_id={agent_id}, user_id={user_id}\033[0m')

		print('\033[93m[DEBUG] Getting agent\033[0m')
		agent = self.get_agent_by_id(agent_id, user_id)
		print(f'\033[96m[DEBUG] Agent retrieved: {agent.id}, config_id: {agent.config_id}\033[0m')

		print('\033[93m[DEBUG] Getting agent config\033[0m')
		config = self.config_dal.get_by_id(agent.config_id)
		if not config:
			print('\033[91m[DEBUG] Config not found, raising NotFoundException\033[0m')
			raise NotFoundException(_('agent_config_not_found'))

		print(f'\033[96m[DEBUG] Config retrieved: {config.id}\033[0m')
		print('\033[92m[DEBUG] AgentRepo.get_agent_with_config() - EXIT\033[0m')
		return agent, config

	def toggle_agent_status(self, agent_id: str, user_id: str) -> Agent:
		"""Toggle agent active status"""
		print('\033[92m[DEBUG] AgentRepo.toggle_agent_status() - ENTRY\033[0m')
		print(f'\033[94m[DEBUG] Parameters: agent_id={agent_id}, user_id={user_id}\033[0m')

		print('\033[93m[DEBUG] Getting agent for status toggle\033[0m')
		agent = self.get_agent_by_id(agent_id, user_id)
		print(f'\033[96m[DEBUG] Agent retrieved: {agent.id}, current status: {agent.is_active}\033[0m')

		new_status = not agent.is_active
		print(f'\033[94m[DEBUG] Toggling status to: {new_status}\033[0m')

		print('\033[93m[DEBUG] Calling agent_dal.update_agent_status()\033[0m')
		success = self.agent_dal.update_agent_status(agent_id, new_status)
		if not success:
			print('\033[91m[DEBUG] Status update failed, raising ValidationException\033[0m')
			raise ValidationException(_('failed_to_update_agent_status'))
		print('\033[96m[DEBUG] Status updated successfully\033[0m')

		# Refresh agent data
		print('\033[93m[DEBUG] Refreshing agent data\033[0m')
		updated_agent = self.agent_dal.get_by_id(agent_id)
		print(f'\033[96m[DEBUG] Agent refreshed: status={updated_agent.is_active}\033[0m')

		print('\033[92m[DEBUG] AgentRepo.toggle_agent_status() - EXIT\033[0m')
		return updated_agent

	def _initialize_agent_memory(self, agent_id: str):
		"""Initialize default memory for new agent"""
		print('\033[92m[DEBUG] AgentRepo._initialize_agent_memory() - ENTRY\033[0m')
		print(f'\033[94m[DEBUG] Parameters: agent_id={agent_id}\033[0m')

		# Create initial workflow state memory
		print('\033[93m[DEBUG] Creating initial workflow state memory\033[0m')
		initial_state = {'initialized': True, 'conversation_count': 0, 'last_interaction': None, 'preferences': {}}
		print(f'\033[94m[DEBUG] Initial state: {initial_state}\033[0m')

		print('\033[93m[DEBUG] Calling memory_dal.create_memory()\033[0m')
		memory = self.memory_dal.create_memory(agent_id=agent_id, memory_type=MemoryType.WORKFLOW_STATE, content=initial_state, importance_score=1.0, meta_data={'type': 'initialization'})
		print(f'\033[96m[DEBUG] Memory created: {memory.id if memory else "None"}\033[0m')

		print('\033[92m[DEBUG] AgentRepo._initialize_agent_memory() - EXIT\033[0m')

	def initialize_user_agents(self, user_id: str) -> Dict[str, Agent]:
		"""Initialize default agents for a new user"""
		print('\033[92m[DEBUG] AgentRepo.initialize_user_agents() - ENTRY\033[0m')
		print(f'\033[94m[DEBUG] Parameters: user_id={user_id}\033[0m')

		agents = {}

		try:
			# Ensure default configs exist
			print('\033[93m[DEBUG] Ensuring default configs exist\033[0m')
			self.ensure_default_configs_exist()
			print('\033[96m[DEBUG] Default configs verified\033[0m')

			# Create default chat agent (primary)
			print('\033[93m[DEBUG] Creating default chat agent\033[0m')
			chat_agent = AgentFactory.create_default_agent(agent_type=AgentType.CHAT, user_id=user_id, agent_repo=self, custom_name=f'Default Assistant')
			agents['chat'] = chat_agent
			print(f'\033[96m[DEBUG] Chat agent created: {chat_agent.id}\033[0m')

			# Optionally create other default agents
			# analysis_agent = AgentFactory.create_default_agent(
			#     agent_type=AgentType.ANALYSIS,
			#     user_id=user_id,
			#     agent_repo=self,
			#     custom_name=f'Data Analyst'
			# )
			# agents['analysis'] = analysis_agent

			print(f'\033[96m[DEBUG] Total agents created: {len(agents)}\033[0m')
			print('\033[92m[DEBUG] AgentRepo.initialize_user_agents() - EXIT\033[0m')
			return agents

		except Exception as e:
			print(f'\033[91m[DEBUG] Exception in initialize_user_agents: {str(e)}\033[0m')
			raise ValidationException(f'{_("failed_to_initialize_user_agents")}: {str(e)}')

	def ensure_default_configs_exist(self) -> bool:
		"""Ensure default configurations exist for all agent types"""
		print('\033[92m[DEBUG] AgentRepo.ensure_default_configs_exist() - ENTRY\033[0m')

		try:
			agent_types = [AgentType.CHAT, AgentType.ANALYSIS, AgentType.TASK]
			print(f'\033[94m[DEBUG] Checking agent types: {[t.value for t in agent_types]}\033[0m')

			for agent_type in agent_types:
				print(f'\033[93m[DEBUG] Processing agent type: {agent_type.value}\033[0m')
				config_name = f'default_{agent_type.value}_config'
				print(f'\033[94m[DEBUG] Looking for config: {config_name}\033[0m')

				existing_config = self.config_dal.get_config_by_name(config_name)

				if not existing_config:
					print(f'\033[95m[DEBUG] Config {config_name} not found, creating it\033[0m')
					# Use AgentFactory to create missing default config
					default_config = AgentFactory.get_default_config_template(agent_type)
					print(f'\033[94m[DEBUG] Default config template: {list(default_config.keys())}\033[0m')

					print('\033[93m[DEBUG] Calling AgentFactory._get_or_create_default_config()\033[0m')
					config = AgentFactory._get_or_create_default_config(agent_type, default_config, self)
					print(f'\033[96m[DEBUG] Config created: {config.id if config else "None"}\033[0m')
				else:
					print(f'\033[96m[DEBUG] Config {config_name} already exists: {existing_config.id}\033[0m')

			print('\033[96m[DEBUG] All default configs verified\033[0m')
			print('\033[92m[DEBUG] AgentRepo.ensure_default_configs_exist() - EXIT (success)\033[0m')
			return True
		except Exception as e:
			# Log error but don't fail completely
			print(f'\033[91m[DEBUG] Warning: Could not ensure all default configs exist: {e}\033[0m')
			print('\033[92m[DEBUG] AgentRepo.ensure_default_configs_exist() - EXIT (warning)\033[0m')
			return False

	def create_agent_with_default_config(self, user_id: str, agent_type: AgentType, name: str = None, description: str = None) -> Agent:
		"""Create agent with automatic default config creation if needed"""
		print('\033[92m[DEBUG] AgentRepo.create_agent_with_default_config() - ENTRY\033[0m')
		print(f'\033[94m[DEBUG] Parameters: user_id={user_id}, agent_type={agent_type}, name={name}, description={description}\033[0m')

		try:
			# Ensure default config exists for this agent type
			print('\033[93m[DEBUG] Ensuring default configs exist\033[0m')
			self.ensure_default_configs_exist()
			print('\033[96m[DEBUG] Default configs verified\033[0m')

			# Use AgentFactory to create agent with default settings
			default_name = name or f'Default {agent_type.value.title()} Agent'
			print(f'\033[94m[DEBUG] Using agent name: {default_name}\033[0m')

			print('\033[93m[DEBUG] Calling AgentFactory.create_default_agent()\033[0m')
			agent = AgentFactory.create_default_agent(agent_type=agent_type, user_id=user_id, agent_repo=self, custom_name=default_name)
			print(f'\033[96m[DEBUG] Agent created: {agent.id}\033[0m')

			# Update description if provided
			if description and description != agent.description:
				print(f'\033[93m[DEBUG] Updating description from "{agent.description}" to "{description}"\033[0m')
				agent = self.agent_dal.update(agent.id, {'description': description})
				print('\033[96m[DEBUG] Description updated\033[0m')

			print('\033[92m[DEBUG] AgentRepo.create_agent_with_default_config() - EXIT\033[0m')
			return agent

		except Exception as e:
			print(f'\033[91m[DEBUG] Exception in create_agent_with_default_config: {str(e)}\033[0m')
			raise ValidationException(f'{_("failed_to_create_agent_with_default_config")}: {str(e)}')
