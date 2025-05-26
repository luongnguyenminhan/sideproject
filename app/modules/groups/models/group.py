"""Group model for storing group information"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.base_model import BaseEntity


class Group(BaseEntity):
	"""Group model for storing group information"""

	__tablename__ = 'groups'

	name = Column(String(255), nullable=False)
	description = Column(Text, nullable=True)
	created_by = Column(String(36), ForeignKey('users.id'), nullable=False)
	create_date = Column(DateTime, nullable=False, default=func.now())
	update_date = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
	is_active = Column(Boolean, nullable=False, default=True)
	is_public = Column(Boolean, nullable=False, default=False)

	# Relationships
	creator = relationship('User', foreign_keys=[created_by])
	members = relationship('GroupMember', back_populates='group', cascade='all, delete-orphan')
	meetings = relationship('Meeting', back_populates='group')

	def __repr__(self):
		return f"<Group(id='{self.id}', name='{self.name}')>"
