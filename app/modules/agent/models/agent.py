from sqlalchemy import (
	Column,
	String,
	Boolean,
	Float,
	Integer,
	JSON,
	Enum,
	Text,
	ForeignKey,
)
from sqlalchemy.orm import relationship
from app.core.base_model import BaseEntity
import enum


class ModelProvider(str, enum.Enum):
	"""Model provider enumeration"""

	GOOGLE = 'google'


class Agent(BaseEntity):
	"""Ultra-simplified Agent model - single record with embedded config AND API key"""

	__tablename__ = 'agents'

	# Basic agent info
	name = Column(String(255), nullable=False, default='System Assistant')
	description = Column(String(500), nullable=True, default='AI Assistant for conversations')
	is_active = Column(Boolean, nullable=False, default=True)

	# User ownership (optional - remove if agents are global)
	user_id = Column(String(36), ForeignKey('users.id'), nullable=True)

	# Embedded LLM Configuration (no separate config table)
	model_provider = Column(Enum(ModelProvider), nullable=False, default=ModelProvider.GOOGLE)
	model_name = Column(String(100), nullable=False, default='gemini-2.0-flash')
	temperature = Column(Float, nullable=False, default=0.7)
	max_tokens = Column(Integer, nullable=True, default=2048)
	default_system_prompt = Column(Text, nullable=True, default='You are a helpful AI assistant.')
	tools_config = Column(JSON, nullable=True)  # JSON config for available tools

	# Embedded API Key (no separate api_keys table)
	api_key = Column(String(500), nullable=True)  # Encrypted API key
	api_provider = Column(String(50), nullable=False, default='google')

	# Relationships
	user = relationship('User', back_populates='agents')  # Remove if agents are global

	def __repr__(self):
		return f'<Agent(id={self.id}, name={self.name}, provider={self.model_provider})>'

	def get_api_key(self) -> str:
		"""Get decrypted API key"""
		# Add decryption logic here if needed
		return self.api_key

	def set_api_key(self, api_key: str):
		"""Set encrypted API key"""
		# Add encryption logic here if needed
		self.api_key = api_key
