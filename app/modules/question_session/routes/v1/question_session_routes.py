"""
Question Session API Routes
CRUD operations for question sessions and survey management
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.base_model import APIResponse
from app.exceptions.handlers import handle_exceptions
from app.http.oauth2 import get_current_user
from app.middleware.translation_manager import _
from app.enums.base_enums import BaseErrorCode
from app.modules.question_session.repository.question_session_repo import (
	QuestionSessionRepo,
)
from app.modules.question_session.services.question_session_integration_service import (
	QuestionSessionIntegrationService,
)
from app.modules.question_session.services.survey_response_processor import (
	SurveyResponseProcessor,
)
from app.modules.question_session.schemas.question_session_request import (
	CreateQuestionSessionRequest,
	UpdateQuestionSessionRequest,
	SubmitAnswersRequest,
	GetQuestionSessionsRequest,
	ParseSurveyResponseRequest,
)
from app.modules.question_session.schemas.question_session_response import (
	CreateQuestionSessionResponse,
	SubmitAnswersResponse,
	GetQuestionSessionsResponse,
)

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

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('question_session_created_successfully'),
		data=session,
	)


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

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('success'),
		data=session_detail,
	)


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

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('question_session_updated_successfully'),
		data=session,
	)


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

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('question_session_deleted_successfully'),
		data={'deleted': success},
	)


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

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('answers_submitted_successfully'),
		data=result,
	)


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

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('survey_response_processed_successfully'),
		data=result,
	)


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

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('answers_submitted_successfully'),
		data=result,
	)


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


@route.post('/process-survey-response', response_model=APIResponse)
@handle_exceptions
async def process_survey_response_for_ai(
	request: ParseSurveyResponseRequest,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""
	Enhanced API endpoint for processing survey responses and integrating with AI workflow

	This endpoint:
	1. Stores survey responses in the database
	2. Converts responses to human-readable text
	3. Processes the text through AI workflow
	4. Returns comprehensive response including AI feedback
	"""
	user_id = current_user_payload['user_id']

	logger.info(f'Processing survey response for AI integration - user: {user_id}, conversation: {request.conversation_id}, session_id: {request.session_id}')

	# Initialize the survey response processor
	processor = SurveyResponseProcessor(db)

	# Get agent instance if available (optional - can be None for text-only processing)
	agent_instance = None
	try:
		# Import and get system agent for AI processing
		from app.modules.agent.repository.system_agent_repo import SystemAgentRepo

		agent_repo = SystemAgentRepo(db)
		agent_instance = agent_repo.get_system_agent()
		logger.info(f'Loaded system agent for survey processing: {agent_instance.name if hasattr(agent_instance, "name") else "SystemAgent"}')
	except Exception as e:
		logger.warning(f'Could not load agent instance: {e}')
		agent_instance = None

	# Process the survey response
	result = await processor.process_survey_response_for_ai(request=request, user_id=user_id, agent_instance=agent_instance)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('survey_response_processed_and_ai_integrated_successfully'),
		data=result,
	)


@route.post('/format-survey-as-human-message', response_model=APIResponse)
@handle_exceptions
async def format_survey_as_human_message(
	request: ParseSurveyResponseRequest,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""
	Convert survey response to human-readable message format

	This endpoint is useful for converting survey responses to text that can be
	sent to AI systems as human input messages.
	"""
	user_id = current_user_payload['user_id']

	logger.info(f'Formatting survey response as human message - user: {user_id}, conversation: {request.conversation_id}, session_id: {request.session_id}')

	# Initialize the survey response processor
	processor = SurveyResponseProcessor(db)

	# Format as human message
	human_message = await processor.format_survey_response_as_human_message(request=request, user_id=user_id)

	result = {
		'human_message': human_message,
		'conversation_id': request.conversation_id,
		'processed_at': request.timestamp or datetime.now().isoformat(),
		'user_id': user_id,
	}

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('survey_formatted_as_human_message_successfully'),
		data=result,
	)


@route.post('/complete-survey-workflow', response_model=APIResponse)
@handle_exceptions
async def complete_survey_workflow(
	request: ParseSurveyResponseRequest,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
	authorization: Optional[str] = Header(None),
):
	"""
	Complete survey workflow with N8N analysis: Process responses + N8N AI analysis + Results

	Enhanced pipeline with N8N integration:
	1. Process and store survey responses in database
	2. Convert responses to human-readable text format
	3. Send to N8N API for advanced AI analysis and insights
	4. Return comprehensive results including N8N analysis
	5. Maintain compatibility for chat integration
	"""
	user_id = current_user_payload['user_id']

	logger.info(f'Starting N8N-enhanced survey workflow - user: {user_id}, conversation: {request.conversation_id}, session_id: {request.session_id}')

	# Extract authorization token from header
	auth_token = None
	if authorization and authorization.startswith('Bearer '):
		auth_token = authorization[7:]  # Remove 'Bearer ' prefix
		logger.info(f'Authorization token extracted for N8N API calls')
	else:
		logger.warning(f'No authorization token provided for N8N API calls')

	# Initialize the survey response processor with N8N integration
	processor = SurveyResponseProcessor(db)

	# Process with N8N analysis
	result = await processor.process_survey_response_with_n8n_analysis(request=request, user_id=user_id, authorization_token=auth_token)

	# Enhance result with WebSocket-ready messages for compatibility
	enhanced_result = {
		**result,
		'websocket_messages': (
			[
				{
					'type': 'chat_message',
					'role': 'user',
					'content': result.get('human_readable_response', ''),
					'conversation_id': request.conversation_id,
					'user_id': user_id,
					'source': 'survey_completion',
					'timestamp': datetime.now().isoformat(),
				},
				{
					'type': 'chat_message',
					'role': 'assistant',
					'content': result.get('ai_response', ''),
					'conversation_id': request.conversation_id,
					'user_id': user_id,
					'source': 'n8n_survey_analysis',
					'timestamp': datetime.now().isoformat(),
				},
			]
			if result.get('human_readable_response') and result.get('ai_response')
			else []
		),
		'chat_integration': {
			'ready_for_websocket': bool(result.get('human_readable_response') and result.get('ai_response')),
			'human_message_available': bool(result.get('human_readable_response')),
			'ai_response_available': bool(result.get('ai_response')),
			'n8n_analysis_available': bool(result.get('n8n_analysis')),
			'n8n_success': result.get('processing_metadata', {}).get('n8n_success', False),
		},
	}

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('complete_survey_workflow_with_n8n_analysis_processed_successfully'),
		data=enhanced_result,
	)


@route.post('/process-and-send-to-chat', response_model=APIResponse)
@handle_exceptions
async def process_survey_and_send_to_chat(
	request: ParseSurveyResponseRequest,
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""
	Process survey response and automatically send to chat workflow

	This endpoint:
	1. Processes and stores survey responses
	2. Converts to human-readable format
	3. Gets AI analysis
	4. Returns formatted messages for chat integration
	5. Provides WebSocket-ready message formats
	"""
	user_id = current_user_payload['user_id']

	logger.info(f'Processing survey and preparing for chat integration - user: {user_id}, conversation: {request.conversation_id}, session_id: {request.session_id}')

	# Import the integration service
	from app.modules.question_session.services.survey_chat_integration import (
		SurveyChatIntegrationService,
	)

	# Initialize the integration service
	integration_service = SurveyChatIntegrationService(db)

	# Process the complete workflow
	result = await integration_service.process_survey_and_chat_response(
		survey_request=request.model_dump(),
		conversation_id=request.conversation_id,
		user_id=user_id,
		custom_ai_prompt='Please analyze this survey response and provide helpful insights, recommendations, or follow-up questions.',
	)

	# Prepare WebSocket-ready messages
	websocket_messages = []

	# Human message for WebSocket
	if result.get('human_message'):
		websocket_messages.append({
			'type': 'chat_message',
			'role': 'user',
			'content': result['human_message'],
			'conversation_id': request.conversation_id,
			'user_id': user_id,
			'source': 'survey_completion',
			'timestamp': datetime.now().isoformat(),
		})

	# AI response message for WebSocket
	if result.get('ai_response', {}).get('content'):
		websocket_messages.append({
			'type': 'chat_message',
			'role': 'assistant',
			'content': result['ai_response']['content'],
			'conversation_id': request.conversation_id,
			'user_id': user_id,
			'source': 'survey_analysis',
			'timestamp': datetime.now().isoformat(),
		})

	# Enhanced result with WebSocket messages
	enhanced_result = {
		**result,
		'websocket_messages': websocket_messages,
		'chat_integration': {
			'ready_for_websocket': len(websocket_messages) > 0,
			'human_message_available': bool(result.get('human_message')),
			'ai_response_available': bool(result.get('ai_response', {}).get('content')),
			'total_messages': len(websocket_messages),
		},
	}

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('survey_processed_and_ready_for_chat_integration'),
		data=enhanced_result,
	)


@route.post('/submit-response', response_model=APIResponse)
@handle_exceptions
async def submit_response(
	request: ParseSurveyResponseRequest,
	repo: QuestionSessionRepo = Depends(),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Submit basic survey response (fallback endpoint)"""
	user_id = current_user_payload['user_id']
	result = repo.parse_survey_response(request, user_id)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('survey_response_submitted_successfully'),
		data=result,
	)
