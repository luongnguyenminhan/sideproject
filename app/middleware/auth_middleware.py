"""Auth Middleware"""

from datetime import datetime

from fastapi import Request
from jwt import DecodeError, ExpiredSignatureError  # type: ignore
from pytz import timezone
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import SECRET_KEY, TOKEN_AUDIENCE, TOKEN_ISSUER
from app.exceptions.exception import UnauthorizedException
from app.middleware.translation_manager import _
from app.utils.generate_jwt import GenerateJWToken


def verify_token(request: Request):
	"""
	Xác minh JWT token và trích xuất thông tin người dùng.
	"""
	auth_header = request.headers.get('Authorization')
	if not auth_header or not auth_header.startswith('Bearer '):
		raise UnauthorizedException(message=_(_('token_verification_failed')))

	try:
		token = auth_header.split('Bearer ')[1]
		jwt_generator = GenerateJWToken()
		payload = jwt_generator.decode_token(token, SECRET_KEY, TOKEN_ISSUER, TOKEN_AUDIENCE)
		exp = payload.get('exp')
		if exp and datetime.fromtimestamp(exp, tz=timezone('Asia/Ho_Chi_Minh')) < datetime.now(timezone('Asia/Ho_Chi_Minh')):
			raise UnauthorizedException()

		return payload  # Trả về dữ liệu người dùng từ token

	except ExpiredSignatureError as exp_error:
		raise UnauthorizedException(_('token_expired')) from exp_error
	except DecodeError as decode_error:
		raise UnauthorizedException(_('invalid_token')) from decode_error
	except Exception as e:
		raise UnauthorizedException(_('token_verification_failed')) from e


def verify_admin(request: Request):
	"""
	Xác minh quyền admin từ JWT token.
	"""
	auth_header = request.headers.get('Authorization')
	if not auth_header or not auth_header.startswith('Bearer '):
		raise UnauthorizedException(message=_(_('token_verification_failed')))
	try:
		token = auth_header.split('Bearer ')[1]
		jwt_generator = GenerateJWToken()
		payload = jwt_generator.decode_token(token, SECRET_KEY, TOKEN_ISSUER, TOKEN_AUDIENCE)
		exp = payload.get('exp')
		if exp and datetime.fromtimestamp(exp, tz=timezone('Asia/Ho_Chi_Minh')) < datetime.now(timezone('Asia/Ho_Chi_Minh')):
			raise UnauthorizedException()
		role = payload.get('role')
		if role != 'admin':
			raise UnauthorizedException(_('admin_access_required'))

		return payload

	except ExpiredSignatureError as exp_error:
		raise UnauthorizedException(_('token_expired')) from exp_error
	except DecodeError as decode_error:
		raise UnauthorizedException(_('invalid_token')) from decode_error
	except Exception as e:
		raise UnauthorizedException(_('token_verification_failed')) from e


class AuthMiddleware(BaseHTTPMiddleware):
	"""AuthMiddleware"""

	async def dispatch(self, request: Request, call_next):
		if request.url.path.startswith('/public'):  # Bỏ qua route public
			return await call_next(request)

		token = request.headers.get('Authorization')
		if not token or not token.startswith('Bearer '):
			raise UnauthorizedException()

		token = token.split('Bearer ')[-1]

		user = verify_token(token)
		if not user:
			raise UnauthorizedException()

		request.state.user = user  # Lưu thông tin user vào request

		return await call_next(request)
