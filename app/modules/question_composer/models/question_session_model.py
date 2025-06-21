"""
Question session database model.
"""

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.base_model import BaseEntity


class QuestionSession(BaseEntity):
	"""
	Database entity for question generation sessions.

	Tracks user question generation sessions and their progress.
	"""

	__tablename__ = 'question_sessions'

	# Session identification
	session_id = Column(String(255), nullable=False, index=True)
	user_id = Column(String(255), ForeignKey('users.id'), nullable=True, index=True)

	# Session status
	status = Column(String(50), nullable=False, default='active')  # active, completed, expired
	current_iteration = Column(Integer, nullable=False, default=0)
	max_iterations = Column(Integer, nullable=False, default=5)

	# User profile data
	user_profile_data = Column(JSON, nullable=True)
	existing_user_data = Column(JSON, nullable=True)

	# Generated questions
	generated_questions = Column(JSON, nullable=True)  # List of all generated questions
	all_previous_questions = Column(JSON, nullable=True)  # All questions asked so far

	# Analysis results
	completeness_score = Column(Float, nullable=False, default=0.0)
	missing_areas = Column(JSON, nullable=True)  # List of missing areas
	focus_areas = Column(JSON, nullable=True)  # Areas to focus on next

	# Workflow metadata
	should_continue = Column(Boolean, nullable=False, default=True)
	workflow_complete = Column(Boolean, nullable=False, default=False)
	total_questions_generated = Column(Integer, nullable=False, default=0)

	# Analysis decision
	analysis_decision = Column(JSON, nullable=True)
	generation_history = Column(JSON, nullable=True)  # History of generation rounds

	# Error tracking
	error_message = Column(Text, nullable=True)
	last_error_at = Column(String(255), nullable=True)

	# Relationships
	user = relationship('User', back_populates='question_sessions')

	def __repr__(self):
		return f"<QuestionSession(session_id='{self.session_id}', status='{self.status}', iteration={self.current_iteration})>"
