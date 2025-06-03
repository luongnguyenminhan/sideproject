from pytz import timezone
from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db
from app.modules.chat.dal.conversation_dal import ConversationDAL
from app.modules.chat.dal.message_dal import MessageDAL
from app.modules.chat.schemas.conversation_request import ConversationListRequest
from app.exceptions.exception import NotFoundException
from app.middleware.translation_manager import _
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConversationRepo:
	def __init__(self, db: Session = Depends(get_db)):
		logger.info(f'\033[96m[ConversationRepo.__init__] Initializing ConversationRepo with db session: {db}\033[0m')
		self.db = db
		self.conversation_dal = ConversationDAL(db)
		self.message_dal = MessageDAL(db)
		logger.info(f'\033[92m[ConversationRepo.__init__] ConversationRepo initialized successfully\033[0m')

	def get_user_conversations(self, user_id: str, request: ConversationListRequest):
		"""Get user's conversations with pagination and filtering"""
		logger.info(f'\033[93m[ConversationRepo.get_user_conversations] Getting conversations for user: {user_id}, page: {request.page}, page_size: {request.page_size}, search: {request.search}, order_by: {request.order_by}, order_direction: {request.order_direction}\033[0m')
		conversations = self.conversation_dal.get_user_conversations(
			user_id=user_id,
			page=request.page,
			page_size=request.page_size,
			search=request.search,
			order_by=request.order_by,
			order_direction=request.order_direction,
		)
		logger.info(f'\033[92m[ConversationRepo.get_user_conversations] Found {len(conversations.items) if hasattr(conversations, "items") else len(conversations)} conversations\033[0m')
		return conversations

	def get_conversation_by_id(self, conversation_id: str, user_id: str):
		"""Get conversation by ID and verify user access"""
		logger.info(f'\033[93m[ConversationRepo.get_conversation_by_id] Getting conversation: {conversation_id} for user: {user_id}\033[0m')
		conversation = self.conversation_dal.get_user_conversation_by_id(conversation_id, user_id)
		if not conversation:
			logger.info(f'\033[91m[ConversationRepo.get_conversation_by_id] Conversation not found: {conversation_id}\033[0m')
			raise NotFoundException(_('conversation_not_found'))
		logger.info(f'\033[92m[ConversationRepo.get_conversation_by_id] Conversation found: {conversation.name}, message_count: {conversation.message_count}\033[0m')
		return conversation

	def create_conversation(
		self,
		user_id: str,
		name: str,
		initial_message: str = None,
		system_prompt: str = None,
	):
		"""Create a new conversation"""
		logger.info(f'\033[93m[ConversationRepo.create_conversation] Creating conversation for user: {user_id}, name: {name}, has_initial_message: {initial_message is not None}, has_system_prompt: {system_prompt is not None}\033[0m')
		conversation_data = {
			'name': name,
			'user_id': user_id,
			'message_count': 0,
			'last_activity': datetime.now(timezone('Asia/Ho_Chi_Minh')).isoformat(),
			'system_prompt': system_prompt,
		}
		logger.info(f'\033[96m[ConversationRepo.create_conversation] Created conversation_data: {conversation_data}\033[0m')

		with self.conversation_dal.transaction():
			logger.info(f'\033[94m[ConversationRepo.create_conversation] Creating conversation in database\033[0m')
			conversation = self.conversation_dal.create(conversation_data)
			logger.info(f'\033[92m[ConversationRepo.create_conversation] Conversation created with ID: {conversation.id}\033[0m')

			# If initial message provided, create it
			if initial_message:
				logger.info(f'\033[94m[ConversationRepo.create_conversation] Initial message provided, would be handled by chat system\033[0m')

			return conversation

	def update_conversation(
		self,
		conversation_id: str,
		user_id: str,
		name: str = None,
		system_prompt: str = None,
	):
		"""Update conversation details"""
		logger.info(f'\033[93m[ConversationRepo.update_conversation] Updating conversation: {conversation_id} for user: {user_id}, new_name: {name}, new_system_prompt: {system_prompt is not None}\033[0m')
		conversation = self.get_conversation_by_id(conversation_id, user_id)
		logger.info(f'\033[94m[ConversationRepo.update_conversation] Current conversation name: {conversation.name}\033[0m')

		update_data = {}
		if name:
			update_data['name'] = name
			logger.info(f'\033[94m[ConversationRepo.update_conversation] Will update name to: {name}\033[0m')
		if system_prompt is not None:  # Allow empty string to clear system prompt
			update_data['system_prompt'] = system_prompt
			logger.info(f'\033[94m[ConversationRepo.update_conversation] Will update system prompt\033[0m')

		if update_data:
			logger.info(f'\033[96m[ConversationRepo.update_conversation] Update data: {update_data}\033[0m')
			with self.conversation_dal.transaction():
				logger.info(f'\033[94m[ConversationRepo.update_conversation] Updating conversation in database\033[0m')
				updated_conversation = self.conversation_dal.update(conversation_id, update_data)
				logger.info(f'\033[92m[ConversationRepo.update_conversation] Conversation updated successfully\033[0m')
				return updated_conversation

		logger.info(f'\033[95m[ConversationRepo.update_conversation] No updates needed, returning original conversation\033[0m')
		return conversation

	def delete_conversation(self, conversation_id: str, user_id: str):
		"""Delete a conversation and its messages"""
		logger.info(f'\033[93m[ConversationRepo.delete_conversation] Deleting conversation: {conversation_id} for user: {user_id}\033[0m')
		conversation = self.get_conversation_by_id(conversation_id, user_id)
		logger.info(f'\033[94m[ConversationRepo.delete_conversation] Conversation found: {conversation.name}, message_count: {conversation.message_count}\033[0m')

		with self.conversation_dal.transaction():
			# Soft delete related messages in MySQL first
			logger.info(f'\033[94m[ConversationRepo.delete_conversation] Soft deleting related messages in MySQL\033[0m')
			self.message_dal.soft_delete_by_conversation(conversation_id)
			logger.info(f'\033[92m[ConversationRepo.delete_conversation] Messages soft deleted in MySQL\033[0m')

			# Soft delete conversation in MySQL
			logger.info(f'\033[94m[ConversationRepo.delete_conversation] Performing soft delete in MySQL\033[0m')
			update_data = {
				'is_deleted': True,
				'update_date': datetime.now(timezone('Asia/Ho_Chi_Minh')).isoformat(),
			}
			self.conversation_dal.update(conversation_id, update_data)
			logger.info(f'\033[92m[ConversationRepo.delete_conversation] Conversation soft deleted in MySQL\033[0m')

		logger.info(f'\033[92m[ConversationRepo.delete_conversation] Conversation deletion completed\033[0m')

	def get_conversation_messages(
		self,
		conversation_id: str,
		page: int = 1,
		page_size: int = 50,
		before_message_id: str = None,
	):
		"""Get messages for a conversation with pagination"""
		logger.info(f'\033[93m[ConversationRepo.get_conversation_messages] Getting messages for conversation: {conversation_id}, page: {page}, page_size: {page_size}, before_message_id: {before_message_id}\033[0m')
		messages = self.message_dal.get_conversation_messages(
			conversation_id=conversation_id,
			page=page,
			page_size=page_size,
			before_message_id=before_message_id,
		)
		logger.info(f'\033[92m[ConversationRepo.get_conversation_messages] Found {len(messages.items) if hasattr(messages, "items") else len(messages)} messages\033[0m')
		return messages
