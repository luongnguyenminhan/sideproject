"""Notification model"""

from sqlalchemy import Boolean, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.base_model import BaseEntity
from app.enums.meeting_enums import NotificationTypeEnum


class Notification(BaseEntity):
	"""Notification model for user notifications"""

	__tablename__ = 'notifications'

	user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
	meeting_id = Column(String(36), ForeignKey('meetings.id'), nullable=False)
	type = Column(String(50), nullable=False, default=NotificationTypeEnum.NOTE_GENERATED.value)
	content = Column(Text, nullable=False)
	is_read = Column(Boolean, default=False)

	# Relationships
	meeting = relationship('Meeting', back_populates='notifications')
