import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.chat.repository.chat_repo import ChatRepo
from app.http.oauth2 import verify_websocket_token
from app.middleware.websocket_middleware import WebSocketErrorHandler
from app.utils.n8n_api_client import n8n_client
from app.middleware.translation_manager import _

logger = logging.getLogger(__name__)

route = APIRouter(prefix='/chat', tags=['Chat V2'])


class WebSocketManagerV2:
	"""WebSocket manager for V2 chat with N8N direct integration"""

	def __init__(self):
		self.active_connections: dict[str, WebSocket] = {}

	async def connect(self, websocket: WebSocket, user_id: str):
		await websocket.accept()
		self.active_connections[user_id] = websocket

	def disconnect(self, user_id: str):
		if user_id in self.active_connections:
			del self.active_connections[user_id]

	async def send_message(self, user_id: str, message: dict):
		"""Send message to WebSocket client"""
		if user_id in self.active_connections:
			websocket = self.active_connections[user_id]
			try:
				message_str = json.dumps(message)
				await websocket.send_text(message_str)
			except Exception as e:
				logger.error(f'Error sending websocket message: {e}')
				self.disconnect(user_id)


# Global WebSocket manager instance for V2
websocket_manager_v2 = WebSocketManagerV2()


@route.websocket('/ws/{conversation_id}')
async def websocket_chat_v2_endpoint(
	websocket: WebSocket,
	conversation_id: str,
	db: Session = Depends(get_db),
):
	"""WebSocket endpoint V2 for chat with direct N8N integration"""
	user_id = None
	try:
		# Get token from query parameters
		query_params = dict(websocket.query_params)
		token = query_params.get('token')
		authorization_token = query_params.get('authorization_token')

		# Verify WebSocket token
		try:
			if not token:
				await WebSocketErrorHandler.handle_auth_error(websocket, reason='Token required')
				return

			token_data = verify_websocket_token(token)
			user_id = token_data.get('user_id')
			if not user_id:
				await WebSocketErrorHandler.handle_auth_error(websocket, reason='Invalid token')
				return

		except Exception as e:
			logger.error(f'Authentication failed: {e}')
			await WebSocketErrorHandler.handle_auth_error(websocket, reason='Authentication failed')
			return

		chat_repo = ChatRepo(db)

		# Verify user has access to conversation
		try:
			conversation = chat_repo.get_conversation_by_id(conversation_id, user_id)
			if not conversation:
				await WebSocketErrorHandler.handle_forbidden_error(websocket, reason='Conversation not found')
				return
		except Exception as e:
			logger.error(f'Access denied: {e}')
			await WebSocketErrorHandler.handle_forbidden_error(websocket, reason='Access denied to conversation')
			return

		await websocket_manager_v2.connect(websocket, user_id)

		try:
			while True:
				# Receive message from client
				data = await websocket.receive_text()

				try:
					message_data = json.loads(data)
				except json.JSONDecodeError as e:
					logger.error(f'JSON decode error: {e}')
					await websocket_manager_v2.send_message(
						user_id,
						{'type': 'error', 'message': 'Invalid JSON format'},
					)
					continue

				if message_data.get('type') == 'chat_message':
					content = message_data.get('content', '').strip()

					if not content:
						await websocket_manager_v2.send_message(
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
						logger.error(f'Failed to save user message: {e}')
						await websocket_manager_v2.send_message(
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
					await websocket_manager_v2.send_message(user_id, user_message_response)

					# Send typing indicator
					typing_message = {'type': 'assistant_typing', 'status': True}
					await websocket_manager_v2.send_message(user_id, typing_message)

					try:
						# Get AI response from N8N directly
						ai_response = await chat_repo.get_ai_response_from_n8n(
							conversation_id=conversation_id,
							user_message=content,
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
						await websocket_manager_v2.send_message(
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
						logger.error(f'Error getting N8N response: {e}')
						await websocket_manager_v2.send_message(
							user_id,
							{'type': 'error', 'message': _('ai_response_error')},
						)

					finally:
						# Stop typing indicator
						await websocket_manager_v2.send_message(user_id, {'type': 'assistant_typing', 'status': False})

				elif message_data.get('type') == 'ping':
					# Respond to ping
					await websocket_manager_v2.send_message(user_id, {'type': 'pong'})

				else:
					logger.warning(f'Unknown message type: {message_data.get("type")}')

		except WebSocketDisconnect:
			logger.info(f'WebSocket disconnected for user: {user_id}')
	except Exception as e:
		logger.error(f'WebSocket error: {e}')
		try:
			await websocket_manager_v2.send_message(user_id, {'type': 'error', 'message': _('websocket_error')})
		except Exception:
			pass
	finally:
		if user_id:
			websocket_manager_v2.disconnect(user_id)
