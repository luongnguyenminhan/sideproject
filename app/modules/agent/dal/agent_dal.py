from app.modules.agent.models.agent import Agent, AgentType
from sqlalchemy.orm import Session
from app.core.base_dal import BaseDAL
from typing import List, Optional


class AgentDAL(BaseDAL[Agent]):
	"""Data Access Layer for Agent operations"""

	def __init__(self, db: Session):
		super().__init__(db, Agent)

	def get_agents_by_user(self, user_id: str, is_active: bool = True) -> List[Agent]:
		"""Get all agents for a specific user"""
		query = self.db.query(self.model).filter(self.model.user_id == user_id, self.model.is_deleted == False)
		if is_active is not None:
			query = query.filter(self.model.is_active == is_active)
		return query.all()

	def get_agent_by_user_and_id(self, user_id: str, agent_id: str) -> Optional[Agent]:
		"""Get specific agent by user and agent ID"""
		return self.db.query(self.model).filter(self.model.id == agent_id, self.model.user_id == user_id, self.model.is_deleted == False).first()

	def get_agents_by_type(self, agent_type: AgentType, user_id: str = None) -> List[Agent]:
		"""Get agents by type, optionally filtered by user"""
		query = self.db.query(self.model).filter(self.model.agent_type == agent_type, self.model.is_deleted == False, self.model.is_active == True)
		if user_id:
			query = query.filter(self.model.user_id == user_id)
		return query.all()

	def get_default_agent_for_user(self, user_id: str) -> Optional[Agent]:
		"""Get the default/first active agent for user"""
		return self.db.query(self.model).filter(self.model.user_id == user_id, self.model.is_active == True, self.model.is_deleted == False).order_by(self.model.create_date.asc()).first()

	def update_agent_status(self, agent_id: str, is_active: bool) -> bool:
		"""Update agent active status"""
		try:
			result = self.db.query(self.model).filter(self.model.id == agent_id).update({'is_active': is_active})
			self.db.commit()
			return result > 0
		except Exception:
			self.db.rollback()
			return False
