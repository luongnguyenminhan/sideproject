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


class ConversationRepo:
	def __init__(self, db: Session = Depends(get_db)):
		self.db = db
		self.conversation_dal = ConversationDAL(db)
		self.message_dal = MessageDAL(db)

	def get_user_conversations(self, user_id: str, request: ConversationListRequest):
		"""Get user's conversations with pagination and filtering"""
		print(
			f'\033[93m[ConversationRepo.get_user_conversations] Getting conversations for user: {user_id}, page: {request.page}, page_size: {request.page_size}, search: {request.search}, order_by: {request.order_by}, order_direction: {request.order_direction}\033[0m'
		)
		conversations = self.conversation_dal.get_user_conversations(
			user_id=user_id,
			page=request.page,
			page_size=request.page_size,
			search=request.search,
			order_by=request.order_by,
			order_direction=request.order_direction,
		)
		return conversations

	def get_conversation_by_id(self, conversation_id: str, user_id: str):
		"""Get conversation by ID and verify user access"""
		conversation = self.conversation_dal.get_user_conversation_by_id(conversation_id, user_id)
		if not conversation:
			raise NotFoundException(_('conversation_not_found'))
		return conversation

	def create_conversation(self, user_id: str, name: str, initial_message: str = None):
		"""Create a new conversation"""
		conversation_data = {
			'name': name,
			'user_id': user_id,
			'message_count': 0,
			'last_activity': datetime.now(timezone('Asia/Ho_Chi_Minh')).isoformat(),
		}

		with self.conversation_dal.transaction():
			conversation = self.conversation_dal.create(conversation_data)

			return conversation

	def update_conversation(self, conversation_id: str, user_id: str, name: str = None):
		"""Update conversation details"""
		conversation = self.get_conversation_by_id(conversation_id, user_id)

		update_data = {}
		if name:
			update_data['name'] = name

		if update_data:
			with self.conversation_dal.transaction():
				updated_conversation = self.conversation_dal.update(conversation_id, update_data)
				return updated_conversation

		return conversation

	def delete_conversation(self, conversation_id: str, user_id: str):
		"""Delete a conversation and its messages"""
		conversation = self.get_conversation_by_id(conversation_id, user_id)

		with self.conversation_dal.transaction():
			# Soft delete related messages in MySQL first
			self.message_dal.soft_delete_by_conversation(conversation_id)

			# Soft delete conversation in MySQL
			self.conversation_dal.delete(conversation_id)

	def get_conversation_messages(
		self,
		conversation_id: str,
		page: int = 1,
		page_size: int = 50,
		before_message_id: str = None,
	):
		"""Get messages for a conversation with pagination"""
		print(
			f'\033[93m[ConversationRepo.get_conversation_messages] Getting messages for conversation: {conversation_id}, page: {page}, page_size: {page_size}, before_message_id: {before_message_id}\033[0m'
		)
		messages = self.message_dal.get_conversation_messages(
			conversation_id=conversation_id,
			page=page,
			page_size=page_size,
			before_message_id=before_message_id,
		)
		return messages
