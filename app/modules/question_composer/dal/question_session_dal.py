"""
Question session data access layer.
"""

from sqlalchemy.orm import Session
from typing import List, Optional

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.base_dal import BaseDAL
from ..models.question_session_model import QuestionSession


class QuestionSessionDAL(BaseDAL[QuestionSession]):
	"""
	Data access layer for question sessions.

	Handles all database operations for question generation sessions.
	"""

	def __init__(self, db: Session):
		super().__init__(db, QuestionSession)

	def get_by_session_id(self, session_id: str) -> Optional[QuestionSession]:
		"""Get question session by session ID"""
		return self.db.query(self.model).filter(self.model.session_id == session_id, self.model.is_deleted == False).first()

	def get_by_user_id(self, user_id: str) -> List[QuestionSession]:
		"""Get all question sessions for a user"""
		return self.db.query(self.model).filter(self.model.user_id == user_id, self.model.is_deleted == False).order_by(self.model.create_date.desc()).all()

	def get_active_sessions(self) -> List[QuestionSession]:
		"""Get all active question sessions"""
		return self.db.query(self.model).filter(self.model.status == 'active', self.model.is_deleted == False).all()

	def get_by_status(self, status: str) -> List[QuestionSession]:
		"""Get sessions by status"""
		return self.db.query(self.model).filter(self.model.status == status, self.model.is_deleted == False).all()

	def update_session_progress(
		self,
		session_id: str,
		current_iteration: int,
		completeness_score: float,
		should_continue: bool,
	) -> Optional[QuestionSession]:
		"""Update session progress"""
		session = self.get_by_session_id(session_id)
		if session:
			session.current_iteration = current_iteration
			session.completeness_score = completeness_score
			session.should_continue = should_continue

			if not should_continue or current_iteration >= session.max_iterations:
				session.status = 'completed'
				session.info = True

			self.db.commit()
			return session
		return None

	def save_generated_questions(self, session_id: str, generated_questions: list, all_previous_questions: list) -> Optional[QuestionSession]:
		"""Save generated questions to session"""
		session = self.get_by_session_id(session_id)
		if session:
			session.generated_questions = generated_questions
			session.all_previous_questions = all_previous_questions
			session.total_questions_generated = len(all_previous_questions)
			self.db.commit()
			return session
		return None

	def save_analysis_result(
		self,
		session_id: str,
		analysis_decision: dict,
		missing_areas: list,
		focus_areas: list,
	) -> Optional[QuestionSession]:
		"""Save analysis results"""
		session = self.get_by_session_id(session_id)
		if session:
			session.analysis_decision = analysis_decision
			session.missing_areas = missing_areas
			session.focus_areas = focus_areas
			self.db.commit()
			return session
		return None

	def mark_session_error(self, session_id: str, error_message: str) -> Optional[QuestionSession]:
		"""Mark session with error"""
		session = self.get_by_session_id(session_id)
		if session:
			session.error_message = error_message
			session.status = 'error'
			self.db.commit()
			return session
		return None
