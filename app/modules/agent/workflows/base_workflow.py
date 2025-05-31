"""
Base workflow class for conversation processing.
Note: This module is simplified - most workflow logic is now handled
in the LangGraphService for conversation-based processing.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator


class BaseWorkflow(ABC):
	"""Base class for simplified conversation workflows"""

	def __init__(self, config: Dict[str, Any]):
		self.config = config

	@abstractmethod
	async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
		"""Execute workflow synchronously"""
		pass

	@abstractmethod
	async def execute_streaming(self, context: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
		"""Execute workflow with streaming response"""
		pass
