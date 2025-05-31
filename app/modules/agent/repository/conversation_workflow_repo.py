from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db
from app.modules.agent.repository.system_agent_repo import SystemAgentRepo
from app.modules.agent.services.langgraph_service import LangGraphService
from app.exceptions.exception import ValidationException
from app.middleware.translation_manager import _
from typing import Dict, Any, List, AsyncGenerator
import logging

logger = logging.getLogger(__name__)


class ConversationWorkflowRepo:
	"""Repository for conversation-based workflow execution using single agent"""

	def __init__(self, db: Session = Depends(get_db)):
		self.db = db
		self.system_agent_repo = SystemAgentRepo(db)
		self.langgraph_service = LangGraphService(db)

	async def execute_chat_workflow(
		self,
		conversation_id: str,
		user_message: str,
		conversation_system_prompt: str = None,
		conversation_history: List[Dict[str, Any]] = None,
	) -> Dict[str, Any]:
		"""Execute chat workflow for conversation using system agent"""
		logger.info(f'execute_chat_workflow - Starting for conversation: {conversation_id}')

		try:
			# Get system agent with embedded config and API key
			agent = self.system_agent_repo.get_system_agent()

			# Execute workflow using agent directly
			result = await self.langgraph_service.execute_conversation_workflow(
				agent=agent,
				conversation_id=conversation_id,
				user_message=user_message,
				conversation_system_prompt=conversation_system_prompt,
				conversation_history=conversation_history or [],
			)

			logger.info('Chat workflow executed successfully')
			return result

		except Exception as e:
			logger.info(f'ERROR execute_chat_workflow - Error: {str(e)}')
			raise ValidationException(f'{_("chat_execution_failed")}: {str(e)}')

	async def execute_streaming_chat_workflow(
		self,
		conversation_id: str,
		user_message: str,
		conversation_system_prompt: str = None,
		conversation_history: List[Dict[str, Any]] = None,
	) -> AsyncGenerator[Dict[str, Any], None]:
		"""Execute streaming chat workflow for conversation using system agent"""
		logger.info(f'execute_streaming_chat_workflow - Starting for conversation: {conversation_id}')

		try:
			# Get system agent with embedded config and API key
			agent = self.system_agent_repo.get_system_agent()

			# Execute streaming workflow using agent directly
			async for chunk in self.langgraph_service.execute_streaming_conversation_workflow(
				agent=agent,
				conversation_id=conversation_id,
				user_message=user_message,
				conversation_system_prompt=conversation_system_prompt,
				conversation_history=conversation_history or [],
			):
				yield chunk

		except Exception as e:
			logger.info(f'ERROR execute_streaming_chat_workflow - Error: {str(e)}')
			yield {
				'type': 'error',
				'message': f'{_("chat_execution_failed")}: {str(e)}',
			}
