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
		authorization_token: str = None,
	) -> Dict[str, Any]:
		"""Execute optimized chat workflow using cached services"""
		logger.info(f'execute_chat_workflow - Starting for conversation: {conversation_id}')

		try:
			# Get system agent using cached repo
			agent = ConversationWorkflowRepo._system_agent_repo.get_system_agent()

			# 🔥 COMBINE BOTH SYSTEM PROMPTS
			combined_system_prompt = self._combine_system_prompts(
				agent_prompt=agent.default_system_prompt,
				conversation_prompt=conversation_system_prompt,
			)

			# Execute workflow using cached service with combined prompt
			result = await ConversationWorkflowRepo._langgraph_service.execute_conversation(
				agent=agent,
				conversation_id=conversation_id,
				user_message=user_message,
				conversation_system_prompt=combined_system_prompt,
				conversation_history=conversation_history or [],
				authorization_token=authorization_token,
			)

			logger.info('Chat workflow executed successfully')
			return result

		except Exception as e:
			logger.error(f'ERROR execute_chat_workflow - Error: {str(e)}')
			raise ValidationException(f'{_("chat_execution_failed")}: {str(e)}')

	def _combine_system_prompts(self, agent_prompt: str = None, conversation_prompt: str = None) -> str:
		"""Combine agent system prompt with conversation system prompt"""
		prompts = []

		# Add agent's default system prompt (base behavior)
		if agent_prompt and agent_prompt.strip():
			prompts.append(f'# Agent System Prompt:\n{agent_prompt.strip()}')

		# Add conversation-specific prompt (override/additional instructions)
		if conversation_prompt and conversation_prompt.strip():
			prompts.append(f'# Conversation Specific Instructions:\n{conversation_prompt.strip()}')

		# Combine with clear separation
		if prompts:
			combined = '\n\n'.join(prompts)
			logger.info(f'Combined system prompts - Agent: {bool(agent_prompt)}, Conversation: {bool(conversation_prompt)}')
			return combined

		# Fallback to default
		return 'You are a helpful AI assistant for financial questions.'

	@classmethod
	def reset_cache(cls):
		"""Reset service cache - useful for testing"""
		cls._langgraph_service = None
		cls._system_agent_repo = None
		logger.info('ConversationWorkflowRepo cache reset')
