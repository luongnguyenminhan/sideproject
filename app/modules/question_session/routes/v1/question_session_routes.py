"""
Question Session API Routes
CRUD operations for question sessions and survey management
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.base_model import APIResponse
from app.exceptions.handlers import handle_exceptions
from app.http.oauth2 import get_current_user
from app.middleware.translation_manager import _
from app.enums.base_enums import BaseErrorCode
from app.modules.question_session.repository.question_session_repo import QuestionSessionRepo
from app.modules.question_session.services.question_session_integration_service import QuestionSessionIntegrationService
from app.modules.question_session.schemas.question_session_request import CreateQuestionSessionRequest, UpdateQuestionSessionRequest, SubmitAnswersRequest, GetQuestionSessionsRequest, ParseSurveyResponseRequest
from app.modules.question_session.schemas.question_session_response import CreateQuestionSessionResponse, SubmitAnswersResponse, GetQuestionSessionsResponse

logger = logging.getLogger(__name__)

route = APIRouter(prefix='/question-sessions', tags=['Question Sessions'])


@route.post('/', response_model=APIResponse)
@handle_exceptions
async def create_question_session(
	request: CreateQuestionSessionRequest,
	repo: QuestionSessionRepo = Depends(),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Create a new question session"""
	user_id = current_user_payload['user_id']
	session = repo.create_question_session(request, user_id)

	return APIResponse(error_code=BaseErrorCode.ERROR_CODE_SUCCESS, message=_('question_session_created_successfully'), data=session)


@route.get('/', response_model=APIResponse)
@handle_exceptions
async def get_question_sessions(
	request: GetQuestionSessionsRequest = Depends(),
	repo: QuestionSessionRepo = Depends(),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get user's question sessions with filtering and pagination"""
	user_id = current_user_payload['user_id']
	result = repo.get_user_sessions(request, user_id)

	return APIResponse(error_code=BaseErrorCode.ERROR_CODE_SUCCESS, message=_('success'), data=result)


@route.get('/{session_id}', response_model=APIResponse)
@handle_exceptions
async def get_question_session_detail(
	session_id: str,
	repo: QuestionSessionRepo = Depends(),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get detailed question session information"""
	user_id = current_user_payload['user_id']
	session_detail = repo.get_session_detail(session_id, user_id)

	return APIResponse(error_code=BaseErrorCode.ERROR_CODE_SUCCESS, message=_('success'), data=session_detail)


@route.put('/{session_id}', response_model=APIResponse)
@handle_exceptions
async def update_question_session(
	session_id: str,
	request: UpdateQuestionSessionRequest,
	repo: QuestionSessionRepo = Depends(),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Update a question session"""
	user_id = current_user_payload['user_id']
	session = repo.update_session(session_id, request, user_id)

	return APIResponse(error_code=BaseErrorCode.ERROR_CODE_SUCCESS, message=_('question_session_updated_successfully'), data=session)


@route.delete('/{session_id}', response_model=APIResponse)
@handle_exceptions
async def delete_question_session(
	session_id: str,
	repo: QuestionSessionRepo = Depends(),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Delete a question session"""
	user_id = current_user_payload['user_id']
	success = repo.delete_session(session_id, user_id)

	return APIResponse(error_code=BaseErrorCode.ERROR_CODE_SUCCESS, message=_('question_session_deleted_successfully'), data={'deleted': success})


@route.post('/submit-answers', response_model=APIResponse)
@handle_exceptions
async def submit_answers(
	request: SubmitAnswersRequest,
	repo: QuestionSessionRepo = Depends(),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Submit answers to a question session"""
	user_id = current_user_payload['user_id']
	result = repo.submit_answers(request, user_id)

	return APIResponse(error_code=BaseErrorCode.ERROR_CODE_SUCCESS, message=_('answers_submitted_successfully'), data=result)


@route.post('/parse-survey-response', response_model=APIResponse)
@handle_exceptions
async def parse_survey_response(
	request: ParseSurveyResponseRequest,
	repo: QuestionSessionRepo = Depends(),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Parse and store survey response from WebSocket"""
	user_id = current_user_payload['user_id']

	logger.info(f'Received survey response for user {user_id}')
	logger.info(f'Request data: {request.model_dump()}')

	result = repo.parse_survey_response(request, user_id)

	return APIResponse(error_code=BaseErrorCode.ERROR_CODE_SUCCESS, message=_('survey_response_processed_successfully'), data=result)


@route.get('/{session_id}/questions', response_model=APIResponse)
@handle_exceptions
async def get_session_questions(
	session_id: str,
	repo: QuestionSessionRepo = Depends(),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get questions data for a specific session"""
	user_id = current_user_payload['user_id']
	session_detail = repo.get_session_detail(session_id, user_id)

	# Extract questions data from session
	questions_data = session_detail.session.questions_data

	if not questions_data:
		raise ValueError('No questions found for this session')

	result = {
		'session_id': session_id,
		'session_name': session_detail.session.name,
		'session_type': session_detail.session.session_type,
		'questions': questions_data,
		'total_questions': (len(questions_data) if isinstance(questions_data, list) else 1),
		'session_status': session_detail.session.session_status,
	}

	return APIResponse(error_code=BaseErrorCode.ERROR_CODE_SUCCESS, message=_('success'), data=result)


@route.post('/{session_id}/submit', response_model=APIResponse)
@handle_exceptions
async def submit_session_answers(
	session_id: str,
	request: SubmitAnswersRequest,
	repo: QuestionSessionRepo = Depends(),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Submit answers for a question session"""
	# Ensure session_id matches
	request.session_id = session_id
	user_id = current_user_payload['user_id']
	result = repo.submit_answers(request, user_id)

	return APIResponse(error_code=BaseErrorCode.ERROR_CODE_SUCCESS, message=_('answers_submitted_successfully'), data=result)


@route.get('/conversation/{conversation_id}/active', response_model=APIResponse)
@handle_exceptions
async def get_active_session_for_conversation(
	conversation_id: str,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get the most recent active session for a conversation"""
	user_id = current_user_payload['user_id']
	integration_service = QuestionSessionIntegrationService(db)
	session_id = await integration_service.get_active_session_for_conversation(conversation_id, user_id)

	if session_id:
		result = {'session_id': session_id}
	else:
		raise ValueError('No active session found for this conversation')

	return APIResponse(error_code=BaseErrorCode.ERROR_CODE_SUCCESS, message=_('success'), data=result)
