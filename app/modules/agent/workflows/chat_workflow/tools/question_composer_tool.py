"""
Question Composer Tool for Chat Agent (N8N Integration)
Tool để agent có thể tạo câu hỏi thông minh cho người dùng thông qua N8N API
"""

import logging
import json
from typing import Dict, Any
from datetime import datetime
from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.utils.n8n_api_client import n8n_client
from app.exceptions.exception import ValidationException

logger = logging.getLogger(__name__)


@tool
async def generate_survey_questions(conversation_id: str, user_id: str = None) -> str:
	"""
	Generate intelligent survey questions using N8N API and send to frontend via WebSocket.

	Use this tool when user asks about:
	- Creating questions, surveys, or forms
	- CV analysis, profile analysis, or career development
	- Interview questions or skill assessment
	- Generating personalized questionnaires

	Args:
	    conversation_id: ID of the current conversation (required)
	    user_id: ID of the user for WebSocket delivery (optional)

	Returns:
	    Success message confirming survey was generated and sent to user interface
	"""
	logger.info(f'[generate_survey_questions] Starting for conversation: {conversation_id}')

	if not conversation_id:
		raise ValidationException('conversation_id is required')

	try:
		# Call N8N API to generate questions
		logger.info(f'[generate_survey_questions] Calling N8N API for conversation: {conversation_id}')

		n8n_response = await n8n_client.generate_questions(
			session_id=conversation_id,
			authorization_token=None,  # Will be set by agent if needed
		)

		logger.info('[generate_survey_questions] N8N API call successful')

		# Send survey data to frontend via WebSocket
		await _send_survey_to_frontend(conversation_id, user_id, n8n_response)

		return "✅ Survey questions generated successfully! The interactive survey has been sent to the user's interface for completion."

	except Exception as e:
		logger.error(f'[generate_survey_questions] Error: {str(e)}')
		return f'❌ Failed to generate survey questions: {str(e)}'


async def _send_survey_to_frontend(conversation_id: str, user_id: str, n8n_response: Dict[str, Any]):
	"""Send survey data to frontend via WebSocket"""
	try:
		# Import WebSocket manager
		from app.modules.chat.routes.v1.chat_route import websocket_manager

		# Format survey data for frontend
		survey_message = {
			'type': 'survey_data',
			'data': n8n_response,
			'conversation_id': conversation_id,
			'timestamp': datetime.now().isoformat(),
		}

		# Send via WebSocket if user is connected
		if user_id and user_id in websocket_manager.active_connections:
			logger.info(f'[_send_survey_to_frontend] Sending survey data via WebSocket to user: {user_id}')
			await websocket_manager.send_message(user_id, survey_message)
			logger.info('[_send_survey_to_frontend] Survey data sent successfully via WebSocket')
		else:
			logger.warning(f'[_send_survey_to_frontend] User {user_id} not connected to WebSocket')

	except Exception as e:
		logger.error(f'[_send_survey_to_frontend] Error sending survey data: {str(e)}')
		# Don't raise - this is not critical, the N8N call was successful


def get_question_composer_tool(db_session: Session):
	"""Factory function để tạo question composer tool instance"""
	logger.info('[get_question_composer_tool] Creating question composer tool')
	return generate_survey_questions
