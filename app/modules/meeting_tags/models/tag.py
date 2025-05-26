"""Tag models"""

from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.base_model import BaseEntity


class Tag(BaseEntity):
	"""Tag model for categorizing meetings"""

	__tablename__ = 'tags'

	name = Column(String(255), nullable=False)
	user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
	is_system = Column(Boolean, default=False)

	# Relationships
	meeting_tags = relationship('MeetingTag', back_populates='tag', cascade='all, delete-orphan')


class MeetingTag(BaseEntity):
	"""MeetingTag model for many-to-many relationship between meetings and tags"""

	__tablename__ = 'meeting_tags'

	meeting_id = Column(String(36), ForeignKey('meetings.id'), nullable=False)
	tag_id = Column(String(36), ForeignKey('tags.id'), nullable=False)

	# Relationships
	meeting = relationship('Meeting', back_populates='tags')
	tag = relationship('Tag', back_populates='meeting_tags')
