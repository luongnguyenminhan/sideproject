"""User model"""

from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy.orm import validates, relationship

from app.core.base_model import BaseEntity
from app.enums.user_enums import UserRoleEnum


class User(BaseEntity):
	"""User model"""

	__tablename__ = 'users'
	profile_picture = Column(String(255), nullable=True)
	username = Column(String(100), nullable=True)
	email = Column(String(100), unique=True, nullable=False)
	name = Column(String(255), nullable=True)
	first_name = Column(String(255), nullable=True)
	last_name = Column(String(255), nullable=True)
	locale = Column(String(20), nullable=True)
	google_id = Column(String(255), nullable=True)
	role = Column(Enum(UserRoleEnum), nullable=False, default=UserRoleEnum.USER)
	confirmed = Column(Boolean, nullable=False, default=True)
	fcm_token = Column(String(255), nullable=True)
	last_login_at = Column(DateTime(timezone=True), nullable=True)

	# Chat system relationships
	conversations = relationship('Conversation', back_populates='user', cascade='all, delete-orphan')
	messages = relationship('Message', back_populates='user', cascade='all, delete-orphan')
	files = relationship('File', back_populates='user', cascade='all, delete-orphan')

	# User logs relationship
	user_logs = relationship('UserLog', back_populates='user', cascade='all, delete-orphan')

	# Agent relationship (if users can own agents)
	agents = relationship('Agent', back_populates='user', cascade='all, delete-orphan')

	@validates('email')
	def validate_email(self, key, address):
		if not address or '@' not in address:
			raise ValueError('Invalid email address')
		return address

	@validates('username')
	def validate_username(self, key, username):
		if username and len(username) < 3:
			raise ValueError('Username must be at least 3 characters long')
		return username

	def to_dict(self):
		"""Convert model to dictionary with role properly serialized"""
		result = super().to_dict()
		# Ensure role is serialized as a string value
		if self.role:
			result['role'] = self.role.value
		return result
