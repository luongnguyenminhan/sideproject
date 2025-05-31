from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db
from app.modules.agent.dal.system_config_dal import SystemConfigDAL
from app.modules.agent.models.system_config import SystemConfig
from app.exceptions.exception import NotFoundException, ValidationException
from app.middleware.translation_manager import _
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class SystemConfigRepo:
	"""Repository for System Configuration operations"""

	def __init__(self, db: Session = Depends(get_db)):
		logger.info('SystemConfigRepo.__init__() - ENTRY')
		self.db = db
		self.config_dal = SystemConfigDAL(db)
		logger.info('SystemConfigRepo.__init__() - EXIT')

	def get_system_config(self) -> SystemConfig:
		"""Get or create system configuration"""
		logger.info('SystemConfigRepo.get_system_config() - ENTRY')

		config = self.config_dal.get_or_create_default_config()

		logger.info(f'System config retrieved: {config.id}')
		return config

	def update_system_config(self, updates: Dict[str, Any]) -> SystemConfig:
		"""Update system configuration"""
		logger.info('SystemConfigRepo.update_system_config() - ENTRY')
		logger.info(f'Updates: {list(updates.keys())}')

		# Get current config
		config = self.get_system_config()

		# Validate model compatibility if being updated
		if 'model_provider' in updates or 'model_name' in updates:
			from app.modules.agent.services.agent_factory import AgentFactory

			provider = updates.get('model_provider', config.model_provider)
			model = updates.get('model_name', config.model_name)

			if not AgentFactory.validate_model_compatibility(provider, model):
				raise ValidationException(_('model_provider_incompatible'))

		# Update configuration
		updated_config = self.config_dal.update(config.id, updates)

		logger.info('System config updated successfully')
		return updated_config

	def get_available_models(self) -> Dict[str, list]:
		"""Get available models"""
		from app.modules.agent.services.agent_factory import AgentFactory

		return AgentFactory.list_available_models()

	def validate_system_config(self) -> bool:
		"""Validate current system configuration"""
		try:
			config = self.get_system_config()

			# Basic validation
			if not config.model_name or not config.model_provider:
				return False

			if config.temperature < 0 or config.temperature > 2:
				return False

			if config.max_tokens and config.max_tokens < 1:
				return False

			return True
		except Exception:
			return False
