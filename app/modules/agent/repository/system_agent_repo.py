from sqlalchemy.orm import Session
from fastapi import Depends

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.database import get_db

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.base_repo import BaseRepo

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.exceptions.exception import NotFoundException, ValidationException

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.middleware.translation_manager import _
from ..dal.agent_dal import AgentDAL
from ..models.agent import Agent, ModelProvider
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class SystemAgentRepo(BaseRepo):
	"""Repository for ultra-simplified System Agent operations"""

	def __init__(self, db: Session = Depends(get_db)):
		super().__init__(db)
		self.agent_dal = AgentDAL(db)

	def get_system_agent(self) -> Agent:
		"""Get or create the system agent with embedded config and API key"""

		agent = self.agent_dal.get_or_create_system_agent()

		return agent

	def update_system_agent_config(self, config_updates: Dict[str, Any]) -> Agent:
		"""Update system agent configuration"""

		# Get current agent
		agent = self.get_system_agent()

		# Validate model compatibility if being updated
		if 'model_provider' in config_updates or 'model_name' in config_updates:
			provider = config_updates.get('model_provider', agent.model_provider)
			model = config_updates.get('model_name', agent.model_name)

			if not self._validate_model_compatibility(provider, model):
				raise ValidationException(_('model_provider_incompatible'))

		# Update agent configuration
		print(f'Updating agent {agent.id} with config: {config_updates}')
		updated_agent = self.agent_dal.update_agent_config(agent.id, config_updates)
		self.db.commit()
		self.db.refresh(updated_agent)
		print(f'Agent after update: {updated_agent}')
		return updated_agent

	def update_system_agent_api_key(self, api_key: str, api_provider: str = 'google') -> Agent:
		"""Update system agent API key"""

		# Get current agent
		agent = self.get_system_agent()

		# Update API key
		updated_agent = self.agent_dal.update_agent_api_key(agent.id, api_key, api_provider)
		self.db.commit()
		self.db.refresh(updated_agent)
		return updated_agent

	def get_available_models(self) -> Dict[str, list]:
		"""Get available models by provider"""
		return {
			ModelProvider.GOOGLE.value: [
				'gemini-2.0-flash',
				'gemini-2.0-flash-lite',
			],
		}

	def _validate_model_compatibility(self, provider: ModelProvider, model_name: str) -> bool:
		"""Validate if model is compatible with provider"""
		available_models = self.get_available_models()
		return model_name in available_models.get(provider.value, [])

	def validate_system_agent(self) -> bool:
		"""Validate current system agent configuration"""
		try:
			agent = self.get_system_agent()

			# Basic validation
			if not agent.model_name or not agent.model_provider:
				return False

			if agent.temperature < 0 or agent.temperature > 2:
				return False

			if agent.max_tokens and agent.max_tokens < 1:
				return False

			return True
		except Exception:
			return False
