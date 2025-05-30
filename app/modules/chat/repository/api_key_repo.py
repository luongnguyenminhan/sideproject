from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db
from app.modules.chat.dal.api_key_dal import ApiKeyDAL
from app.exceptions.exception import NotFoundException
from app.middleware.translation_manager import _
import logging

logger = logging.getLogger(__name__)

class ApiKeyRepo:
	def __init__(self, db: Session = Depends(get_db)):
		logger.debug(f'\033[96m[ApiKeyRepo.__init__] Initializing ApiKeyRepo with db session: {db}\033[0m')
		self.db = db
		self.api_key_dal = ApiKeyDAL(db)
		logger.debug(f'\033[92m[ApiKeyRepo.__init__] ApiKeyRepo initialized successfully\033[0m')

	def save_api_key(
		self,
		user_id: str,
		provider: str,
		api_key: str,
		is_default: bool = False,
		key_name: str = None,
	):
		"""Save user's API key for AI services"""
		logger.debug(f'\033[93m[ApiKeyRepo.save_api_key] Starting save_api_key for user_id: {user_id}, provider: {provider}, is_default: {is_default}, key_name: {key_name}\033[0m')

		# If setting as default, clear other default keys for this provider
		if is_default:
			logger.debug(f'\033[94m[ApiKeyRepo.save_api_key] Setting as default, clearing other defaults for provider: {provider}\033[0m')
			with self.api_key_dal.transaction():
				self.api_key_dal.clear_default_for_provider(user_id, provider)
				logger.debug(f'\033[92m[ApiKeyRepo.save_api_key] Cleared default keys for provider: {provider}\033[0m')

		# Create new API key
		api_key_data = {
			'user_id': user_id,
			'provider': provider,
			'is_default': is_default,
			'key_name': key_name or f'{provider.title()} API Key',
		}
		logger.debug(f'\033[96m[ApiKeyRepo.save_api_key] Created api_key_data: {api_key_data}\033[0m')

		with self.api_key_dal.transaction():
			logger.debug(f'\033[94m[ApiKeyRepo.save_api_key] Creating new API key in database\033[0m')
			new_api_key = self.api_key_dal.create(api_key_data)
			logger.debug(f'\033[92m[ApiKeyRepo.save_api_key] Created API key with ID: {new_api_key.id}\033[0m')

			# Encrypt and store the API key
			logger.debug(f'\033[94m[ApiKeyRepo.save_api_key] Encrypting and storing API key\033[0m')
			new_api_key.set_api_key(api_key)
			self.db.commit()
			logger.debug(f'\033[92m[ApiKeyRepo.save_api_key] API key saved and committed successfully\033[0m')

			return new_api_key

	def get_user_api_keys(self, user_id: str):
		"""Get all API keys for a user"""
		logger.debug(f'\033[93m[ApiKeyRepo.get_user_api_keys] Getting API keys for user_id: {user_id}\033[0m')
		api_keys = self.api_key_dal.get_user_api_keys(user_id)
		logger.debug(f'\033[92m[ApiKeyRepo.get_user_api_keys] Found {len(api_keys)} API keys for user\033[0m')
		return api_keys

	def get_user_api_key_by_id(self, key_id: str, user_id: str):
		"""Get API key by ID for a user"""
		logger.debug(f'\033[93m[ApiKeyRepo.get_user_api_key_by_id] Getting API key by ID: {key_id} for user: {user_id}\033[0m')
		api_key = self.api_key_dal.get_user_api_key_by_id(key_id, user_id)
		if not api_key:
			logger.debug(f'\033[91m[ApiKeyRepo.get_user_api_key_by_id] API key not found: {key_id}\033[0m')
			raise NotFoundException(_('api_key_not_found'))
		logger.debug(f'\033[92m[ApiKeyRepo.get_user_api_key_by_id] Found API key: {api_key.id}, provider: {api_key.provider}\033[0m')
		return api_key

	def delete_api_key(self, key_id: str, user_id: str):
		"""Delete an API key"""
		logger.debug(f'\033[93m[ApiKeyRepo.delete_api_key] Deleting API key: {key_id} for user: {user_id}\033[0m')
		# Verify user has access
		api_key = self.get_user_api_key_by_id(key_id, user_id)
		logger.debug(f'\033[94m[ApiKeyRepo.delete_api_key] Verified user access to API key: {api_key.id}\033[0m')

		# Soft delete the API key
		with self.api_key_dal.transaction():
			logger.debug(f'\033[94m[ApiKeyRepo.delete_api_key] Performing soft delete\033[0m')
			self.api_key_dal.delete(key_id)
			logger.debug(f'\033[92m[ApiKeyRepo.delete_api_key] API key deleted successfully\033[0m')

	def set_default_api_key(self, key_id: str, user_id: str):
		"""Set an API key as default for its provider"""
		logger.debug(f'\033[93m[ApiKeyRepo.set_default_api_key] Setting API key as default: {key_id} for user: {user_id}\033[0m')
		api_key = self.get_user_api_key_by_id(key_id, user_id)
		logger.debug(f'\033[94m[ApiKeyRepo.set_default_api_key] Found API key for provider: {api_key.provider}\033[0m')

		with self.api_key_dal.transaction():
			# Clear other default keys for this provider
			logger.debug(f'\033[94m[ApiKeyRepo.set_default_api_key] Clearing other defaults for provider: {api_key.provider}\033[0m')
			self.api_key_dal.clear_default_for_provider(user_id, api_key.provider)

			# Set this key as default
			logger.debug(f'\033[94m[ApiKeyRepo.set_default_api_key] Setting key as default\033[0m')
			updated_key = self.api_key_dal.update(key_id, {'is_default': True})
			logger.debug(f'\033[92m[ApiKeyRepo.set_default_api_key] API key set as default successfully\033[0m')

			return updated_key
