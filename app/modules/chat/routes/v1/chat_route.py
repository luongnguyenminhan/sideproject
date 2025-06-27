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

	def disconnect(self, user_id: str):
		if user_id in self.active_connections:
			del self.active_connections[user_id]
		else:
			pass

	async def send_message(self, user_id: str, message: dict):
		if user_id in self.active_connections:
			websocket = self.active_connections[user_id]
			try:
				message_str = json.dumps(message)
				await websocket.send_text(message_str)
			except Exception as e:
				logger.error(f'Error sending message to user {user_id}: {e}')
				self.disconnect(user_id)
		else:
			pass


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

		# Get authorization token for N8N API from headers or query params
		authorization_token = None
		if hasattr(websocket, 'headers'):
			authorization_header = websocket.headers.get('authorization')
			if authorization_header and authorization_header.startswith('Bearer '):
				authorization_token = authorization_header[7:]  # Remove 'Bearer ' prefix

		# Fallback to query parameter if header not available
		if not authorization_token:
			authorization_token = query_params.get('authorization_token')

		# Verify WebSocket token
		try:
			if not token:
				logger.error('WebSocket token missing')
				await WebSocketErrorHandler.handle_auth_error(websocket, reason='Token required')
				return

			token_data = verify_websocket_token(token)

			user_id = token_data.get('user_id')
			if not user_id:
				logger.error('WebSocket token invalid - no user_id')
				await WebSocketErrorHandler.handle_auth_error(websocket, reason='Invalid token')
				return

		except Exception as e:
			logger.error(f'WebSocket token verification failed: {e}')
			await WebSocketErrorHandler.handle_auth_error(websocket, reason='Authentication failed')
			return

		chat_repo = ChatRepo(db)

		# Verify user has access to conversation
		try:
			conversation = chat_repo.get_conversation_by_id(conversation_id, user_id)
		except Exception as e:
			await WebSocketErrorHandler.handle_forbidden_error(websocket, reason='Access denied to conversation')
			return

		await websocket_manager.connect(websocket, user_id)
		try:
			while True:
				# Receive message from client
				data = await websocket.receive_text()

				try:
					message_data = json.loads(data)
				except json.JSONDecodeError as e:
					await websocket_manager.send_message(
						user_id,
						{'type': 'error', 'message': 'Invalid JSON format'},
					)
					continue

				if message_data.get('type') == 'chat_message':
					content = message_data.get('content', '').strip()
					api_key = message_data.get('api_key')

					if not content:
						await websocket_manager.send_message(
							user_id,
							{'type': 'error', 'message': _('message_content_required')},
						)
						continue

					# Create user message
					try:
						user_message = chat_repo.create_message(
							conversation_id=conversation_id,
							user_id=user_id,
							content=content,
							role='user',
						)
					except Exception as e:
						await websocket_manager.send_message(
							user_id,
							{'type': 'error', 'message': 'Failed to save message'},
						)
						continue

					# Send user message confirmation
					await websocket_manager.send_message(
						user_id,
						{
							'type': 'user_message',
							'message': {
								'id': user_message.id,
								'content': content,
								'role': 'user',
								'timestamp': user_message.timestamp.isoformat(),
							},
						},
					)

					# Send typing indicator
					await websocket_manager.send_message(user_id, {'type': 'assistant_typing', 'status': True})

					try:
						# Get AI response with streaming using Agent system
						ai_response = await chat_repo.get_ai_response(
							conversation_id=conversation_id,
							user_message=content,
							api_key=api_key,
							user_id=user_id,
							authorization_token=authorization_token,
						)

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
						logger.error(f'Error getting AI response: {e}')
						await websocket_manager.send_message(
							user_id,
							{'type': 'error', 'message': _('ai_response_error')},
						)

					finally:
						# Stop typing indicator
						await websocket_manager.send_message(user_id, {'type': 'assistant_typing', 'status': False})

				elif message_data.get('type') == 'ping':
					# Respond to ping
					await websocket_manager.send_message(user_id, {'type': 'pong'})
				else:
					pass

		except WebSocketDisconnect:
			pass
		except Exception as e:
			logger.error(f'WebSocket error for user {user_id}: {e}')
			try:
				await websocket_manager.send_message(user_id, {'type': 'error', 'message': _('websocket_error')})
			except:
				pass
		finally:
			if user_id:
				websocket_manager.disconnect(user_id)

	except Exception as e:
		logger.error(f'Fatal WebSocket error: {e}')
		try:
			await WebSocketErrorHandler.handle_auth_error(websocket, 1011, 'Internal server error')
		except:
			pass


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
			logger.info(f'Storing CV context for conversation: {conversation_id}')
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
