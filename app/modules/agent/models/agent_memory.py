from sqlalchemy import Column, String, JSON, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.base_model import BaseEntity
import enum


class MemoryType(str, enum.Enum):
	"""Memory type enumeration"""

	SHORT_TERM = 'short_term'
	LONG_TERM = 'long_term'
	CONTEXT = 'context'
	WORKFLOW_STATE = 'workflow_state'


class AgentMemory(BaseEntity):
	"""Agent memory model - stores conversation context and agent state"""

	__tablename__ = 'agent_memories'

	agent_id = Column(String(36), ForeignKey('agents.id'), nullable=False)
	conversation_id = Column(String(36), ForeignKey('conversations.id'), nullable=True)
	memory_type = Column(Enum(MemoryType), nullable=False, default=MemoryType.CONTEXT)
	content = Column(JSON, nullable=False)  # Stores memory content as JSON
	importance_score = Column(Float, nullable=False, default=0.5)
	session_id = Column(String(255), nullable=True)  # For grouping related memories
	meta_data = Column(JSON, nullable=True)  # Đổi tên từ metadata sang meta_data

	# Relationships
	agent = relationship('Agent', back_populates='memories')

	def __repr__(self):
		return f'<AgentMemory(id={self.id}, agent_id={self.agent_id}, type={self.memory_type})>'
