from typing import Dict, List

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.exceptions.exception import ValidationException

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.middleware.translation_manager import _
import logging

from ..models.agent import ModelProvider

logger = logging.getLogger(__name__)


class AgentFactory(object):
	"""Simplified factory for model validation and basic utilities"""

	@classmethod
	def list_available_models(cls) -> Dict[str, List[str]]:
		"""List available models by provider"""
		logger.info('AgentFactory.list_available_models() - ENTRY')
		models = {
			ModelProvider.GOOGLE.value: [
				'gemini-2.0-flash',
				'gemini-2.0-flash-lite',
			],
		}
		logger.info(f'Available models: {models}')
		return models

	@classmethod
	def validate_model_compatibility(cls, provider: ModelProvider, model_name: str) -> bool:
		"""Validate if model is compatible with provider"""
		logger.info(f'AgentFactory.validate_model_compatibility() - provider={provider}, model={model_name}')

		available_models = cls.list_available_models()
		compatible = model_name in available_models.get(provider.value, [])

		logger.info(f'Model compatibility result: {compatible}')
		return compatible

	@classmethod
	def get_default_config(cls) -> Dict[str, any]:
		"""Get default system configuration"""
		return {
			'name': 'System Configuration',
			'description': 'Default system-wide AI configuration',
			'model_provider': ModelProvider.GOOGLE,
			'model_name': 'gemini-2.0-flash-lite',
			'temperature': 1,
			'max_tokens': 2048,
			'tools_config': {
				'web_search': False,
				'memory_retrieval': True,
				'custom_tools': [],
			},
			'workflow_config': {
				'type': 'conversational',
				'memory_enabled': True,
				'context_window': 10,
			},
		}
