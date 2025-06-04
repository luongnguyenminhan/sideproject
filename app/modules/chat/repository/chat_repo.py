import os
from pytz import timezone
from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db
from app.modules.agent.dal.agent_dal import AgentDAL
from app.modules.chat.dal.conversation_dal import ConversationDAL
from app.modules.chat.dal.message_dal import MessageDAL
from app.modules.agent.repository.conversation_workflow_repo import (
	ConversationWorkflowRepo,
)
from app.exceptions.exception import NotFoundException, ValidationException
from app.middleware.translation_manager import _
from datetime import datetime
import time
import asyncio
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ChatRepo:
	def __init__(self, db: Session = Depends(get_db)):
		logger.info(f'\033[96m[ChatRepo.__init__] Initializing ChatRepo with db session: {db}\033[0m')
		self.db = db
		self.conversation_dal = ConversationDAL(db)
		self.message_dal = MessageDAL(db)
		self.agent_dal = AgentDAL(db)
		self.conversation_workflow_repo = ConversationWorkflowRepo(db)
		logger.info(f'\033[92m[ChatRepo.__init__] ChatRepo initialized successfully\033[0m')

	def get_conversation_by_id(self, conversation_id: str, user_id: str):
		"""Get conversation by ID and verify user access"""
		logger.info(f'\033[93m[ChatRepo.get_conversation_by_id] Getting conversation: {conversation_id} for user: {user_id}\033[0m')
		conversation = self.conversation_dal.get_user_conversation_by_id(conversation_id, user_id)
		if not conversation:
			logger.info(f'\033[91m[ChatRepo.get_conversation_by_id] Conversation not found: {conversation_id}\033[0m')
			raise NotFoundException(_('conversation_not_found'))
		logger.info(f'\033[92m[ChatRepo.get_conversation_by_id] Conversation found: {conversation.name}\033[0m')
		return conversation

	def get_conversation_history(self, conversation_id: str, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
		"""Get conversation message history for context"""
		logger.info(f'\033[93m[ChatRepo.get_conversation_history] Getting history for conversation: {conversation_id}, limit: {limit}\033[0m')

		# Verify conversation access
		conversation = self.get_conversation_by_id(conversation_id, user_id)

		# Get messages from database using conversation_history method for better performance
		messages = self.message_dal.get_conversation_history(conversation_id, limit=limit)

		# Format messages for agent context (reverse to chronological order)
		history = []
		for message in reversed(messages):  # Messages come in desc order, reverse for chronological
			history.append({
				'role': message.role,
				'content': message.content,
				'timestamp': (message.timestamp.isoformat() if message.timestamp else None),
				'model_used': message.model_used,
			})

		logger.info(f'\033[92m[ChatRepo.get_conversation_history] Retrieved {len(history)} messages\033[0m')
		return history

	def create_message(
		self,
		conversation_id: str,
		user_id: str,
		content: str,
		role: str,
		model_used: str = None,
		tokens_used: str = None,
		response_time_ms: str = None,
	):
		"""Create a new message in the conversation"""
		logger.info(f'\033[93m[ChatRepo.create_message] Creating message in conversation: {conversation_id}, user: {user_id}, role: {role}, content_length: {len(content)}, model: {model_used}, tokens: {tokens_used}, response_time: {response_time_ms}ms\033[0m')
		# Verify conversation exists and user has access
		conversation = self.get_conversation_by_id(conversation_id, user_id)
		logger.info(f'\033[94m[ChatRepo.create_message] Conversation verified: {conversation.name}\033[0m')

		message_timestamp = datetime.now(timezone('Asia/Ho_Chi_Minh'))
		logger.info(f'\033[96m[ChatRepo.create_message] Message timestamp: {message_timestamp}\033[0m')

		# Create message in MySQL only
		message_data = {
			'conversation_id': conversation_id,
			'user_id': user_id,
			'role': role,
			'content': content,
			'timestamp': message_timestamp,
			'model_used': model_used,
			'tokens_used': tokens_used,
			'response_time_ms': response_time_ms,
		}
		logger.info(f'\033[96m[ChatRepo.create_message] Created message_data for MySQL\033[0m')

		with self.message_dal.transaction():
			logger.info(f'\033[94m[ChatRepo.create_message] Creating message in MySQL\033[0m')
			message = self.message_dal.create(message_data)
			logger.info(f'\033[92m[ChatRepo.create_message] Message created in MySQL with ID: {message.id}\033[0m')

			# Update conversation activity and message count
			logger.info(f'\033[94m[ChatRepo.create_message] Updating conversation activity and message count\033[0m')
			conversation.last_activity = message_timestamp
			conversation.message_count += 1
			logger.info(f'\033[96m[ChatRepo.create_message] New message count: {conversation.message_count}\033[0m')
			self.conversation_dal.update(
				conversation.id,
				{
					'last_activity': conversation.last_activity,
					'message_count': conversation.message_count,
				},
			)
			logger.info(f'\033[92m[ChatRepo.create_message] Conversation updated successfully\033[0m')

			return message

	async def get_ai_response(
		self,
		conversation_id: str,
		user_message: str,
		api_key: str = None,
		user_id: str = None,
	) -> dict:
		"""Get AI response for a message using Agent system (non-streaming)"""
		logger.info(f'\033[93m[ChatRepo.get_ai_response] Getting AI response via Agent system for conversation: {conversation_id}, user: {user_id}, message_length: {len(user_message)}, has_api_key: {api_key is not None}\033[0m')
		# Get user_id from conversation if not provided
		if not user_id:
			conversation = self.get_conversation_by_id(conversation_id, '')
			user_id = conversation.user_id
			logger.info(f'\033[94m[ChatRepo.get_ai_response] Retrieved user_id from conversation: {user_id}\033[0m')

		# Validate API key is provided
		if not api_key:
			logger.info(f'\033[93m[ChatRepo.get_ai_response] No API key provided, checking agent settings\033[0m')
			api_key = self.agent_dal.get_agent_api_key(user_id)
			logger.info(f'\033[94m[ChatRepo.get_ai_response] Retrieved API key from agent: {api_key}\033[0m')
			if not api_key:
				logger.error(f'\033[91m[ChatRepo.get_ai_response] No API key provided\033[0m')
				# Optionally, you can get the user's default API key if available
				api_key = os.getenv('GOOGLE_API_KEY')
				logger.info(f'\033[94m[ChatRepo.get_ai_response] Using default API key: {api_key}\033[0m')
			else:
				logger.info(f'\033[94m[ChatRepo.get_ai_response] Using API key from agent: {api_key}\033[0m')
				pass

		try:
			# Get conversation history for context
			conversation_history = self.get_conversation_history(conversation_id, user_id)
			logger.info(f'\033[94m[ChatRepo.get_ai_response] Retrieved {len(conversation_history)} messages for context\033[0m')

			# Get conversation for system prompt
			conversation = self.get_conversation_by_id(conversation_id, user_id)
			conversation_system_prompt = getattr(conversation, 'system_prompt', None)

			# Call agent workflow system
			logger.info(f'\033[94m[ChatRepo.get_ai_response] Calling ConversationWorkflowRepo for AI response\033[0m')
			result = await self.conversation_workflow_repo.execute_chat_workflow(
				conversation_id=conversation_id,
				user_message=user_message,
				conversation_system_prompt=conversation_system_prompt,
				conversation_history=conversation_history,
			)

			logger.info(f'\033[92m[ChatRepo.get_ai_response] AI response completed: {result}ms\033[0m')
			return result

		except Exception as e:
			logger.error(f'\033[91m[ChatRepo.get_ai_response] Error getting AI response from agent system: {e}\033[0m')
			logger.info(f'\033[93m[ChatRepo.get_ai_response] Falling back to simulation\033[0m')

			# Fallback to simulation if agent system fails
			try:
				result = await self._simulate_ai_response_fallback(user_message, api_key)
				logger.info(f'\033[92m[ChatRepo.get_ai_response] Fallback response completed\033[0m')
				return result
			except Exception as fallback_error:
				logger.error(f'\033[91m[ChatRepo.get_ai_response] Fallback also failed: {fallback_error}\033[0m')
				raise ValidationException(_('ai_response_failed'))

	async def get_ai_response_streaming(
		self,
		conversation_id: str,
		user_message: str,
		api_key: str = None,
		websocket_manager=None,
		user_id: str = None,
	) -> dict:
		"""Get AI response using Agent system with streaming support"""
		logger.info(f'\033[93m[ChatRepo.get_ai_response_streaming] Getting streaming AI response via Agent system for conversation: {conversation_id}, user: {user_id}, message_length: {len(user_message)}, has_websocket: {websocket_manager is not None}\033[0m')

		# Get user_id from conversation if not provided
		if not user_id:
			conversation = self.get_conversation_by_id(conversation_id, '')  # Fix: use empty string for user_id check
			user_id = conversation.user_id
			logger.info(f'\033[94m[ChatRepo.get_ai_response_streaming] Retrieved user_id from conversation: {user_id}\033[0m')

		# Get user's API key if not provided
		if not api_key:
			logger.error(f'\033[91m[ChatRepo.get_ai_response_streaming] No API key provided\033[0m')
			# Use environment variable as fallback
			api_key = os.getenv('GOOGLE_API_KEY')
			logger.info(f'\033[94m[ChatRepo.get_ai_response_streaming] Using default API key from environment\033[0m')

		try:
			# Get conversation history for context
			conversation_history = self.get_conversation_history(conversation_id, user_id)
			logger.info(f'\033[94m[ChatRepo.get_ai_response_streaming] Retrieved {len(conversation_history)} messages for context\033[0m')

			# Get conversation for system prompt
			conversation = self.get_conversation_by_id(conversation_id, user_id)
			conversation_system_prompt = getattr(conversation, 'system_prompt', None)

			# Call agent workflow system for streaming
			logger.info(f'\033[94m[ChatRepo.get_ai_response_streaming] Calling ConversationWorkflowRepo for streaming AI response\033[0m')

			# Collect streaming response
			result_content = ''
			result_data = {}

			async for chunk in self.conversation_workflow_repo.execute_streaming_chat_workflow(
				conversation_id=conversation_id,
				user_message=user_message,
				conversation_system_prompt=conversation_system_prompt,
				conversation_history=conversation_history,
			):
				if chunk.get('type') == 'content':
					result_content += chunk.get('content', '')

					# Send websocket update if available
					if websocket_manager and user_id:
						await websocket_manager.send_message(
							user_id,
							{
								'type': 'assistant_message_chunk',
								'chunk': chunk.get('content', ''),
								'is_final': False,
							},
						)
				elif chunk.get('type') == 'final':
					result_data = chunk

					# Send final websocket update
					if websocket_manager and user_id:
						await websocket_manager.send_message(
							user_id,
							{
								'type': 'assistant_message_chunk',
								'chunk': '',
								'is_final': True,
							},
						)

			# Prepare final result
			final_result = {
				'content': result_content,
				'model_used': result_data.get('model_used', 'agent-workflow'),
				'usage': result_data.get('usage', {}),
				'response_time_ms': result_data.get('response_time_ms', 0),
				'agent_name': result_data.get('agent_name', 'conversation-workflow'),
			}

			logger.info(f'\033[92m[ChatRepo.get_ai_response_streaming] Agent streaming response completed, agent: {final_result.get("agent_name", "unknown")}, response_time: {final_result.get("response_time_ms", 0)}ms\033[0m')
			return final_result

		except Exception as e:
			logger.info(f'\033[91m[ChatRepo.get_ai_response_streaming] Error getting Agent streaming response: {e}\033[0m')
			logger.error(f'Error getting Agent streaming response: {e}')

			# Fallback to simulation if agent system fails
			logger.info(f'\033[93m[ChatRepo.get_ai_response_streaming] Falling back to streaming simulation\033[0m')
			return await self._simulate_streaming_ai_response_fallback(user_message, api_key, websocket_manager, user_id)

	async def _simulate_ai_response_fallback(self, message: str, api_key: str) -> dict:
		"""
		Fallback AI response simulation when agent system fails
		"""
		logger.info(f'\033[93m[ChatRepo._simulate_ai_response_fallback] Running fallback simulation for message_length: {len(message)}\033[0m')
		start_time = time.time()

		# Simulate processing delay
		await asyncio.sleep(0.5)

		# Simple fallback response
		response_content = f"[Fallback Mode] I received your message: '{message}'. The AI agent system is temporarily unavailable, but I'm here to help! "

		if 'hello' in message.lower():
			response_content += 'Hello! How can I help you today?'
		elif 'how are you' in message.lower():
			response_content += "I'm doing well, thank you for asking!"
		else:
			response_content += 'Please try again in a moment when the full AI system is restored.'

		response_time = int((time.time() - start_time) * 1000)

		return {
			'content': response_content,
			'model_used': 'fallback-simulation',
			'usage': {
				'prompt_tokens': len(message.split()),
				'completion_tokens': len(response_content.split()),
				'total_tokens': len(message.split()) + len(response_content.split()),
			},
			'response_time_ms': response_time,
		}

	async def _simulate_streaming_ai_response_fallback(
		self,
		message: str,
		api_key: str,
		websocket_manager=None,
		user_id: str = None,
	) -> dict:
		"""
		Fallback streaming AI response simulation when agent system fails
		"""
		logger.info(f'\033[93m[ChatRepo._simulate_streaming_ai_response_fallback] Running fallback streaming simulation for user: {user_id}\033[0m')
		start_time = time.time()

		# Get the full response first
		full_response = await self._simulate_ai_response_fallback(message, api_key)
		response_text = full_response['content']

		if websocket_manager and user_id:
			logger.info(f'\033[94m[ChatRepo._simulate_streaming_ai_response_fallback] Starting fallback streaming\033[0m')
			# Simulate streaming by sending chunks
			words = response_text.split()

			for i, word in enumerate(words):
				chunk = word + ' '

				# Send chunk every word for fallback (faster)
				if i % 2 == 0 or i == len(words) - 1:
					await websocket_manager.send_message(
						user_id,
						{
							'type': 'assistant_message_chunk',
							'chunk': chunk.strip(),
							'is_final': i == len(words) - 1,
							'fallback_mode': True,
						},
					)
					await asyncio.sleep(0.05)  # Faster for fallback

		response_time = int((time.time() - start_time) * 1000)
		full_response['response_time_ms'] = response_time
		return full_response
