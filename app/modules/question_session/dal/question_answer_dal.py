import logging
from datetime import datetime
from typing import List, Optional

from pytz import timezone
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.core.base_dal import BaseDAL
from app.modules.question_session.models.question_session import QuestionAnswer

logger = logging.getLogger(__name__)


class QuestionAnswerDAL(BaseDAL[QuestionAnswer]):
	def __init__(self, db: Session):
		super().__init__(db, QuestionAnswer)

	def get_session_answers(self, session_id: str) -> List[QuestionAnswer]:
		"""Get all answers for a specific session"""
		return self.db.query(self.model).filter(and_(self.model.session_id == session_id, self.model.is_deleted == False)).order_by(desc(self.model.create_date)).all()

	def get_answer_by_question(self, session_id: str, question_id: str) -> Optional[QuestionAnswer]:
		"""Get answer for a specific question in a session"""
		return (
			self.db.query(self.model)
			.filter(
				and_(
					self.model.session_id == session_id,
					self.model.question_id == question_id,
					self.model.is_deleted == False,
				)
			)
			.first()
		)

	def create_or_update_answer(
		self,
		session_id: str,
		question_id: str,
		question_text: Optional[str],
		answer_data: dict,
		answer_type: str,
	) -> QuestionAnswer:
		"""Create or update an answer for a question"""
		# Check if answer already exists
		existing_answer = self.get_answer_by_question(session_id, question_id)

		if existing_answer:
			# Update existing answer
			update_data = {
				'answer_data': answer_data,
				'answer_type': answer_type,
				'submitted_at': datetime.now(timezone('Asia/Ho_Chi_Minh')),
			}
			if question_text:
				update_data['question_text'] = question_text

			return self.update(existing_answer.id, update_data)
		else:
			# Create new answer
			answer_data_dict = {
				'session_id': session_id,
				'question_id': question_id,
				'question_text': question_text,
				'answer_data': answer_data,
				'answer_type': answer_type,
				'submitted_at': datetime.now(timezone('Asia/Ho_Chi_Minh')),
			}
			return self.create(answer_data_dict)

	def delete_session_answers(self, session_id: str) -> bool:
		"""Delete (soft delete) all answers for a session"""
		answers = self.get_session_answers(session_id)

		try:
			for answer in answers:
				self.delete(answer.id)
			return True
		except Exception as e:
			logger.error(f'Error deleting session answers: {e}')
			return False

	def get_answers_by_question_ids(self, session_id: str, question_ids: List[str]) -> List[QuestionAnswer]:
		"""Get answers for specific question IDs in a session"""
		return (
			self.db.query(self.model)
			.filter(
				and_(
					self.model.session_id == session_id,
					self.model.question_id.in_(question_ids),
					self.model.is_deleted == False,
				)
			)
			.all()
		)
