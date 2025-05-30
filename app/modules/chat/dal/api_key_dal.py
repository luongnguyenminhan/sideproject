from sqlalchemy.orm import Session
from app.core.base_dal import BaseDAL
from app.modules.chat.models.api_key import ApiKey
from typing import List, Optional


class ApiKeyDAL(BaseDAL[ApiKey]):
	def __init__(self, db: Session):
		super().__init__(db, ApiKey)

	def get_user_api_keys(self, user_id: str) -> List[ApiKey]:
		"""Get all API keys for a user"""
		api_keys = self.db.query(self.model).filter(self.model.user_id == user_id, self.model.is_deleted == False).all()
		return api_keys

	def get_user_api_key_by_provider(self, user_id: str, provider: str) -> List[ApiKey]:
		"""Get API keys for a specific provider"""
		api_keys = (
			self.db.query(self.model)
			.filter(
				self.model.user_id == user_id,
				self.model.provider == provider,
				self.model.is_deleted == False,
			)
			.all()
		)
		return api_keys

	def get_user_default_api_key(self, user_id: str, provider: str) -> Optional[ApiKey]:
		"""Get default API key for a provider"""
		api_key = (
			self.db.query(self.model)
			.filter(
				self.model.user_id == user_id,
				self.model.provider == provider,
				self.model.is_default == True,
				self.model.is_deleted == False,
			)
			.first()
		)
		return api_key

	def get_user_api_key_by_id(self, key_id: str, user_id: str) -> Optional[ApiKey]:
		"""Get API key by ID for a specific user"""
		api_key = (
			self.db.query(self.model)
			.filter(
				self.model.id == key_id,
				self.model.user_id == user_id,
				self.model.is_deleted == False,
			)
			.first()
		)

		return api_key

	def clear_default_for_provider(self, user_id: str, provider: str):
		"""Clear default flag for all keys of a provider"""
		result = (
			self.db.query(self.model)
			.filter(
				self.model.user_id == user_id,
				self.model.provider == provider,
				self.model.is_deleted == False,
			)
			.update({'is_default': False})
		)
