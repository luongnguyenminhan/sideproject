from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.base_dal import BaseDAL
from app.core.base_model import Pagination
from app.modules.chat.models.message import Message
from typing import List, Optional


class MessageDAL(BaseDAL[Message]):
	def __init__(self, db: Session):
		super().__init__(db, Message)

	def get_conversation_messages(
		self,
		conversation_id: str,
		page: int = 1,
		page_size: int = 50,
		before_message_id: Optional[str] = None,
	):
		"""Get messages for a conversation with pagination"""
		print(
			f'\033[93m[MessageDAL.get_conversation_messages] Getting messages for conversation: {conversation_id}, page: {page}, page_size: {page_size}, before_message_id: {before_message_id}\033[0m'
		)
		query = self.db.query(self.model).filter(
			self.model.conversation_id == conversation_id,
			self.model.is_deleted == False,
		)

		# If before_message_id is provided, get messages before that message
		if before_message_id:
			before_message = self.get_by_id(before_message_id)
			if before_message:
				query = query.filter(self.model.timestamp < before_message.timestamp)
			else:
				pass
		# Order by timestamp descending (newest first)
		query = query.order_by(self.model.timestamp)

		# Count total records
		total_count = query.count()

		# Apply pagination
		conversations = query.offset((page - 1) * page_size).limit(page_size).all()

		paginated_result = Pagination(items=conversations, total_count=total_count, page=page, page_size=page_size)
		return paginated_result

	def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Message]:
		"""Get recent messages for conversation context"""
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
		return messages

	def get_latest_message(self, conversation_id: str) -> Optional[Message]:
		"""Get the latest message in a conversation"""
		message = (
			self.db.query(self.model)
			.filter(
				self.model.conversation_id == conversation_id,
				self.model.is_deleted == False,
			)
			.order_by(desc(self.model.timestamp))
			.first()
		)
		return message

	def soft_delete_by_conversation(self, conversation_id: str):
		"""Soft delete all messages in a conversation"""
		updated_count = (
			self.db.query(self.model)
			.filter(
				self.model.conversation_id == conversation_id,
				self.model.is_deleted == False,
			)
			.update({'is_deleted': True})
		)
		return updated_count
