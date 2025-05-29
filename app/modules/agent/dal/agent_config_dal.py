from app.modules.agent.models.agent_config import AgentConfig, ModelProvider
from sqlalchemy.orm import Session
from app.core.base_dal import BaseDAL
from typing import List, Optional


class AgentConfigDAL(BaseDAL[AgentConfig]):
	"""Data Access Layer for Agent Configuration operations"""

	def __init__(self, db: Session):
		super().__init__(db, AgentConfig)

	def get_configs_by_type(self, agent_type: str) -> List[AgentConfig]:
		"""Get configurations by agent type"""
		return self.db.query(self.model).filter(self.model.agent_type == agent_type, self.model.is_deleted == False).all()

	def get_configs_by_provider(self, provider: ModelProvider) -> List[AgentConfig]:
		"""Get configurations by model provider"""
		return self.db.query(self.model).filter(self.model.model_provider == provider, self.model.is_deleted == False).all()

	def get_config_by_name(self, name: str) -> Optional[AgentConfig]:
		"""Get configuration by name"""
		return self.db.query(self.model).filter(self.model.name == name, self.model.is_deleted == False).first()

	def get_default_config_for_type(self, agent_type: str) -> Optional[AgentConfig]:
		"""Get default configuration for agent type"""
		return self.db.query(self.model).filter(self.model.agent_type == agent_type, self.model.is_deleted == False).order_by(self.model.create_date.asc()).first()

	def search_configs(self, search_term: str) -> List[AgentConfig]:
		"""Search configurations by name or description"""
		search = f'%{search_term}%'
		return self.db.query(self.model).filter((self.model.name.ilike(search) | self.model.description.ilike(search)), self.model.is_deleted == False).all()
