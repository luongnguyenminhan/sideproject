from sqlalchemy import Column, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.base_model import BaseEntity
import enum


class AgentType(str, enum.Enum):
	"""Agent type enumeration"""

	CHAT = 'chat'
	ANALYSIS = 'analysis'
	TASK = 'task'
	CUSTOM = 'custom'


class Agent(BaseEntity):
	"""Agent model - represents AI agents with specific configurations"""

	__tablename__ = 'agents'

	name = Column(String(255), nullable=False)
	description = Column(String(500), nullable=True)
	agent_type = Column(Enum(AgentType), nullable=False, default=AgentType.CHAT)
	config_id = Column(String(36), ForeignKey('agent_configs.id'), nullable=False)
	user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
	is_active = Column(Boolean, nullable=False, default=True)
	created_by = Column(String(36), ForeignKey('users.id'), nullable=False)

	# Relationships
	config = relationship('AgentConfig', back_populates='agents')
	memories = relationship('AgentMemory', back_populates='agent', cascade='all, delete-orphan')

	def __repr__(self):
		return f'<Agent(id={self.id}, name={self.name}, type={self.agent_type})>'
