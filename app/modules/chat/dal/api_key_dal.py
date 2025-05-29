from sqlalchemy.orm import Session
from app.core.base_dal import BaseDAL
from app.modules.chat.models.api_key import ApiKey
from typing import List, Optional


class ApiKeyDAL(BaseDAL[ApiKey]):
    def __init__(self, db: Session):
        print(
            f"\033[96m[ApiKeyDAL.__init__] Initializing ApiKeyDAL with db session: {db}\033[0m"
        )
        super().__init__(db, ApiKey)
        print(f"\033[92m[ApiKeyDAL.__init__] ApiKeyDAL initialized successfully\033[0m")

    def get_user_api_keys(self, user_id: str) -> List[ApiKey]:
        """Get all API keys for a user"""
        print(
            f"\033[93m[ApiKeyDAL.get_user_api_keys] Getting API keys for user_id: {user_id}\033[0m"
        )
        api_keys = (
            self.db.query(self.model)
            .filter(self.model.user_id == user_id, self.model.is_deleted == False)
            .all()
        )
        print(
            f"\033[92m[ApiKeyDAL.get_user_api_keys] Found {len(api_keys)} API keys for user\033[0m"
        )
        return api_keys

    def get_user_api_key_by_provider(self, user_id: str, provider: str) -> List[ApiKey]:
        """Get API keys for a specific provider"""
        print(
            f"\033[93m[ApiKeyDAL.get_user_api_key_by_provider] Getting API keys for user: {user_id}, provider: {provider}\033[0m"
        )
        api_keys = (
            self.db.query(self.model)
            .filter(
                self.model.user_id == user_id,
                self.model.provider == provider,
                self.model.is_deleted == False,
            )
            .all()
        )
        print(
            f"\033[92m[ApiKeyDAL.get_user_api_key_by_provider] Found {len(api_keys)} API keys for provider: {provider}\033[0m"
        )
        return api_keys

    def get_user_default_api_key(self, user_id: str, provider: str) -> Optional[ApiKey]:
        """Get default API key for a provider"""
        print(
            f"\033[93m[ApiKeyDAL.get_user_default_api_key] Getting default API key for user: {user_id}, provider: {provider}\033[0m"
        )
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
        if api_key:
            print(
                f"\033[92m[ApiKeyDAL.get_user_default_api_key] Found default API key: {api_key.id}, key_name: {api_key.key_name}\033[0m"
            )
        else:
            print(
                f"\033[95m[ApiKeyDAL.get_user_default_api_key] No default API key found for provider: {provider}\033[0m"
            )
        return api_key

    def get_user_api_key_by_id(self, key_id: str, user_id: str) -> Optional[ApiKey]:
        """Get API key by ID for a specific user"""
        print(
            f"\033[93m[ApiKeyDAL.get_user_api_key_by_id] Getting API key by ID: {key_id} for user: {user_id}\033[0m"
        )
        api_key = (
            self.db.query(self.model)
            .filter(
                self.model.id == key_id,
                self.model.user_id == user_id,
                self.model.is_deleted == False,
            )
            .first()
        )
        if api_key:
            print(
                f"\033[92m[ApiKeyDAL.get_user_api_key_by_id] Found API key: {api_key.key_name}, provider: {api_key.provider}, is_default: {api_key.is_default}\033[0m"
            )
        else:
            print(
                f"\033[95m[ApiKeyDAL.get_user_api_key_by_id] API key not found: {key_id}\033[0m"
            )
        return api_key

    def clear_default_for_provider(self, user_id: str, provider: str):
        """Clear default flag for all keys of a provider"""
        print(
            f"\033[93m[ApiKeyDAL.clear_default_for_provider] Clearing default flags for user: {user_id}, provider: {provider}\033[0m"
        )
        result = (
            self.db.query(self.model)
            .filter(
                self.model.user_id == user_id,
                self.model.provider == provider,
                self.model.is_deleted == False,
            )
            .update({"is_default": False})
        )
        print(
            f"\033[92m[ApiKeyDAL.clear_default_for_provider] Cleared default flag for {result} API keys\033[0m"
        )
