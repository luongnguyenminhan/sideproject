"""Authentication utility functions"""

import logging
from datetime import datetime, timedelta

from pytz import timezone
from fastapi import status

from app.core.config import SECRET_KEY, TOKEN_AUDIENCE, TOKEN_ISSUER
from app.enums.user_enums import UserRoleEnum
from app.exceptions.exception import CustomHTTPException, NotFoundException
from app.middleware.translation_manager import _
from app.utils.generate_jwt import GenerateJWToken

logger = logging.getLogger(__name__)


async def create_and_store_otp(email: str, otp_dal):
	"""Create and store OTP for email verification or password reset

	Args:
	    email (str): User email
	    otp_dal: OTP data access layer

	Returns:
	    str: Generated OTP code
	"""
	from app.utils.otp_utils import OTPUtils

	otp_utils = OTPUtils()
	otp_code = otp_utils.GenerateOTP()

	# Create OTP record with 10 minute expiration
	new_otp = {
		'email': email,
		'otp': otp_code,
		'expired_at': datetime.now(timezone('Asia/Ho_Chi_Minh')) + timedelta(minutes=10),
		'is_used': False,
	}

	# Update any existing unused OTPs for this email
	otp_dal.update_otp_used_by_email(email)

	# Store new OTP
	otp_dal.create(new_otp)

	return otp_code


def log_user_action(user_logs_dal, user_id: str, action: str, details: str):
	"""Log a user action

	Args:
	    user_logs_dal: User logs data access layer
	    user_id (str): User ID
	    action (str): Action performed
	    details (str): Details of the action
	"""
	try:
		if not user_id or user_id == 'None':
			return

		if user_logs_dal:
			log_data = {'user_id': user_id, 'action': action, 'details': details}
			user_logs_dal.create(log_data)
	except Exception as ex:
		# Just log the error, don't raise an exception as logging failure
		# shouldn't affect the main functionality
		logger.error(f'Logging error for user {user_id}: {ex}')


def generate_auth_tokens(user, expires_minutes=None, refresh_days=None):
	"""Generate authentication tokens for a user

	Args:
	    user: User object
	    expires_minutes: Optional minutes until access token expires
	    refresh_days: Optional days until refresh token expires

	Returns:
	    dict: Dictionary with access_token, refresh_token, and token_type
	"""
	from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

	current_time = datetime.now(timezone('Asia/Ho_Chi_Minh'))

	# Prepare claims for the token
	auth_claims = {
		'user_id': str(user.id),
		'email': user.email,
		'role': user.role.value if user.role else UserRoleEnum.USER.value,
	}

	# Generate tokens
	jwt_generator = GenerateJWToken()

	# Use provided values or defaults from config
	token_validity = expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
	refresh_validity = refresh_days or REFRESH_TOKEN_EXPIRE_DAYS

	access_token = jwt_generator.create_token(
		auth_claims=auth_claims,
		secret_key=SECRET_KEY,
		issuer=TOKEN_ISSUER,
		audience=TOKEN_AUDIENCE,
		token_validity_in_minutes=token_validity,
		current_time=current_time,
	)

	refresh_token = jwt_generator.create_refresh_token(
		auth_claims=auth_claims,
		secret_key=SECRET_KEY,
		issuer=TOKEN_ISSUER,
		audience=TOKEN_AUDIENCE,
		refresh_token_validity_in_days=refresh_validity,
		current_time=current_time,
	)

	return {
		'access_token': access_token,
		'refresh_token': refresh_token,
		'token_type': 'bearer',
	}


def verify_refresh_token(refresh_token):
	"""Verify and decode a refresh token

	Args:
	    refresh_token (str): Refresh token to verify

	Returns:
	    dict: Claims from the token

	Raises:
	    CustomHTTPException: If token validation fails
	"""
	jwt_generator = GenerateJWToken()
	try:
		claims = jwt_generator.decode_token(
			refresh_token,
			SECRET_KEY,
			issuer=TOKEN_ISSUER,
			audience=TOKEN_AUDIENCE,
		)
		return claims
	except Exception:
		raise CustomHTTPException(
			message=_('invalid_refresh_token'),
		)


def verify_refresh_token(refresh_token):
	"""Verify and decode a refresh token

	Args:
	    refresh_token (str): Refresh token to verify

	Returns:
	    dict: Claims from the token

	Raises:
	    CustomHTTPException: If token validation fails
	"""
	jwt_generator = GenerateJWToken()
	try:
		claims = jwt_generator.decode_token(
			refresh_token,
			SECRET_KEY,
			issuer=TOKEN_ISSUER,
			audience=TOKEN_AUDIENCE,
		)
		return claims
	except Exception:
		raise CustomHTTPException(
			message=_('invalid_refresh_token'),
		)