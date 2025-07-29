"""
JD Matching Tool for Chat Agent (N8N Integration)
Triggers the n8n JD matching workflow with provided JD and candidate data.
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
	print(f'[JDMatching] Authorization token set: {token[:20] if token else None}...')


def set_conversation_context(conversation_id: str, user_id: str = None):
	"""Set conversation context for current request"""
	global _current_conversation_id, _current_user_id
	_current_conversation_id = conversation_id
	_current_user_id = user_id
	logger.info(f'[JDMatching] Context set - Conversation: {conversation_id}, User: {user_id}')


def get_authorization_token() -> Optional[str]:
	"""Get current authorization token"""
	return _current_authorization_token


def get_conversation_context() -> tuple[Optional[str], Optional[str]]:
	"""Get current conversation context (conversation_id, user_id)"""
	return _current_conversation_id, _current_user_id


@tool(return_direct=False)
async def trigger_jd_matching_tool(
	jd_data_json: str = 'Job description data as JSON string',
	candidate_data_json: str = 'Candidate profile data as JSON string',
	description: str = 'JD matching analysis for candidate evaluation',
) -> str:
	"""
	🔥 CRITICAL TOOL: Trigger JD matching workflow using N8N API for candidate evaluation.

	⚡ CALL THIS TOOL WHENEVER USER MENTIONS:
	- "JD matching" or "job matching" - ANY JD MATCHING REQUEST
	- "candidate evaluation" - CANDIDATE ASSESSMENT
	- "job description" analysis - JD ANALYSIS
	- "candidate profile" matching - PROFILE MATCHING
	- "recruitment" or "hiring" - RECRUITMENT PROCESS
	- "candidate screening" - SCREENING PROCESS
	- "job fit" or "role fit" - FIT ANALYSIS
	- "candidate assessment" - ASSESSMENT PROCESS
	- "matching score" - SCORE CALCULATION
	- "recruitment workflow" - WORKFLOW PROCESSING

	🎯 USE CASES (CALL IMMEDIATELY):
	- User provides JD and candidate data → Trigger matching analysis
	- User requests candidate evaluation → Perform JD matching
	- User wants to assess job fit → Run matching workflow
	- User mentions recruitment process → Execute matching analysis
	- User provides candidate profile → Match against JD
	- User requests screening results → Generate matching report
	- User wants hiring insights → Perform comprehensive matching
	- ANY conversation about candidate-job matching → Execute workflow

	⚠️ IMPORTANT: This tool is designed to be called proactively!
	Don't wait for explicit "match JD" requests - be proactive when JD and candidate data are available!

	Args:
	    jd_data_json: Job Description data as JSON string
	    candidate_data_json: Candidate profile data as JSON string
	    description: Brief description of the matching purpose (optional)

	Returns:
	    Success message confirming JD matching was executed and results are available
	"""

	# Get context from global variables
	conversation_id, user_id = get_conversation_context()
	authorization_token = get_authorization_token()

	logger.info(f'[trigger_jd_matching_tool] 🔧 Context - Conversation: {conversation_id}, User: {user_id}')
	logger.info(f'[trigger_jd_matching_tool] 🔐 Authorization token available: {bool(authorization_token)}')

	if not conversation_id:
		logger.error(f'[trigger_jd_matching_tool] ❌ MISSING CONVERSATION_ID - Cannot proceed!')
		return '❌ Lỗi: Không tìm thấy conversation ID. Vui lòng thử lại sau.'

	try:
		# Parse JSON data
		try:
			jd_data = json.loads(jd_data_json)
			candidate_data = json.loads(candidate_data_json)
		except Exception as e:
			logger.error(f'[trigger_jd_matching_tool] Invalid input JSON: {e}')
			return f'❌ Invalid input JSON: {str(e)}'

		# Call N8N API to trigger JD matching
		print(f'[trigger_jd_matching_tool] 📞 Calling N8N JD matching API for conversation: {conversation_id}')
		print(f'[trigger_jd_matching_tool] 🔑 Using authorization token: {authorization_token[:20] if authorization_token else "None"}...')
		print(f'[trigger_jd_matching_tool] 🔧 Description: {description}')
		
		try:
			n8n_response = await n8n_client.trigger_jd_matching(
				jd_data=jd_data,
				candidate_data=candidate_data,
				authorization_token=authorization_token,
			)
			print('[trigger_jd_matching_tool] ✅ N8N JD matching API call successful')
		except Exception as n8n_error:
			logger.warning(f'[trigger_jd_matching_tool] ⚠️ N8N API failed: {n8n_error}')
			return f'❌ Error triggering JD matching: {str(n8n_error)}'

		# Send matching results to frontend via WebSocket
		session_id = await _send_matching_results_to_frontend(conversation_id, user_id, n8n_response, description)

		if session_id:
			return f'✅ JD matching đã được thực hiện thành công! Tôi đã phân tích và đánh giá sự phù hợp giữa ứng viên và vị trí công việc "{description}". Kết quả đã được gửi đến giao diện người dùng.<jd_matching>{session_id}</jd_matching>'
		else:
			return f'✅ JD matching đã được thực hiện thành công! Tôi đã phân tích và đánh giá sự phù hợp giữa ứng viên và vị trí công việc "{description}". Kết quả: {json.dumps(n8n_response)}'

	except Exception as e:
		logger.error(f'[trigger_jd_matching_tool] Error: {str(e)}')
		return f'❌ Failed to trigger JD matching: {str(e)}'


async def _send_matching_results_to_frontend(conversation_id: str, user_id: str, n8n_response: Dict[str, Any], description: str) -> str:
	"""Send JD matching results to frontend via WebSocket and return session ID"""
	try:
		# Import WebSocket manager
		from app.modules.chat.routes.v1.chat_route import websocket_manager

		# Create matching session in database
		enhanced_data = await _create_matching_session(conversation_id, user_id, n8n_response, description)
		session_id = enhanced_data.get('session_id')

		# Format matching message for frontend
		matching_message = {
			'type': 'jd_matching_data',
			'data': enhanced_data.get('matching_data', n8n_response),
			'conversation_id': conversation_id,
			'session_id': session_id,
			'description': description,
			'timestamp': datetime.now().isoformat(),
		}

		# Send via WebSocket if user is connected
		if user_id and user_id in websocket_manager.active_connections:
			print(f'[_send_matching_results_to_frontend] Sending matching data via WebSocket to user: {user_id}')
			await websocket_manager.send_message(user_id, matching_message)
			print('[_send_matching_results_to_frontend] Matching data sent successfully via WebSocket')
		else:
			logger.warning(f'[_send_matching_results_to_frontend] User {user_id} not connected to WebSocket')

		return session_id

	except Exception as e:
		logger.error(f'[_send_matching_results_to_frontend] Error sending matching data: {str(e)}')
		# Don't raise - this is not critical, the N8N call was successful
		return None


async def _create_matching_session(conversation_id: str, user_id: str, matching_data: Dict[str, Any], description: str) -> Dict[str, Any]:
	"""Create matching session in database for the JD matching results"""
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

			# Handle matching session creation
			result = await integration_service.handle_survey_generation(
				conversation_id=conversation_id,
				user_id=user_id,
				survey_data=[{
					'type': 'jd_matching',
					'description': description,
					'matching_data': matching_data,
					'timestamp': datetime.now().isoformat(),
				}],
				description=f'JD Matching Analysis: {description}',
			)

			print(f'[_create_matching_session] Matching session created: {result.get("session_id")}')
			return {
				'session_id': result.get('session_id'),
				'matching_data': matching_data,
				'description': description,
			}

		finally:
			db.close()

	except Exception as e:
		logger.error(f'[_create_matching_session] Error creating matching session: {str(e)}')
		# Return original data if session creation fails
		return {
			'conversation_id': conversation_id,
			'matching_data': matching_data,
			'description': description,
			'error': str(e),
		}


def get_jd_matching_tool(db_session: Session = None):
	"""Factory function để tạo JD matching tool instance"""
	print('[get_jd_matching_tool] Creating JD matching tool')
	return trigger_jd_matching_tool


__all__ = ['trigger_jd_matching_tool', 'get_jd_matching_tool'] 