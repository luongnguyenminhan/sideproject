import json
import logging
from fastapi import WebSocket
from typing import Callable, Any
from app.exceptions.exception import ValidationException

logger = logging.getLogger(__name__)


class WebSocketErrorHandler:
	"""Handle WebSocket-specific errors and send appropriate responses"""

	@staticmethod
	async def handle_auth_error(
		websocket: WebSocket,
		error_code: int = 4001,
		reason: str = 'Authentication failed',
	):
		"""Handle authentication errors for WebSocket connections"""
		try:
			# Send error message before closing
			await websocket.send_text(
				json.dumps({
					'type': 'error',
					'error_code': error_code,
					'message': reason,
					'action': 'reconnect_required',
				})
			)
		except Exception:
			pass  # Connection might already be closed
		finally:
			await websocket.close(code=error_code, reason=reason)

	@staticmethod
	async def handle_forbidden_error(websocket: WebSocket, reason: str = 'Access forbidden'):
		"""Handle 403 Forbidden errors for WebSocket connections"""
		try:
			# Send forbidden error message
			await websocket.send_text(
				json.dumps({
					'type': 'error',
					'error_code': 4003,
					'message': reason,
					'action': 'access_denied',
				})
			)
		except Exception:
			pass  # Connection might already be closed
		finally:
			await websocket.close(code=4003, reason=reason)

	@staticmethod
	async def handle_validation_error(websocket: WebSocket, error: ValidationException):
		"""Handle validation errors for WebSocket connections"""
		try:
			await websocket.send_text(
				json.dumps({
					'type': 'error',
					'error_code': 4000,
					'message': str(error),
					'action': 'fix_request',
				})
			)
		except Exception:
			pass
		finally:
			await websocket.close(code=4000, reason=str(error))


async def websocket_error_middleware(websocket: WebSocket, call_next: Callable) -> Any:
	"""Middleware to handle WebSocket errors consistently"""
	try:
		return await call_next()
	except ValidationException as e:
		logger.error(f'WebSocket validation error: {e}')
		await WebSocketErrorHandler.handle_validation_error(websocket, e)
	except PermissionError as e:
		logger.error(f'WebSocket permission error: {e}')
		await WebSocketErrorHandler.handle_forbidden_error(websocket, reason=str(e))
	except Exception as e:
		logger.error(f'WebSocket unexpected error: {e}')
		try:
			await websocket.send_text(
				json.dumps({
					'type': 'error',
					'error_code': 1011,
					'message': 'Internal server error',
					'action': 'retry_later',
				})
			)
		except Exception:
			pass
		finally:
			await websocket.close(code=1011, reason='Internal server error')
