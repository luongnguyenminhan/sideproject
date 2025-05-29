from sqlalchemy import Column, String, Text, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.core.base_model import BaseEntity
from cryptography.fernet import Fernet
import os
import enum


class ApiProvider(str, enum.Enum):
	GOOGLE = 'google'


class ApiKey(BaseEntity):
	"""API Key model for storing encrypted AI service keys"""

	__tablename__ = 'api_keys'

	user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
	provider = Column(Enum(ApiProvider), nullable=False)
	encrypted_key = Column(Text, nullable=False)
	is_default = Column(Boolean, default=False)
	key_name = Column(String(100), nullable=True)

	# Relationships
	user = relationship('User', back_populates='api_keys')

	def set_api_key(self, api_key: str):
		"""Encrypt and store API key"""
		key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
		if isinstance(key, str):
			key = key.encode()
		f = Fernet(key)
		self.encrypted_key = f.encrypt(api_key.encode()).decode()

	def get_api_key(self) -> str:
		"""Decrypt and return API key"""
		key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
		if isinstance(key, str):
			key = key.encode()
		f = Fernet(key)
		return f.decrypt(self.encrypted_key.encode()).decode()

	@property
	def masked_key(self) -> str:
		"""Return masked version of API key for display"""
		try:
			original_key = self.get_api_key()
			if len(original_key) <= 8:
				return '*' * len(original_key)
			return original_key[:4] + '*' * (len(original_key) - 8) + original_key[-4:]
		except:
			return '****-****-****'
