from sqlalchemy import Column, String, ForeignKey, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from app.core.base_model import BaseEntity
import uuid


class QuestionSession(BaseEntity):
	"""Question Session model representing survey/questionnaire sessions linked to conversations"""

	__tablename__ = 'question_sessions'

	name = Column(String(255), nullable=False, default='New Question Session')
	conversation_id = Column(String(36), ForeignKey('conversations.id'), nullable=False)
	user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
	parent_session_id = Column(String(36), ForeignKey('question_sessions.id'), nullable=True)  # For follow-up sessions
	session_type = Column(String(50), nullable=False, default='survey')  # survey, quiz, assessment, etc.
	questions_data = Column(JSON, nullable=True)  # Store the original questions structure
	session_status = Column(String(20), nullable=False, default='active')  # active, completed, cancelled
	start_date = Column(DateTime, nullable=True)
	completion_date = Column(DateTime, nullable=True)
	extra_metadata = Column(Text, nullable=True)  # Additional metadata as JSON

	# Relationships
	conversation = relationship('Conversation', back_populates='question_sessions')
	user = relationship('User', back_populates='question_sessions')
	parent_session = relationship('QuestionSession', remote_side='QuestionSession.id', back_populates='followup_sessions')
	followup_sessions = relationship('QuestionSession', back_populates='parent_session', cascade='all, delete-orphan')
	answers = relationship('QuestionAnswer', back_populates='session', cascade='all, delete-orphan')


class QuestionAnswer(BaseEntity):
	"""Question Answer model storing individual answers within a session"""

	__tablename__ = 'question_answers'

	session_id = Column(String(36), ForeignKey('question_sessions.id'), nullable=False)
	question_id = Column(String(255), nullable=False)  # References the question ID from questions_data
	question_text = Column(Text, nullable=True)  # Store question text for historical reference
	answer_data = Column(JSON, nullable=False)  # Store the answer data (can be array, string, object)
	answer_type = Column(String(50), nullable=False)  # multiple_choice, single_choice, text, rating, etc.
	submitted_at = Column(DateTime, nullable=True)

	# Relationships
	session = relationship('QuestionSession', back_populates='answers')
