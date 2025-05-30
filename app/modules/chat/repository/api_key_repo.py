from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db
from app.modules.chat.dal.api_key_dal import ApiKeyDAL
from app.exceptions.exception import NotFoundException
from app.middleware.translation_manager import _


class ApiKeyRepo:
	def __init__(self, db: Session = Depends(get_db)):
		self.db = db
		self.api_key_dal = ApiKeyDAL(db)

	def save_api_key(
		self,
		user_id: str,
		provider: str,
		api_key: str,
		is_default: bool = False,
		key_name: str = None,
	):
		"""Save user's API key for AI services"""

		# If setting as default, clear other default keys for this provider
		if is_default:
			with self.api_key_dal.transaction():
				self.api_key_dal.clear_default_for_provider(user_id, provider)

		# Create new API key
		api_key_data = {
			'user_id': user_id,
			'provider': provider,
			'is_default': is_default,
			'key_name': key_name or f'{provider.title()} API Key',
		}

		with self.api_key_dal.transaction():
			new_api_key = self.api_key_dal.create(api_key_data)

			# Encrypt and store the API key
			new_api_key.set_api_key(api_key)
			self.db.commit()

			return new_api_key

	def get_user_api_keys(self, user_id: str):
		"""Get all API keys for a user"""
		api_keys = self.api_key_dal.get_user_api_keys(user_id)
		return api_keys

	def get_user_api_key_by_id(self, key_id: str, user_id: str):
		"""Get API key by ID for a user"""
		api_key = self.api_key_dal.get_user_api_key_by_id(key_id, user_id)
		if not api_key:
			raise NotFoundException(_('api_key_not_found'))
		return api_key

	def delete_api_key(self, key_id: str, user_id: str):
		"""Delete an API key"""
		# Verify user has access
		api_key = self.get_user_api_key_by_id(key_id, user_id)

		# Soft delete the API key
		with self.api_key_dal.transaction():
			self.api_key_dal.delete(key_id)

	def set_default_api_key(self, key_id: str, user_id: str):
		"""Set an API key as default for its provider"""
		api_key = self.get_user_api_key_by_id(key_id, user_id)

		with self.api_key_dal.transaction():
			# Clear other default keys for this provider
			self.api_key_dal.clear_default_for_provider(user_id, api_key.provider)

			# Set this key as default
			updated_key = self.api_key_dal.update(key_id, {'is_default': True})

			return updated_key
