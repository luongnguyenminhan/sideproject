from sqlalchemy import Column, String, Float, Integer, JSON, Enum
from app.core.base_model import BaseEntity
import enum


class ModelProvider(str, enum.Enum):
	"""Model provider enumeration"""

	GOOGLE = 'google'


class SystemConfig(BaseEntity):
	"""System-wide AI configuration - single record only"""

	__tablename__ = 'system_configs'

	name = Column(String(255), nullable=False, default='System AI Configuration')
	description = Column(
		String(500),
		nullable=True,
		default='Global AI configuration for all conversations',
	)
	model_provider = Column(Enum(ModelProvider), nullable=False, default=ModelProvider.GOOGLE)
	model_name = Column(String(100), nullable=False, default='gemini-2.0-flash')
	temperature = Column(Float, nullable=False, default=0.7)
	max_tokens = Column(Integer, nullable=True, default=2048)
	default_system_prompt = Column(String(2000), nullable=True, default='You are a helpful AI assistant.')
	tools_config = Column(JSON, nullable=True)  # JSON config for available tools
	is_active = Column(String(10), nullable=False, default='true')  # Only one active config allowed

	def __repr__(self):
		return f'<SystemConfig(id={self.id}, name={self.name}, provider={self.model_provider})>'
