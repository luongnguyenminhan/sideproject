from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator, Optional
from app.modules.agent.models.agent_config import AgentConfig


class BaseWorkflow(ABC):
	"""Abstract base class for all agent workflows"""

	def __init__(self, config: AgentConfig):
		self.config = config
		self.workflow_type = 'base'

	@abstractmethod
	async def execute(self, context: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
		"""Execute workflow and return response"""
		pass

	@abstractmethod
	async def execute_streaming(self, context: Dict[str, Any], api_key: str = None) -> AsyncGenerator[Dict[str, Any], None]:
		"""Execute workflow with streaming response"""
		pass

	def prepare_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
		"""Prepare and enhance context for workflow execution"""
		enhanced_context = context.copy()
		enhanced_context['workflow_type'] = self.workflow_type
		enhanced_context['config'] = self.config.dict() if hasattr(self.config, 'dict') else vars(self.config)
		return enhanced_context

	def validate_context(self, context: Dict[str, Any]) -> bool:
		"""Validate context for workflow execution"""
		required_fields = ['user_message', 'agent', 'config']
		return all(field in context for field in required_fields)

	def get_capabilities(self) -> Dict[str, Any]:
		"""Get workflow capabilities"""
		return {'streaming': True, 'memory': True, 'tools': [], 'features': []}
