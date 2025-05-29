from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from app.core.base_dal import BaseDAL
from app.modules.agent.models.agent_memory import AgentMemory, MemoryType
from typing import List, Optional, Dict, Any


class AgentMemoryDAL(BaseDAL[AgentMemory]):
	"""Data Access Layer for Agent Memory operations"""

	def __init__(self, db: Session):
		super().__init__(db, AgentMemory)

	def get_memories_by_agent(self, agent_id: str, memory_type: MemoryType = None, limit: int = 50) -> List[AgentMemory]:
		"""Get memories for specific agent"""
		query = self.db.query(self.model).filter(self.model.agent_id == agent_id, self.model.is_deleted == False)

		if memory_type:
			query = query.filter(self.model.memory_type == memory_type)

		return query.order_by(desc(self.model.create_date)).limit(limit).all()

	def get_conversation_memories(self, agent_id: str, conversation_id: str) -> List[AgentMemory]:
		"""Get memories for specific conversation"""
		return (
			self.db.query(self.model)
			.filter(self.model.agent_id == agent_id, self.model.conversation_id == conversation_id, self.model.is_deleted == False)
			.order_by(self.model.create_date.asc())
			.all()
		)

	def get_session_memories(self, agent_id: str, session_id: str) -> List[AgentMemory]:
		"""Get memories for specific session"""
		return self.db.query(self.model).filter(self.model.agent_id == agent_id, self.model.session_id == session_id, self.model.is_deleted == False).order_by(self.model.create_date.asc()).all()

	def get_important_memories(self, agent_id: str, min_importance: float = 0.7, limit: int = 20) -> List[AgentMemory]:
		"""Get high importance memories"""
		return (
			self.db.query(self.model)
			.filter(self.model.agent_id == agent_id, self.model.importance_score >= min_importance, self.model.is_deleted == False)
			.order_by(desc(self.model.importance_score))
			.limit(limit)
			.all()
		)

	def create_memory(
		self, agent_id: str, memory_type: MemoryType, content: Dict[str, Any], conversation_id: str = None, session_id: str = None, importance_score: float = 0.5, meta_data: Dict[str, Any] = None
	) -> AgentMemory:
		"""Create new memory entry"""
		memory = AgentMemory(
			agent_id=agent_id, conversation_id=conversation_id, memory_type=memory_type, content=content, importance_score=importance_score, session_id=session_id, meta_data=meta_data or {}
		)

		self.db.add(memory)
		self.db.commit()
		self.db.refresh(memory)
		return memory

	def clear_memories_by_type(self, agent_id: str, memory_type: MemoryType) -> int:
		"""Clear all memories of specific type for agent"""
		try:
			result = self.db.query(self.model).filter(self.model.agent_id == agent_id, self.model.memory_type == memory_type).update({'is_deleted': True})
			self.db.commit()
			return result
		except Exception:
			self.db.rollback()
			return 0

	def clear_conversation_memories(self, agent_id: str, conversation_id: str) -> int:
		"""Clear memories for specific conversation"""
		try:
			result = self.db.query(self.model).filter(self.model.agent_id == agent_id, self.model.conversation_id == conversation_id).update({'is_deleted': True})
			self.db.commit()
			return result
		except Exception:
			self.db.rollback()
			return 0
