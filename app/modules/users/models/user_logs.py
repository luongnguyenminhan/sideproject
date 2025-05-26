"""User logs model"""

from sqlalchemy import Column, ForeignKey, String, Text

from app.core.base_model import BaseEntity


class UserLog(BaseEntity):
	"""User logs model for tracking user actions"""

	__tablename__ = 'user_logs'

	user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
	action = Column(String(255), nullable=False)
	details = Column(Text, nullable=True)
	ip_address = Column(String(50), nullable=True)
	user_agent = Column(Text, nullable=True)
