from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.core.base_dal import BaseDAL
from app.core.base_model import Pagination
from app.modules.chat.models.conversation import Conversation
from typing import Optional


class ConversationDAL(BaseDAL[Conversation]):
	def __init__(self, db: Session):
		super().__init__(db, Conversation)

	def get_user_conversations(
		self,
		user_id: str,
		page: int = 1,
		page_size: int = 10,
		search: Optional[str] = None,
		order_by: str = 'last_activity',
		order_direction: str = 'desc',
	):
		"""Get conversations for a user with pagination and filtering"""
		print(
			f'\033[93m[ConversationDAL.get_user_conversations] Getting conversations for user: {user_id}, page: {page}, page_size: {page_size}, search: {search}, order_by: {order_by}, order_direction: {order_direction}\033[0m'
		)
		query = self.db.query(self.model).filter(self.model.user_id == user_id, self.model.is_deleted == False)

		# Apply search filter
		if search:
			query = query.filter(self.model.name.ilike(f'%{search}%'))

		# Apply ordering
		order_column = getattr(self.model, order_by, self.model.last_activity)
		if order_direction.lower() == 'desc':
			query = query.order_by(desc(order_column))
		else:
			query = query.order_by(asc(order_column))

		# Count total records
		total_count = query.count()

		# Apply pagination
		conversations = query.offset((page - 1) * page_size).limit(page_size).all()


		paginated_result = Pagination(items=conversations, total_count=total_count, page=page, page_size=page_size)
		return paginated_result

	def get_user_conversation_by_id(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
		"""Get a specific conversation for a user"""
		conversation = (
			self.db.query(self.model)
			.filter(
				self.model.id == conversation_id,
				self.model.user_id == user_id,
				self.model.is_deleted == False,
			)
			.first()
		)
		if conversation:
			print(
				f'\033[92m[ConversationDAL.get_user_conversation_by_id] Found conversation: {conversation.name}, message_count: {conversation.message_count}, last_activity: {conversation.last_activity}\033[0m'
			)
		else:
			pass
		return conversation
