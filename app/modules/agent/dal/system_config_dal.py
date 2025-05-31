from app.modules.agent.models.system_config import SystemConfig, ModelProvider
from sqlalchemy.orm import Session
from app.core.base_dal import BaseDAL
from typing import Optional


class SystemConfigDAL(BaseDAL[SystemConfig]):
	"""Data Access Layer for System Configuration operations"""

	def __init__(self, db: Session):
		super().__init__(db, SystemConfig)

	def get_active_config(self) -> Optional[SystemConfig]:
		"""Get the active system configuration"""
		return self.db.query(self.model).filter(self.model.is_active == 'true', self.model.is_deleted == False).first()

	def get_or_create_default_config(self) -> SystemConfig:
		"""Get existing config or create default one"""
		config = self.get_active_config()
		if not config:
			# Create default config
			default_data = {
				'name': 'Default System Configuration',
				'description': 'Default AI configuration for all conversations',
				'model_provider': ModelProvider.GOOGLE,
				'model_name': 'gemini-2.0-flash',
				'temperature': 0.7,
				'max_tokens': 2048,
				'default_system_prompt': 'You are a helpful AI assistant. Provide accurate, helpful, and friendly responses.',
				'tools_config': {'web_search': False, 'memory_retrieval': True},
				'is_active': 'true',
			}
			config = self.create(default_data)
			self.db.commit()
			self.db.refresh(config)
		return config

	def deactivate_all_configs(self) -> int:
		"""Deactivate all configurations"""
		return self.db.query(self.model).update({'is_active': 'false'})

	def activate_config(self, config_id: str) -> bool:
		"""Activate a specific configuration (deactivates others)"""
		try:
			# Deactivate all
			self.deactivate_all_configs()
			# Activate the specified one
			result = self.db.query(self.model).filter(self.model.id == config_id).update({'is_active': 'true'})
			self.db.commit()
			return result > 0
		except Exception:
			self.db.rollback()
			return False
