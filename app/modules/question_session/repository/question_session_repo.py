import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends
from pytz import timezone
from sqlalchemy.orm import Session

from app.core.base_model import PaginatedResponse, Pagination, PagingInfo
from app.core.database import get_db
from app.exceptions.exception import (
	NotFoundException,
	ValidationException,
)
from app.middleware.translation_manager import _
from app.modules.chat.dal.conversation_dal import ConversationDAL
from app.modules.question_session.dal.question_answer_dal import QuestionAnswerDAL
from app.modules.question_session.dal.question_session_dal import QuestionSessionDAL
from app.modules.question_session.schemas.question_session_request import (
	CreateQuestionSessionRequest,
	GetQuestionSessionsRequest,
	ParseSurveyResponseRequest,
	SubmitAnswersRequest,
	UpdateQuestionSessionRequest,
)
from app.modules.question_session.schemas.question_session_response import (
	ParsedSurveyResponse,
	QuestionSessionDetailResponse,
	QuestionSessionResponse,
)

logger = logging.getLogger(__name__)


class QuestionSessionRepo:
	def __init__(self, db: Session = Depends(get_db)):
		self.db = db
		self.question_session_dal = QuestionSessionDAL(db)
		self.question_answer_dal = QuestionAnswerDAL(db)
		self.conversation_dal = ConversationDAL(db)

	def create_question_session(self, request: CreateQuestionSessionRequest, user_id: str) -> QuestionSessionResponse:
		"""Create a new question session"""
		# Verify conversation exists and user has access
		conversation = self.conversation_dal.get_user_conversation_by_id(request.conversation_id, user_id)
		if not conversation:
			raise NotFoundException(_('conversation_not_found'))

		# Verify parent session if provided
		if request.parent_session_id:
			parent_session = self.question_session_dal.get_session_by_id(request.parent_session_id, user_id)
			if not parent_session:
				raise NotFoundException(_('parent_session_not_found'))

		session_data = {
			'id': str(uuid.uuid4()),  # Ensure id is a valid string
			'create_date': datetime.now(timezone('Asia/Ho_Chi_Minh')),  # Ensure create_date is a valid datetime
			'name': request.name,
			'conversation_id': request.conversation_id,
			'user_id': user_id,
			'parent_session_id': request.parent_session_id,
			'session_type': request.session_type,
			'questions_data': request.questions_data,
			'session_status': 'active',
			'start_date': datetime.now(timezone('Asia/Ho_Chi_Minh')),
			'extra_metadata': request.extra_metadata,
		}

		session = self.question_session_dal.create(session_data)
		return QuestionSessionResponse.model_validate(session)

	def get_user_sessions(self, request: GetQuestionSessionsRequest, user_id: str) -> PaginatedResponse[QuestionSessionResponse]:
		"""Get user's question sessions with filtering and pagination"""
		# If conversation_id is provided, verify user has access
		if request.conversation_id:
			conversation = self.conversation_dal.get_user_conversation_by_id(request.conversation_id, user_id)
			if not conversation:
				raise NotFoundException(_('conversation_not_found'))

		pagination = self.question_session_dal.get_user_sessions(
			user_id=user_id,
			conversation_id=request.conversation_id,
			page=request.page or 1,
			page_size=request.page_size or 10,
			session_status=request.session_status,
			session_type=request.session_type,
			order_by=request.order_by,
			order_direction=request.order_direction,
		)

		# Convert to response models
		session_responses = [QuestionSessionResponse.model_validate(session) for session in pagination.items]

		return PaginatedResponse(
			items=session_responses,
			paging=PagingInfo(
				total=pagination.total_count,
				total_pages=pagination.total_pages,
				page=pagination.page,
				page_size=pagination.page_size,
			),
		)

	def get_session_detail(self, session_id: str, user_id: str) -> QuestionSessionDetailResponse:
		"""Get detailed session information including answers"""
		session = self.question_session_dal.get_session_by_id(session_id, user_id)
		if not session:
			raise NotFoundException(_('question_session_not_found'))

		# Get session answers
		answers = self.question_answer_dal.get_session_answers(session_id)

		# Get follow-up sessions
		followup_sessions = self.question_session_dal.get_followup_sessions(session_id, user_id)

		return QuestionSessionDetailResponse(
			session=QuestionSessionResponse.model_validate(session),
			answers=[answer.dict() for answer in answers],
			followup_sessions=([QuestionSessionResponse.model_validate(fs) for fs in followup_sessions] if followup_sessions else None),
		)

	def update_session(self, session_id: str, request: UpdateQuestionSessionRequest, user_id: str) -> QuestionSessionResponse:
		"""Update a question session"""
		session = self.question_session_dal.get_session_by_id(session_id, user_id)
		if not session:
			raise NotFoundException(_('question_session_not_found'))

		update_data = {}
		if request.name is not None:
			update_data['name'] = request.name
		if request.session_status is not None:
			update_data['session_status'] = request.session_status
			if request.session_status == 'completed':
				update_data['completion_date'] = datetime.now(timezone('Asia/Ho_Chi_Minh'))
		if request.questions_data is not None:
			update_data['questions_data'] = request.questions_data
		if request.extra_metadata is not None:
			update_data['extra_metadata'] = request.extra_metadata

		updated_session = self.question_session_dal.update(session_id, update_data)
		return QuestionSessionResponse.model_validate(updated_session)

	def submit_answers(self, request: SubmitAnswersRequest, user_id: str) -> ParsedSurveyResponse:
		"""Submit answers to a question session"""
		# Verify session exists and user has access
		session = self.question_session_dal.get_session_by_id(request.session_id, user_id)
		if not session:
			raise NotFoundException(_('question_session_not_found'))

		# Verify conversation access if provided
		if request.conversation_id and session.conversation_id != request.conversation_id:
			raise ValidationException(_('conversation_session_mismatch'))

		answers_processed = 0
		total_answers = len(request.answers)

		try:
			with self.question_session_dal.transaction():
				# Process each answer
				for question_id, answer_value in request.answers.items():
					# Determine answer type based on the data
					answer_type = self._determine_answer_type(answer_value)

					# Get question text from session questions_data if available
					question_text = self._get_question_text(session.questions_data, question_id)

					# Create or update the answer
					self.question_answer_dal.create_or_update_answer(
						session_id=request.session_id,
						question_id=question_id,
						question_text=question_text,
						answer_data=(answer_value if isinstance(answer_value, dict) else {'value': answer_value}),
						answer_type=answer_type,
					)
					answers_processed += 1

				# Update session status if all answers are submitted
				if answers_processed == total_answers:
					self.question_session_dal.update_session_status(request.session_id, 'completed', user_id)

		except Exception as e:
			logger.error(f'Error submitting answers: {e}')
			raise ValidationException(_('failed_to_submit_answers'))

		# Get updated session
		updated_session = self.question_session_dal.get_session_by_id(request.session_id, user_id)

		return ParsedSurveyResponse(
			session_id=request.session_id,
			conversation_id=session.conversation_id,
			total_answers=total_answers,
			answers_processed=answers_processed,
			session_status=updated_session.session_status,
			completion_date=updated_session.completion_date,
		)

	def parse_survey_response(self, request: ParseSurveyResponseRequest, user_id: str) -> ParsedSurveyResponse:
		"""Parse survey response from WebSocket and store answers"""
		logger.info(f'Parsing survey response for user {user_id}, conversation {request.conversation_id}')

		# Verify conversation access
		conversation = self.conversation_dal.get_user_conversation_by_id(request.conversation_id, user_id)
		if not conversation:
			raise NotFoundException(_('conversation_not_found'))

		# Find or create active session for this conversation
		active_sessions = self.question_session_dal.get_conversation_sessions(request.conversation_id, user_id, session_status='active')

		if not active_sessions:
			raise NotFoundException(_('no_active_session_found'))

		# Use the most recent active session
		session = active_sessions[0]

		# Convert answers to the format expected by submit_answers
		submit_request = SubmitAnswersRequest(
			session_id=session.id,
			answers=request.answers,
			conversation_id=request.conversation_id,
		)

		return self.submit_answers(submit_request, user_id)

	def delete_session(self, session_id: str, user_id: str) -> bool:
		"""Delete a question session (soft delete)"""
		session = self.question_session_dal.get_session_by_id(session_id, user_id)
		if not session:
			raise NotFoundException(_('question_session_not_found'))

		try:
			with self.question_session_dal.transaction():
				# Delete all answers first
				self.question_answer_dal.delete_session_answers(session_id)

				# Delete the session
				self.question_session_dal.delete(session_id)

			return True
		except Exception as e:
			logger.error(f'Error deleting session: {e}')
			raise ValidationException(_('failed_to_delete_session'))

	def _determine_answer_type(self, answer_value: Any) -> str:
		"""Determine the answer type based on the value"""
		if isinstance(answer_value, list):
			return 'multiple_choice'
		elif isinstance(answer_value, str):
			return 'text' if len(answer_value) > 50 else 'single_choice'
		elif isinstance(answer_value, (int, float)):
			return 'rating'
		elif isinstance(answer_value, dict):
			return 'complex'
		else:
			return 'text'

	def _get_question_text(self, questions_data: Optional[List[Dict[str, Any]]], question_id: str) -> Optional[str]:
		"""Extract question text from questions_data by question_id"""
		if not questions_data:
			return None

		try:
			# Try to find question by index (if question_id is numeric)
			if question_id.isdigit():
				index = int(question_id)
				if 0 <= index < len(questions_data):
					question = questions_data[index]
					return question.get('Question', question.get('question', question.get('text')))

			# Try to find question by ID field
			for question in questions_data:
				if question.get('id') == question_id or question.get('question_id') == question_id or str(questions_data.index(question)) == question_id:
					return question.get('Question', question.get('question', question.get('text')))

		except (ValueError, IndexError, AttributeError) as e:
			logger.warning(f'Could not extract question text for ID {question_id}: {e}')

		return f'Question {question_id}'
