"""GroupLog model for storing group audit log information"""

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Boolean
from sqlalchemy.sql import func
import json

from app.core.base_model import BaseEntity


class GroupLog(BaseEntity):
	__tablename__ = 'group_logs'

	group_id = Column(String(36), ForeignKey('groups.id'), nullable=False, index=True)
	user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)  # User performing the action
	action = Column(String(100), nullable=False)
	details = Column(Text, nullable=True)  # JSON string for additional details
	create_date = Column(DateTime, nullable=False, default=func.now())
	update_date = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
	is_deleted = Column(Boolean, nullable=False, default=False)

	def __repr__(self):
		return f"<GroupLog(id='{self.id}', group_id='{self.group_id}', action='{self.action}', user_id='{self.user_id}')>"
