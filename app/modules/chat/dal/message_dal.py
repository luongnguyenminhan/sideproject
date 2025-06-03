from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.base_dal import BaseDAL
from app.core.base_model import Pagination
from app.modules.chat.models.message import Message
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class MessageDAL(BaseDAL[Message]):
	def __init__(self, db: Session):
		logger.info(f'\033[96m[MessageDAL.__init__] Initializing MessageDAL with db session: {db}\033[0m')
		super().__init__(db, Message)
		logger.info(f'\033[92m[MessageDAL.__init__] MessageDAL initialized successfully\033[0m')

	def get_conversation_messages(
		self,
		conversation_id: str,
		page: int = 1,
		page_size: int = 50,
		before_message_id: Optional[str] = None,
	):
		"""Get messages for a conversation with pagination"""
		logger.info(f'\033[93m[MessageDAL.get_conversation_messages] Getting messages for conversation: {conversation_id}, page: {page}, page_size: {page_size}, before_message_id: {before_message_id}\033[0m')
		query = self.db.query(self.model).filter(
			self.model.conversation_id == conversation_id,
			self.model.is_deleted == False,
		)
		logger.info(f'\033[94m[MessageDAL.get_conversation_messages] Base query created for conversation messages\033[0m')

		# If before_message_id is provided, get messages before that message
		if before_message_id:
			logger.info(f'\033[94m[MessageDAL.get_conversation_messages] Applying before_message filter: {before_message_id}\033[0m')
			before_message = self.get_by_id(before_message_id)
			if before_message:
				logger.info(f'\033[94m[MessageDAL.get_conversation_messages] Found before_message, filtering by timestamp: {before_message.timestamp}\033[0m')
				query = query.filter(self.model.timestamp < before_message.timestamp)
			else:
				logger.info(f'\033[95m[MessageDAL.get_conversation_messages] Before message not found: {before_message_id}\033[0m')

		# Order by timestamp descending (newest first)
		logger.info(f'\033[94m[MessageDAL.get_conversation_messages] Ordering by timestamp descending\033[0m')
		query = query.order_by(self.model.timestamp)

		# Count total records
		total_count = query.count()

		# Apply pagination
		conversations = query.offset((page - 1) * page_size).limit(page_size).all()

		logger.info(f'Found {total_count} conversations, returning page {page} with {len(conversations)} items')

		paginated_result = Pagination(items=conversations, total_count=total_count, page=page, page_size=page_size)
		logger.info(f'\033[92m[MessageDAL.get_conversation_messages] Pagination completed, returning results\033[0m')
		return paginated_result

	def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Message]:
		"""Get recent messages for conversation context"""
		logger.info(f'\033[93m[MessageDAL.get_conversation_history] Getting conversation history for: {conversation_id}, limit: {limit}\033[0m')
		messages = (
			self.db.query(self.model)
			.filter(
				self.model.conversation_id == conversation_id,
				self.model.is_deleted == False,
			)
			.order_by(desc(self.model.timestamp))
			.limit(limit)
			.all()
		)
		logger.info(f'\033[92m[MessageDAL.get_conversation_history] Found {len(messages)} messages in history\033[0m')
		return messages

	def get_latest_message(self, conversation_id: str) -> Optional[Message]:
		"""Get the latest message in a conversation"""
		logger.info(f'\033[93m[MessageDAL.get_latest_message] Getting latest message for conversation: {conversation_id}\033[0m')
		message = (
			self.db.query(self.model)
			.filter(
				self.model.conversation_id == conversation_id,
				self.model.is_deleted == False,
			)
			.order_by(desc(self.model.timestamp))
			.first()
		)
		if message:
			logger.info(f'\033[92m[MessageDAL.get_latest_message] Found latest message: {message.id}, role: {message.role}, timestamp: {message.timestamp}\033[0m')
		else:
			logger.info(f'\033[95m[MessageDAL.get_latest_message] No messages found for conversation: {conversation_id}\033[0m')
		return message

	def soft_delete_by_conversation(self, conversation_id: str):
		"""Soft delete all messages in a conversation"""
		logger.info(f'\033[93m[MessageDAL.soft_delete_by_conversation] Soft deleting all messages for conversation: {conversation_id}\033[0m')
		updated_count = (
			self.db.query(self.model)
			.filter(
				self.model.conversation_id == conversation_id,
				self.model.is_deleted == False,
			)
			.update({'is_deleted': True})
		)
		logger.info(f'\033[92m[MessageDAL.soft_delete_by_conversation] Soft deleted {updated_count} messages for conversation: {conversation_id}\033[0m')
		return updated_count
