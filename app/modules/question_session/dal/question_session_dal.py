from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_
from app.core.base_dal import BaseDAL
from app.core.base_model import Pagination
from app.modules.question_session.models.question_session import QuestionSession
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class QuestionSessionDAL(BaseDAL[QuestionSession]):
	def __init__(self, db: Session):
		super().__init__(db, QuestionSession)

	def get_user_sessions(
		self,
		user_id: str,
		conversation_id: Optional[str] = None,
		page: int = 1,
		page_size: int = 10,
		session_status: Optional[str] = None,
		session_type: Optional[str] = None,
		order_by: str = 'create_date',
		order_direction: str = 'desc',
	) -> Pagination[QuestionSession]:
		"""Get question sessions for a user with filtering and pagination"""
		query = self.db.query(self.model).filter(self.model.user_id == user_id, self.model.is_deleted == False)

		# Apply conversation filter
		if conversation_id:
			query = query.filter(self.model.conversation_id == conversation_id)

		# Apply status filter
		if session_status:
			query = query.filter(self.model.session_status == session_status)

		# Apply type filter
		if session_type:
			query = query.filter(self.model.session_type == session_type)

		# Apply ordering
		order_column = getattr(self.model, order_by, self.model.create_date)
		if order_direction.lower() == 'desc':
			query = query.order_by(desc(order_column))
		else:
			query = query.order_by(asc(order_column))

		# Count total records
		total_count = query.count()

		# Apply pagination
		sessions = query.offset((page - 1) * page_size).limit(page_size).all()

		return Pagination(items=sessions, total_count=total_count, page=page, page_size=page_size)

	def get_session_by_id(self, session_id: str, user_id: str) -> Optional[QuestionSession]:
		"""Get a specific session for a user"""
		return (
			self.db.query(self.model)
			.filter(
				self.model.id == session_id,
				self.model.user_id == user_id,
				self.model.is_deleted == False,
			)
			.first()
		)

	def get_conversation_sessions(self, conversation_id: str, user_id: str, session_status: Optional[str] = None) -> List[QuestionSession]:
		"""Get all sessions for a specific conversation"""
		query = self.db.query(self.model).filter(and_(self.model.conversation_id == conversation_id, self.model.user_id == user_id, self.model.is_deleted == False))

		if session_status:
			query = query.filter(self.model.session_status == session_status)

		return query.order_by(desc(self.model.create_date)).all()

	def get_followup_sessions(self, parent_session_id: str, user_id: str) -> List[QuestionSession]:
		"""Get all follow-up sessions for a parent session"""
		return self.db.query(self.model).filter(and_(self.model.parent_session_id == parent_session_id, self.model.user_id == user_id, self.model.is_deleted == False)).order_by(asc(self.model.create_date)).all()

	def update_session_status(self, session_id: str, status: str, user_id: str) -> Optional[QuestionSession]:
		"""Update session status with user verification"""
		session = self.get_session_by_id(session_id, user_id)
		if session:
			session.session_status = status
			if not self.db.in_transaction():
				self.db.commit()
				self.db.refresh(session)
		return session
