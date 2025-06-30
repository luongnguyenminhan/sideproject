from app.modules.agent.models.agent import Agent, ModelProvider
from sqlalchemy.orm import Session
from app.core.base_dal import BaseDAL
from typing import Optional, Dict, Any


class AgentDAL(BaseDAL[Agent]):
	"""Data Access Layer for Agent operations"""

	def __init__(self, db: Session):
		super().__init__(db, Agent)

	def get_system_agent(self) -> Optional[Agent]:
		"""Get the single system agent"""
		return self.db.query(self.model).filter(self.model.is_active == True, self.model.is_deleted == False).first()

	def get_or_create_system_agent(self) -> Agent:
		"""Get existing system agent or create default one"""
		agent = self.get_system_agent()
		if not agent:
			# Create default system agent with embedded config and API key
			default_data = {
				'name': 'System Assistant',
				'description': 'AI Assistant for all conversations',
				'is_active': True,
				'model_provider': ModelProvider.GOOGLE,
				'model_name': 'gemini-2.0-flash-lite',
				'temperature': 0.7,
				'max_tokens': 2048,
				'default_system_prompt': 'You are a helpful AI assistant. Provide accurate, helpful, and friendly responses.',
				'tools_config': {'web_search': False, 'memory_retrieval': True},
				'api_provider': 'google',
				'api_key': None,  # Will be set by user
			}
			agent = self.create(default_data)
			self.db.commit()
			self.db.refresh(agent)
		return agent

	def update_agent_config(self, agent_id: str, config_updates: Dict[str, Any]) -> Optional[Agent]:
		"""Update agent configuration fields"""
		return self.update(agent_id, config_updates)

	def update_agent_api_key(self, agent_id: str, api_key: str, api_provider: str = 'google') -> Optional[Agent]:
		"""Update agent API key"""
		updates = {'api_key': api_key, 'api_provider': api_provider}
		print(f'Updating agent {agent_id} API key with provider {api_provider}')
		return self.update(agent_id, updates)

	def deactivate_all_agents(self) -> int:
		"""Deactivate all agents (for system reset)"""
		return self.db.query(self.model).update({'is_active': False})

	def get_agent_api_key(self, user_id: str) -> Optional[str]:
		"""Get the API key for a specific agent"""
		agent = (
			self.db.query(self.model)
			.filter(
				self.model.user_id == user_id,
				self.model.is_active == True,
				self.model.is_deleted == False,
			)
			.first()
		)
		return agent.api_key

	def create_user_agent(self, user_id: str, agent_data: Dict[str, Any]) -> Agent:
		"""Create an agent for a specific user"""
		agent_data['user_id'] = user_id
		return self.create(agent_data)

	def get_user_agents(self, user_id: str):
		"""Get all agents for a specific user"""
		return self.db.query(self.model).filter(self.model.user_id == user_id, self.model.is_deleted == False).all()
