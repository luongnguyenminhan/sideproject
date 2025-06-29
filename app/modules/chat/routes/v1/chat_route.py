import json
from fastapi import (
	APIRouter,
	Depends,
	Form,
	WebSocket,
	WebSocketDisconnect,
	UploadFile,
	File,
)
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.enums.base_enums import BaseErrorCode
from app.modules.chat.repository.chat_repo import ChatRepo
from app.modules.chat.schemas.chat_request import SendMessageRequest
from app.modules.chat.schemas.chat_response import SendMessageResponse
from app.core.base_model import APIResponse
from app.exceptions.handlers import handle_exceptions
from app.http.oauth2 import get_current_user, verify_websocket_token
from app.middleware.translation_manager import _
from app.exceptions.exception import ValidationException
from app.middleware.websocket_middleware import WebSocketErrorHandler
from app.modules.chat.services.cv_integration_service import CVIntegrationService
import logging

logger = logging.getLogger(__name__)

route = APIRouter(prefix='/chat', tags=['Chat'])


class WebSocketManager:
	"""Manage WebSocket connections for chat"""

	def __init__(self):
		self.active_connections: dict[str, WebSocket] = {}

	async def connect(self, websocket: WebSocket, user_id: str):
		await websocket.accept()
		self.active_connections[user_id] = websocket
		logger.info(f'[WebSocketManager] ✅ Connected user {user_id}, total connections: {len(self.active_connections)}')

	def disconnect(self, user_id: str):
		if user_id in self.active_connections:
			del self.active_connections[user_id]
			logger.info(f'[WebSocketManager] 🔌 Disconnected user {user_id}, remaining connections: {len(self.active_connections)}')
		else:
			logger.warning(f'[WebSocketManager] ⚠️ Attempted to disconnect non-existent user: {user_id}')

	async def send_message(self, user_id: str, message: dict):
		"""Send message to WebSocket client with comprehensive logging"""
		if user_id in self.active_connections:
			websocket = self.active_connections[user_id]
			try:
				message_str = json.dumps(message)
				message_type = message.get('type', 'unknown')
				
				# Log the outgoing message with details
				logger.info(f'[WebSocketManager] 📤 SENDING to user {user_id}:')
				logger.info(f'[WebSocketManager] 📤   Message type: {message_type}')
				logger.info(f'[WebSocketManager] 📤   Message size: {len(message_str)} chars')
				
				# Log content preview based on message type
				if message_type == 'user_message':
					content = message.get('message', {}).get('content', '')
					logger.info(f'[WebSocketManager] 📤   User message content preview: {content[:100]}...' + (' (truncated)' if len(content) > 100 else ''))
				elif message_type == 'assistant_message_complete':
					content = message.get('message', {}).get('content', '')
					model = message.get('message', {}).get('model_used', 'unknown')
					response_time = message.get('message', {}).get('response_time_ms', 'unknown')
					logger.info(f'[WebSocketManager] 📤   Assistant message content preview: {content[:100]}...' + (' (truncated)' if len(content) > 100 else ''))
					logger.info(f'[WebSocketManager] 📤   Model used: {model}, Response time: {response_time}ms')
				elif message_type == 'assistant_typing':
					status = message.get('status', False)
					logger.info(f'[WebSocketManager] 📤   Typing indicator: {"ON" if status else "OFF"}')
				elif message_type == 'error':
					error_msg = message.get('message', 'Unknown error')
					logger.info(f'[WebSocketManager] 📤   Error message: {error_msg}')
				elif message_type in ['ping', 'pong']:
					logger.info(f'[WebSocketManager] 📤   Heartbeat: {message_type}')
				else:
					logger.info(f'[WebSocketManager] 📤   Message keys: {list(message.keys())}')
				
				await websocket.send_text(message_str)
				logger.info(f'[WebSocketManager] ✅ Message sent successfully to user {user_id}')
				
			except Exception as e:
				logger.error(f'[WebSocketManager] ❌ Error sending message to user {user_id}: {e}')
				logger.error(f'[WebSocketManager] ❌ Message that failed: {message.get("type", "unknown")} type')
				self.disconnect(user_id)
		else:
			logger.warning(f'[WebSocketManager] ⚠️ Cannot send message to user {user_id}: Not connected')
			logger.warning(f'[WebSocketManager] ⚠️ Active connections: {list(self.active_connections.keys())}')


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


@route.post('/websocket/token', response_model=APIResponse)
@handle_exceptions
async def get_websocket_token(
	current_user: dict = Depends(get_current_user),
):
	"""Generate WebSocket token for authentication"""
	from app.http.oauth2 import create_websocket_token

	user_id = current_user.get('user_id')
	email = current_user.get('email')
	role = current_user.get('role', 'user')

	# Create token with all required user data
	user_data = {'user_id': user_id, 'email': email, 'role': role}

	token = create_websocket_token(user_data)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('websocket_token_generated'),
		data={'token': token, 'expires_in': 3600},
	)


@route.websocket('/ws/{conversation_id}')
async def websocket_chat_endpoint(
	websocket: WebSocket,
	conversation_id: str,
	db: Session = Depends(get_db),
):
	"""WebSocket endpoint for real-time chat messaging"""

	user_id = None
	try:
		# Get token from query parameters
		query_params = dict(websocket.query_params)
		token = query_params.get('token')

		# Get authorization token for N8N API from query params
		authorization_token = query_params.get('authorization_token')
		
		# 🔍 LOG: WebSocket connection attempt
		logger.info(f'[WebSocket] 🚀 CONNECTION ATTEMPT')
		logger.info(f'[WebSocket] 📝 Conversation ID: {conversation_id}')
		logger.info(f'[WebSocket] 🔑 Query params: {list(query_params.keys())}')
		logger.info(f'[WebSocket] 🎫 Token available: {bool(token)}')
		logger.info(f'[WebSocket] 🔐 Authorization token available: {bool(authorization_token)}')
		if authorization_token:
			logger.info(f'[WebSocket] 🔐 Authorization token (first 20 chars): {authorization_token[:20]}...')

		# Verify WebSocket token
		try:
			if not token:
				logger.error('[WebSocket] ❌ TOKEN ERROR: WebSocket token missing')
				await WebSocketErrorHandler.handle_auth_error(websocket, reason='Token required')
				return

			logger.info('[WebSocket] 🔍 Verifying WebSocket token...')
			token_data = verify_websocket_token(token)

			user_id = token_data.get('user_id')
			if not user_id:
				logger.error('[WebSocket] ❌ TOKEN ERROR: Invalid token - no user_id found')
				await WebSocketErrorHandler.handle_auth_error(websocket, reason='Invalid token')
				return
			
			logger.info(f'[WebSocket] ✅ TOKEN VERIFIED: User ID = {user_id}')

		except Exception as e:
			logger.error(f'[WebSocket] ❌ TOKEN VERIFICATION FAILED: {str(e)}')
			await WebSocketErrorHandler.handle_auth_error(websocket, reason='Authentication failed')
			return

		chat_repo = ChatRepo(db)

		# Verify user has access to conversation
		try:
			logger.info(f'[WebSocket] 🔍 Verifying access to conversation: {conversation_id}')
			conversation = chat_repo.get_conversation_by_id(conversation_id, user_id)
			logger.info(f'[WebSocket] ✅ CONVERSATION ACCESS VERIFIED: {conversation.name if hasattr(conversation, "name") else "Unnamed"}')
		except Exception as e:
			logger.error(f'[WebSocket] ❌ ACCESS DENIED: {str(e)}')
			await WebSocketErrorHandler.handle_forbidden_error(websocket, reason='Access denied to conversation')
			return

		logger.info(f'[WebSocket] 🔗 CONNECTING WebSocket for user: {user_id}')
		await websocket_manager.connect(websocket, user_id)
		logger.info(f'[WebSocket] ✅ CONNECTION ESTABLISHED successfully')
		try:
			while True:
				# Receive message from client
				logger.info('[WebSocket] 📬 WAITING for client message...')
				data = await websocket.receive_text()
				logger.info(f'[WebSocket] 📨 RECEIVED RAW DATA: {data[:200]}...' + (' (truncated)' if len(data) > 200 else ''))

				try:
					message_data = json.loads(data)
					logger.info(f'[WebSocket] 📦 PARSED MESSAGE: Type={message_data.get("type")}, Keys={list(message_data.keys())}')
				except json.JSONDecodeError as e:
					logger.error(f'[WebSocket] ❌ JSON DECODE ERROR: {str(e)}')
					logger.info('[WebSocket] 📤 SENDING ERROR response for invalid JSON')
					await websocket_manager.send_message(
						user_id,
						{'type': 'error', 'message': 'Invalid JSON format'},
					)
					continue

				if message_data.get('type') == 'chat_message':
					content = message_data.get('content', '').strip()
					api_key = message_data.get('api_key')
					
					logger.info(f'[WebSocket] 💬 CHAT MESSAGE received:')
					logger.info(f'[WebSocket] 💬   Content length: {len(content)} chars')
					logger.info(f'[WebSocket] 💬   Content preview: {content[:100]}...' + (' (truncated)' if len(content) > 100 else ''))
					logger.info(f'[WebSocket] 💬   API key provided: {bool(api_key)}')

					if not content:
						logger.warning('[WebSocket] ⚠️ EMPTY CONTENT: Sending error response')
						await websocket_manager.send_message(
							user_id,
							{'type': 'error', 'message': _('message_content_required')},
						)
						continue

					# Create user message
					try:
						logger.info('[WebSocket] 💾 CREATING user message in database...')
						user_message = chat_repo.create_message(
							conversation_id=conversation_id,
							user_id=user_id,
							content=content,
							role='user',
						)
						logger.info(f'[WebSocket] ✅ USER MESSAGE SAVED: ID={user_message.id}')
					except Exception as e:
						logger.error(f'[WebSocket] ❌ FAILED to save user message: {str(e)}')
						await websocket_manager.send_message(
							user_id,
							{'type': 'error', 'message': 'Failed to save message'},
						)
						continue

					# Send user message confirmation
					user_message_response = {
						'type': 'user_message',
						'message': {
							'id': user_message.id,
							'content': content,
							'role': 'user',
							'timestamp': user_message.timestamp.isoformat(),
						},
					}
					await websocket_manager.send_message(user_id, user_message_response)

					# Send typing indicator
					typing_message = {'type': 'assistant_typing', 'status': True}
					await websocket_manager.send_message(user_id, typing_message)

					try:
						# Get AI response with streaming using Agent system
						# Pass authorization token to AI service
						logger.info('[WebSocket] 🤖 STARTING AI response generation...')
						logger.info(f'[WebSocket] 🤖   Conversation ID: {conversation_id}')
						logger.info(f'[WebSocket] 🤖   User ID: {user_id}')
						logger.info(f'[WebSocket] 🤖   Authorization token available: {bool(authorization_token)}')
						logger.info(f'[WebSocket] 🤖   API key provided: {bool(api_key)}')
						
						ai_response = await chat_repo.get_ai_response(
							conversation_id=conversation_id,
							user_message=content,
							api_key=api_key,
							user_id=user_id,
							authorization_token=authorization_token,  # Pass authorization token
						)
						
						logger.info(f'[WebSocket] ✅ AI RESPONSE received:')
						logger.info(f'[WebSocket] ✅   Content length: {len(ai_response.get("content", ""))} chars')
						logger.info(f'[WebSocket] ✅   Model used: {ai_response.get("model_used")}')
						logger.info(f'[WebSocket] ✅   Response time: {ai_response.get("response_time_ms")}ms')

						# Create AI message in database
						ai_message = chat_repo.create_message(
							conversation_id=conversation_id,
							user_id=user_id,
							content=ai_response['content'],
							role='assistant',
							model_used=ai_response.get('model_used'),
							tokens_used=json.dumps(ai_response.get('usage', {})),
							response_time_ms=str(ai_response.get('response_time_ms', 0)),
						)

						# Send final message confirmation
						await websocket_manager.send_message(
							user_id,
							{
								'type': 'assistant_message_complete',
								'message': {
									'id': ai_message.id,
									'content': ai_message.content,
									'role': 'assistant',
									'timestamp': ai_message.timestamp.isoformat(),
									'model_used': ai_message.model_used,
									'response_time_ms': ai_message.response_time_ms,
								},
							},
						)

					except Exception as e:
						logger.error(f'[WebSocket] ❌ Error getting AI response: {e}')
						await websocket_manager.send_message(
							user_id,
							{'type': 'error', 'message': _('ai_response_error')},
						)

					finally:
						# Stop typing indicator
						await websocket_manager.send_message(user_id, {'type': 'assistant_typing', 'status': False})
						
				elif message_data.get('type') == 'ping':
					logger.info('[WebSocket] 🏓 PING received, responding with PONG')
					# Respond to ping
					await websocket_manager.send_message(user_id, {'type': 'pong'})
					
				else:
					message_type = message_data.get('type', 'unknown')
					logger.warning(f'[WebSocket] ⚠️ UNKNOWN MESSAGE TYPE: {message_type}')
					logger.warning(f'[WebSocket] ⚠️ Message keys: {list(message_data.keys())}')

		except WebSocketDisconnect:
			logger.info(f'[WebSocket] 🔌 CLIENT DISCONNECTED: User {user_id} closed connection')
	except Exception as e:
		logger.error(f'[WebSocket] ❌ UNEXPECTED ERROR for user {user_id}: {e}')
		logger.error(f'[WebSocket] ❌ Error type: {type(e).__name__}')
		try:
			await websocket_manager.send_message(user_id, {'type': 'error', 'message': _('websocket_error')})
		except Exception as send_error:
			logger.error(f'[WebSocket] ❌ Failed to send error message to user {user_id}: {send_error}')
	finally:
		if user_id:
			logger.info(f'[WebSocket] 🧹 CLEANUP: Disconnecting user {user_id}')
			websocket_manager.disconnect(user_id)
		else:
			logger.warning('[WebSocket] 🧹 CLEANUP: No user_id available for cleanup')


@route.post('/send-message', response_model=APIResponse)
@handle_exceptions
async def send_message(
	request: SendMessageRequest,
	db: Session = Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	"""Send a chat message (non-streaming alternative)"""
	chat_repo = ChatRepo(db)
	user_id = current_user.get('user_id')

	try:
		# Verify user has access to conversation
		conversation = chat_repo.get_conversation_by_id(request.conversation_id, user_id)
		logger.debug(f'Verified access to conversation: {conversation.id}')

		# Create user message
		user_message = chat_repo.create_message(
			conversation_id=request.conversation_id,
			user_id=user_id,
			content=request.content,
			role='user',
		)

		# Get AI response using Agent system (non-streaming)
		ai_response = await chat_repo.get_ai_response(
			conversation_id=request.conversation_id,
			user_message=request.content,
			api_key=request.api_key,
			user_id=user_id,
		)

		# Create AI message
		ai_message = chat_repo.create_message(
			conversation_id=request.conversation_id,
			user_id=user_id,
			content=ai_response['content'],
			role='assistant',
			model_used=ai_response.get('model_used'),
			tokens_used=json.dumps(ai_response.get('usage', {})),
			response_time_ms=str(ai_response.get('response_time_ms', 0)),
		)

		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
			message=_('message_sent_successfully'),
			data=SendMessageResponse(
				user_message=user_message.dict(include_relationships=False),
				ai_message=ai_message.dict(include_relationships=False),
			),
		)

	except ValidationException:
		# Re-raise validation exceptions
		raise
	except Exception as e:
		logger.error(f'Error in send_message: {e}')
		raise ValidationException(_('failed_to_send_message'))


@route.get('/files/{file_id}/download', response_model=APIResponse)
@handle_exceptions
async def get_file_download_url(
	file_id: str,
	expires: int = 3600,
	db: Session = Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	"""Get temporary download URL for file in chat context"""
	from app.modules.chat.repository.file_repo import FileRepo

	file_repo = FileRepo(db)
	user_id = current_user.get('user_id')
	download_url = file_repo.get_file_download_url(file_id, user_id, expires)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('download_url_generated'),
		data={'download_url': download_url, 'expires_in': expires},
	)


@route.post('/upload-cv', response_model=APIResponse)
@handle_exceptions
async def upload_cv_for_chat(
	file: UploadFile = File(...),
	conversation_id: str = Form(None),
	db: Session = Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	"""Upload và extract thông tin CV cho chat context"""
	if not conversation_id:
		raise ValidationException(_('conversation_id_required'))

	try:
		user_id = current_user.get('user_id')

		# Validate file type - chỉ accept CV files
		cv_extensions = ['.pdf', '.doc', '.docx']
		if not any(file.filename.lower().endswith(ext) for ext in cv_extensions):
			raise ValidationException(_('invalid_cv_file_type'))

		# Upload file lên MinIO
		from app.utils.minio.minio_handler import minio_handler

		object_path = await minio_handler.upload_fastapi_file(file=file, meeting_id=conversation_id or user_id, file_type='cv_files')

		# Generate download URL for CV extraction
		cv_file_url = minio_handler.get_file_url(object_path, expires=3600)

		# Use cv_extraction module for CV processing
		from app.modules.cv_extraction.repository.cv_repo import CVRepo
		from app.modules.cv_extraction.schemas.cv import ProcessCVRequest

		cv_repo = CVRepo(db)
		cv_request = ProcessCVRequest(cv_file_url=cv_file_url)
		cv_result = await cv_repo.process_cv(cv_request)

		if cv_result.error_code != 0:
			raise ValidationException(cv_result.message)
		# Handle both dictionary and Pydantic model cases
		if isinstance(cv_result.data, dict):
			cv_data = cv_result.data
		else:
			# Convert Pydantic model to dictionary
			cv_data = cv_result.data.model_dump() if hasattr(cv_result.data, 'model_dump') else cv_result.data.dict()

		# Store CV context trong conversation (nếu có)
		if conversation_id:
			cv_service = CVIntegrationService(db)
			logger.info(f'Storing CV context for conversation: {conversation_id} using service: {type(cv_service).__name__}')
			# Extract cv_analysis_result from the ProcessCVResponse
			cv_analysis_data = cv_data.get('cv_analysis_result')
			if hasattr(cv_analysis_data, 'model_dump'):
				cv_analysis_dict = cv_analysis_data.model_dump()
			elif hasattr(cv_analysis_data, 'dict'):
				cv_analysis_dict = cv_analysis_data.dict()
			else:
				cv_analysis_dict = cv_analysis_data

			await cv_service.store_cv_context(conversation_id, user_id, cv_analysis_dict)

		response_file_path = object_path
		response_cv_file_url = cv_data.get('cv_file_url', cv_file_url)
		response_cv_analysis_result = cv_data.get('cv_analysis_result')
		response_personal_info = cv_data.get('personal_info')
		response_skills_count = cv_data.get('skills_count', 0)
		response_experience_count = cv_data.get('experience_count', 0)
		response_cv_summary = cv_data.get('cv_summary', '')

		response_data = {
			'file_path': response_file_path,
			'cv_file_url': response_cv_file_url,
			'cv_analysis_result': response_cv_analysis_result,
			'personal_info': response_personal_info,
			'skills_count': response_skills_count,
			'experience_count': response_experience_count,
			'cv_summary': response_cv_summary,
		}

		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
			message=_('cv_uploaded_successfully'),
			data=response_data,
		)

	except Exception as e:
		logger.error(f'Error uploading CV: {e}')
		raise ValidationException(_('cv_upload_failed'))


@route.get('/conversation/{conversation_id}/cv-metadata', response_model=APIResponse)
@handle_exceptions
async def get_cv_metadata(
	conversation_id: str,
	db: Session = Depends(get_db),
	current_user: dict = Depends(get_current_user),
):
	"""Get CV metadata from conversation"""
	try:
		user_id = current_user.get('user_id')
		cv_service = CVIntegrationService(db)

		# Get conversation và check access
		chat_repo = ChatRepo(db)
		conversation = chat_repo.get_conversation_by_id(conversation_id, user_id)

		if not conversation.extra_metadata:
			return APIResponse(
				error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
				message=_('no_cv_data_found'),
				data=None,
			)

		# Parse metadata
		metadata = json.loads(conversation.extra_metadata)
		cv_context = metadata.get('cv_context')

		if not cv_context or not cv_context.get('cv_uploaded'):
			return APIResponse(
				error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
				message=_('no_cv_data_found'),
				data=None,
			)

		# Return CV data in format compatible với CVModal
		cv_data = {
			'file_path': cv_context.get('file_path', ''),
			'cv_file_url': cv_context.get('cv_file_url', ''),
			'cv_analysis_result': cv_context.get('full_cv_analysis', {}),
			'personal_info': cv_context.get('personal_info', {}),
			'skills_count': cv_context.get('skills_count', len(cv_context.get('skills', []))),
			'experience_count': cv_context.get('experience_count', 0),
			'cv_summary': cv_context.get('cv_summary', ''),
		}

		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
			message=_('cv_metadata_retrieved'),
			data=cv_data,
		)

	except Exception as e:
		logger.error(f'Error getting CV metadata: {e}')
		raise ValidationException(_('failed_to_get_cv_metadata'))
