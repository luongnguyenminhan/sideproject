"""Authentication repository for Google OAuth"""

import logging
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.base_repo import BaseRepo
from app.core.database import get_db
from app.modules.users.dal.user_dal import UserDAL
from app.modules.users.dal.user_logs_dal import UserLogDAL
from app.modules.users.schemas.users import OAuthUserInfo, RefreshTokenRequest
from app.modules.users.auth.oauth_service import OAuthService

logger = logging.getLogger(__name__)


class AuthenRepo(BaseRepo):
	"""Authentication repository for handling Google OAuth authentication

	This is the main entry point for Google OAuth authentication operations.
	"""

	def __init__(self, db: Session = Depends(get_db)):
		"""Initialize the authentication repository

		Args:
		    db (Session): Database session
		"""
		self.db = db
		self.user_dal = UserDAL(db)
		self.user_logs_dal = UserLogDAL(db)

		# Initialize service
		self._oauth_service = None

	def get_oauth_service(self):
		"""Get or initialize the OAuth service

		Returns:
		    OAuthService: OAuth service instance
		"""
		if not self._oauth_service:
			self._oauth_service = OAuthService(self.user_dal, self.user_logs_dal, self.db)
		return self._oauth_service

	# ----- OAuth Methods -----
	async def refresh_token(self, request: RefreshTokenRequest):
		"""Refresh user access token

		Args:
		    request (RefreshTokenRequest): Request containing refresh token

		Returns:
		    dict: New access token and user information
		"""
		return await self.get_oauth_service().refresh_token(request)

	async def login_with_google(self, user_info: OAuthUserInfo):
		"""Login or register a user with Google OAuth

		Args:
		    user_info (OAuthUserInfo): Google user information

		Returns:
		    dict: User information with tokens including is_new_user flag
		"""
		return await self.get_oauth_service().login_with_google(user_info)

	async def log_oauth_token_revocation(self, user_id: str):
		"""Log OAuth token revocation

		Args:
		    user_id (str): The ID of the user revoking access

		Returns:
		    bool: True if successful
		"""
		return await self.get_oauth_service().log_oauth_token_revocation(user_id)
