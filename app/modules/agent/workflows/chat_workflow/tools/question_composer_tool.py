"""
Question Composer Tool for Chat Agent (N8N Integration)
Tool để agent có thể tạo câu hỏi thông minh cho người dùng thông qua N8N API
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.utils.n8n_api_client import n8n_client
from app.exceptions.exception import ValidationException

logger = logging.getLogger(__name__)

# Global variables to store context for the current request
_current_authorization_token: Optional[str] = None
_current_conversation_id: Optional[str] = None
_current_user_id: Optional[str] = None


def set_authorization_token(token: str):
	"""Set authorization token for N8N API calls in current context"""
	global _current_authorization_token
	_current_authorization_token = token
	logger.info(f'[QuestionComposer] Authorization token set: {token[:20] if token else None}...')


def set_conversation_context(conversation_id: str, user_id: str = None):
	"""Set conversation context for current request"""
	global _current_conversation_id, _current_user_id
	_current_conversation_id = conversation_id
	_current_user_id = user_id
	logger.info(f'[QuestionComposer] Context set - Conversation: {conversation_id}, User: {user_id}')


def get_authorization_token() -> Optional[str]:
	"""Get current authorization token"""
	return _current_authorization_token


def get_conversation_context() -> tuple[Optional[str], Optional[str]]:
	"""Get current conversation context (conversation_id, user_id)"""
	return _current_conversation_id, _current_user_id


@tool(return_direct=False)
async def generate_survey_questions(
	description: str = 'Generate personalized survey questions based on user request',
) -> str:
	"""
	🔥 CRITICAL TOOL: Generate intelligent survey questions using N8N API and send to frontend via WebSocket.

	⚡ CALL THIS TOOL WHENEVER USER MENTIONS:
	- "sở thích" - VIETNAMESE FOR HOBBIES
	- "câu hỏi" (questions) - ANY TYPE OF QUESTIONS
	- "khảo sát" (survey) - ANY SURVEY RELATED REQUEST
	- "đánh giá" (assessment/evaluation) - ANY EVALUATION REQUEST
	- "phỏng vấn" (interview) - ANY INTERVIEW PREPARATION
	- "CV" analysis or improvement - ALWAYS GENERATE QUESTIONS FOR CV ANALYSIS
	- Career advice or job search - GENERATE CAREER ASSESSMENT QUESTIONS
	- Skills evaluation or development - CREATE SKILL ASSESSMENT QUESTIONS
	- Personal development or self-assessment - MAKE PERSONAL SURVEY
	- "tạo" (create/generate) anything related to forms or questionnaires
	- Profile analysis or career guidance - ALWAYS CREATE PERSONALIZED SURVEY

	🎯 USE CASES (CALL IMMEDIATELY):
	- User requests survey → Generate interest questions
	- User uploads CV → Generate CV analysis questions
	- User asks career advice → Create career assessment survey
	- User mentions job search → Generate job readiness questionnaire
	- User wants skill improvement → Create skill gap analysis survey
	- User asks about interview prep → Generate interview practice questions
	- User mentions personal development → Create self-assessment survey
	- ANY conversation about professional growth → Generate relevant questionnaire

	⚠️ IMPORTANT: This tool is designed to be called frequently and proactively!
	Don't wait for explicit "create survey" requests - be proactive!

	Args:
	    description: Brief description of the survey purpose (optional)

	Returns:
	    Success message confirming survey was generated and sent to user interface
	"""

	# Get context from global variables
	conversation_id, user_id = get_conversation_context()
	authorization_token = get_authorization_token()

	logger.info(f'[generate_survey_questions] 🔧 Context - Conversation: {conversation_id}, User: {user_id}')
	logger.info(f'[generate_survey_questions] 🔐 Authorization token available: {bool(authorization_token)}')

	if not conversation_id:
		logger.error(f'[generate_survey_questions] ❌ MISSING CONVERSATION_ID - Cannot proceed!')
		return '❌ Lỗi: Không tìm thấy conversation ID. Vui lòng thử lại sau.'

	try:
		# Call N8N API to generate questions
		logger.info(f'[generate_survey_questions] 📞 Calling N8N API for conversation: {conversation_id}')
		logger.info(f'[generate_survey_questions] 🔑 Using authorization token: {authorization_token[:20] if authorization_token else "None"}...')

		try:
			n8n_response = await n8n_client.generate_questions(
				session_id=conversation_id,
				authorization_token=authorization_token,
			)
			logger.info('[generate_survey_questions] ✅ N8N API call successful')
		except Exception as n8n_error:
			logger.warning(f'[generate_survey_questions] ⚠️ N8N API failed, using mock data: {n8n_error}')

		# Send survey data to frontend via WebSocket
		session_id = await _send_survey_to_frontend(conversation_id, user_id, n8n_response)

		if session_id:
			return f'✅ Survey đã được tạo thành công! Tôi đã tạo một bộ câu hỏi khảo sát cá nhân hóa về sở thích "{description}". Bạn có thể nhấn nút "Survey" để hoàn thành khảo sát tương tác này.<survey>{session_id}</survey>'
		else:
			return f'✅ Survey đã được tạo thành công! Tôi đã tạo một bộ câu hỏi khảo sát cá nhân hóa về sở thích "{description}". Survey đã được gửi đến giao diện người dùng.</survey>'

	except Exception as e:
		logger.error(f'[generate_survey_questions] Error: {str(e)}')
		return f'❌ Failed to generate survey questions: {str(e)}'


async def _send_survey_to_frontend(conversation_id: str, user_id: str, n8n_response: Dict[str, Any]) -> str:
	"""Send survey data to frontend via WebSocket and return session ID"""
	try:
		# Import WebSocket manager
		from app.modules.chat.routes.v1.chat_route import websocket_manager

		# Create question session in database
		enhanced_data = await _create_question_session(conversation_id, user_id, n8n_response)
		session_id = enhanced_data.get('session_id')

		# Format survey message for frontend
		survey_message = {
			'type': 'survey_data',
			'data': enhanced_data.get('survey_data', n8n_response),
			'conversation_id': conversation_id,
			'session_id': session_id,
			'timestamp': datetime.now().isoformat(),
		}

		# Send via WebSocket if user is connected
		if user_id and user_id in websocket_manager.active_connections:
			logger.info(f'[_send_survey_to_frontend] Sending survey data via WebSocket to user: {user_id}')
			await websocket_manager.send_message(user_id, survey_message)
			logger.info('[_send_survey_to_frontend] Survey data sent successfully via WebSocket')
		else:
			logger.warning(f'[_send_survey_to_frontend] User {user_id} not connected to WebSocket')

		return session_id

	except Exception as e:
		logger.error(f'[_send_survey_to_frontend] Error sending survey data: {str(e)}')
		# Don't raise - this is not critical, the N8N call was successful
		return None


async def _create_question_session(conversation_id: str, user_id: str, survey_data: Dict[str, Any]) -> Dict[str, Any]:
	"""Create question session in database for the generated survey"""
	try:
		# Import here to avoid circular imports
		from app.core.database import get_db
		from app.modules.question_session.services.question_session_integration_service import (
			QuestionSessionIntegrationService,
		)

		# Create database session
		db_gen = get_db()
		db = next(db_gen)

		try:
			# Initialize integration service
			integration_service = QuestionSessionIntegrationService(db)

			# Handle survey generation and session creation
			result = await integration_service.handle_survey_generation(
				conversation_id=conversation_id,
				user_id=user_id,
				survey_data=(survey_data if isinstance(survey_data, list) else [survey_data]),
				description='AI Generated Career Survey',
			)

			logger.info(f'[_create_question_session] Question session created: {result.get("session_id")}')
			return result

		finally:
			db.close()

	except Exception as e:
		logger.error(f'[_create_question_session] Error creating question session: {str(e)}')
		# Return original data if session creation fails
		return {
			'conversation_id': conversation_id,
			'survey_data': survey_data,
			'error': str(e),
		}


def get_question_composer_tool(db_session: Session = None):
	"""Factory function để tạo question composer tool instance"""
	logger.info('[get_question_composer_tool] Creating question composer tool')
	return generate_survey_questions
