from pytz import timezone
from app.modules.agent.services.agent_integration_service import AgentIntegrationService
from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db
from app.modules.chat.dal.conversation_dal import ConversationDAL
from app.modules.chat.dal.message_dal import MessageDAL
from app.modules.chat.dal.api_key_dal import ApiKeyDAL
from app.exceptions.exception import NotFoundException, ValidationException
from app.middleware.translation_manager import _
from datetime import datetime
import time
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class ChatRepo:
	def __init__(self, db: Session = Depends(get_db)):
		print(f'\033[96m[ChatRepo.__init__] Initializing ChatRepo with db session: {db}\033[0m')
		self.db = db
		self.conversation_dal = ConversationDAL(db)
		self.message_dal = MessageDAL(db)
		self.api_key_dal = ApiKeyDAL(db)
		self.agent_integration = AgentIntegrationService(db)
		print(f'\033[92m[ChatRepo.__init__] ChatRepo initialized successfully with Agent Integration\033[0m')

	def get_conversation_by_id(self, conversation_id: str, user_id: str):
		"""Get conversation by ID and verify user access"""
		print(f'\033[93m[ChatRepo.get_conversation_by_id] Getting conversation: {conversation_id} for user: {user_id}\033[0m')
		conversation = self.conversation_dal.get_user_conversation_by_id(conversation_id, user_id)
		if not conversation:
			print(f'\033[91m[ChatRepo.get_conversation_by_id] Conversation not found: {conversation_id}\033[0m')
			raise NotFoundException(_('conversation_not_found'))
		print(f'\033[92m[ChatRepo.get_conversation_by_id] Conversation found: {conversation.name}\033[0m')
		return conversation

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
		print(
			f'\033[93m[ChatRepo.create_message] Creating message in conversation: {conversation_id}, user: {user_id}, role: {role}, content_length: {len(content)}, model: {model_used}, tokens: {tokens_used}, response_time: {response_time_ms}ms\033[0m'
		)
		# Verify conversation exists and user has access
		conversation = self.get_conversation_by_id(conversation_id, user_id)
		print(f'\033[94m[ChatRepo.create_message] Conversation verified: {conversation.name}\033[0m')

		message_timestamp = datetime.now(timezone('Asia/Ho_Chi_Minh')).isoformat()
		print(f'\033[96m[ChatRepo.create_message] Message timestamp: {message_timestamp}\033[0m')

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
		print(f'\033[96m[ChatRepo.create_message] Created message_data for MySQL\033[0m')

		with self.message_dal.transaction():
			print(f'\033[94m[ChatRepo.create_message] Creating message in MySQL\033[0m')
			message = self.message_dal.create(message_data)
			print(f'\033[92m[ChatRepo.create_message] Message created in MySQL with ID: {message.id}\033[0m')

			# Update conversation activity and message count
			print(f'\033[94m[ChatRepo.create_message] Updating conversation activity and message count\033[0m')
			conversation.last_activity = message_timestamp
			conversation.message_count += 1
			print(f'\033[96m[ChatRepo.create_message] New message count: {conversation.message_count}\033[0m')
			self.conversation_dal.update(
				conversation.id,
				{
					'last_activity': conversation.last_activity,
					'message_count': conversation.message_count,
				},
			)
			print(f'\033[92m[ChatRepo.create_message] Conversation updated successfully\033[0m')

			return message

	async def get_ai_response(self, conversation_id: str, user_message: str, api_key: str = None, user_id: str = None) -> dict:
		"""Get AI response for a message using Agent system (non-streaming)"""
		print(
			f'\033[93m[ChatRepo.get_ai_response] Getting AI response via Agent system for conversation: {conversation_id}, user: {user_id}, message_length: {len(user_message)}, has_api_key: {api_key is not None}\033[0m'
		)

		# Get user_id from conversation if not provided
		if not user_id:
			conversation = self.get_conversation_by_id(conversation_id, '')
			user_id = conversation.user_id
			print(f'\033[94m[ChatRepo.get_ai_response] Retrieved user_id from conversation: {user_id}\033[0m')

		# Get user's API key if not provided
		if not api_key:
			print(f"\033[94m[ChatRepo.get_ai_response] No API key provided, getting user's default key\033[0m")
			default_key = self.api_key_dal.get_user_default_api_key(user_id=user_id, provider='google')
			if default_key:
				api_key = default_key.get_api_key()
				print(f'\033[92m[ChatRepo.get_ai_response] Found default API key for GOOGLE\033[0m')

		try:
			print(f'\033[94m[ChatRepo.get_ai_response] Calling Agent Integration Service\033[0m')
			print(f'\033[96m[ChatRepo.get_ai_response] Using API key: {api_key}... (truncated for security)\033[0m')
			result = await self.agent_integration.get_ai_response(conversation_id=conversation_id, user_message=user_message, user_id=user_id, api_key=api_key)
			print(f'\033[92m[ChatRepo.get_ai_response] Agent response received, agent: {result.get("agent_name", "unknown")}, response_time: {result.get("response_time_ms", 0)}ms\033[0m')
			return result

		except Exception as e:
			print(f'\033[91m[ChatRepo.get_ai_response] Error getting Agent response: {e}\033[0m')
			logger.error(f'Error getting Agent response: {e}')

			# Fallback to simulation if agent system fails
			print(f'\033[93m[ChatRepo.get_ai_response] Falling back to simulation\033[0m')
			return await self._simulate_ai_response_fallback(user_message, api_key)

	async def get_ai_response_streaming(
		self,
		conversation_id: str,
		user_message: str,
		api_key: str = None,
		websocket_manager=None,
		user_id: str = None,
	) -> dict:
		"""Get AI response using Agent system with streaming support"""
		print(
			f'\033[93m[ChatRepo.get_ai_response_streaming] Getting streaming AI response via Agent system for conversation: {conversation_id}, user: {user_id}, message_length: {len(user_message)}, has_websocket: {websocket_manager is not None}\033[0m'
		)

		# Get user_id from conversation if not provided
		if not user_id:
			conversation = self.get_conversation_by_id(conversation_id, user_id)
			user_id = conversation.user_id
			print(f'\033[94m[ChatRepo.get_ai_response_streaming] Retrieved user_id from conversation: {user_id}\033[0m')

		# Get user's API key if not provided
		if not api_key:
			print(f"\033[94m[ChatRepo.get_ai_response_streaming] No API key provided, getting user's default key\033[0m")
			default_key = self.api_key_dal.get_user_default_api_key(user_id=user_id, provider='google')
			if default_key:
				api_key = default_key.get_api_key()
				print(f'\033[92m[ChatRepo.get_ai_response_streaming] Found default API key for Google\033[0m')

		try:
			print(f'\033[94m[ChatRepo.get_ai_response_streaming] Calling Agent Integration Service for streaming\033[0m')
			result = await self.agent_integration.get_ai_response_streaming(
				conversation_id=conversation_id, user_message=user_message, user_id=user_id, api_key=api_key, websocket_manager=websocket_manager
			)
			print(
				f'\033[92m[ChatRepo.get_ai_response_streaming] Agent streaming response completed, agent: {result.get("agent_name", "unknown")}, response_time: {result.get("response_time_ms", 0)}ms\033[0m'
			)
			return result

		except Exception as e:
			print(f'\033[91m[ChatRepo.get_ai_response_streaming] Error getting Agent streaming response: {e}\033[0m')
			logger.error(f'Error getting Agent streaming response: {e}')

			# Fallback to simulation if agent system fails
			print(f'\033[93m[ChatRepo.get_ai_response_streaming] Falling back to streaming simulation\033[0m')
			return await self._simulate_streaming_ai_response_fallback(user_message, api_key, websocket_manager, user_id)

	async def _simulate_ai_response_fallback(self, message: str, api_key: str) -> dict:
		"""
		Fallback AI response simulation when agent system fails
		"""
		print(f'\033[93m[ChatRepo._simulate_ai_response_fallback] Running fallback simulation for message_length: {len(message)}\033[0m')
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
		print(f'\033[93m[ChatRepo._simulate_streaming_ai_response_fallback] Running fallback streaming simulation for user: {user_id}\033[0m')
		start_time = time.time()

		# Get the full response first
		full_response = await self._simulate_ai_response_fallback(message, api_key)
		response_text = full_response['content']

		if websocket_manager and user_id:
			print(f'\033[94m[ChatRepo._simulate_streaming_ai_response_fallback] Starting fallback streaming\033[0m')
			# Simulate streaming by sending chunks
			words = response_text.split()

			for i, word in enumerate(words):
				chunk = word + ' '

				# Send chunk every word for fallback (faster)
				if i % 2 == 0 or i == len(words) - 1:
					await websocket_manager.send_message(
						user_id,
						{'type': 'assistant_message_chunk', 'chunk': chunk.strip(), 'is_final': i == len(words) - 1, 'fallback_mode': True},
					)
					await asyncio.sleep(0.05)  # Faster for fallback

		response_time = int((time.time() - start_time) * 1000)
		full_response['response_time_ms'] = response_time
		return full_response
