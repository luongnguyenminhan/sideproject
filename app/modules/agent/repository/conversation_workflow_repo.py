from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db
from app.modules.agent.repository.system_agent_repo import SystemAgentRepo
from app.modules.agent.services.langgraph_service import LangGraphService
from app.exceptions.exception import ValidationException
from app.middleware.translation_manager import _
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ConversationWorkflowRepo:
	"""Optimized repository for conversation workflow execution"""

	# Class-level service caching
	_langgraph_service = None
	_system_agent_repo = None

	def __init__(self, db: Session = Depends(get_db)):
		self.db = db
		# Use cached services
		if ConversationWorkflowRepo._system_agent_repo is None:
			ConversationWorkflowRepo._system_agent_repo = SystemAgentRepo(db)
		if ConversationWorkflowRepo._langgraph_service is None:
			ConversationWorkflowRepo._langgraph_service = LangGraphService(db)

	async def execute_chat_workflow(
		self,
		conversation_id: str,
		user_message: str,
		conversation_system_prompt: str = None,
		conversation_history: List[Dict[str, Any]] = None,
	) -> Dict[str, Any]:
		"""Execute optimized chat workflow using cached services"""
		logger.info(f'execute_chat_workflow - Starting for conversation: {conversation_id}')

		try:
			# Get system agent using cached repo
			agent = ConversationWorkflowRepo._system_agent_repo.get_system_agent()

			# Execute workflow using cached service with global workflow
			result = await ConversationWorkflowRepo._langgraph_service.execute_conversation(
				agent=agent,
				conversation_id=conversation_id,
				user_message=user_message,
				conversation_system_prompt=conversation_system_prompt,
				conversation_history=conversation_history or [],
			)

			logger.info('Chat workflow executed successfully')
			return result

		except Exception as e:
			logger.error(f'ERROR execute_chat_workflow - Error: {str(e)}')
			raise ValidationException(f'{_("chat_execution_failed")}: {str(e)}')

	@classmethod
	def reset_cache(cls):
		"""Reset service cache - useful for testing"""
		cls._langgraph_service = None
		cls._system_agent_repo = None
		logger.info('ConversationWorkflowRepo cache reset')
