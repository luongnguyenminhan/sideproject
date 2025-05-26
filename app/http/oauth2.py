from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.config import SECRET_KEY, TOKEN_AUDIENCE, TOKEN_ISSUER
from app.exceptions.exception import UnauthorizedException
from app.middleware.translation_manager import _
from app.utils.generate_jwt import GenerateJWToken

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')


def get_current_user(data: str = Depends(oauth2_scheme)):
	"""
	Trích xuất thông tin người dùng từ JWT token.
	"""
	try:
		jwt_generator = GenerateJWToken()
		payload = jwt_generator.decode_token(data, SECRET_KEY, TOKEN_ISSUER, TOKEN_AUDIENCE)
		return payload
	except Exception as e:
		print(f'Unexpected error in get_current_user: {e}')
		raise UnauthorizedException(_('token_verification_failed')) from e
