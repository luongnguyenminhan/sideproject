"""Group member model for storing group membership information"""

import enum
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.base_model import BaseEntity


class GroupMemberRole(str, enum.Enum):
	"""Role enumeration for group members"""

	LEADER = 'LEADER'
	MEMBER = 'MEMBER'


class GroupMemberJoinStatus(str, enum.Enum):
	"""Join status enumeration for group members"""

	PENDING = 'PENDING'
	ACCEPTED = 'ACCEPTED'
	REJECTED = 'REJECTED'


class GroupMember(BaseEntity):
	"""Group member model for managing group memberships"""

	__tablename__ = 'group_members'

	group_id = Column(String(36), ForeignKey('groups.id'), nullable=False)
	user_id = Column(String(36), ForeignKey('users.id'), nullable=True)  # Changed nullable to True
	email_for_invitation = Column(String, nullable=True)  # Added
	invitation_token = Column(String, nullable=True, index=True, unique=True)  # Added
	expires_at = Column(DateTime, nullable=True)  # Added
	role = Column(Enum(GroupMemberRole), nullable=False, default=GroupMemberRole.MEMBER)
	join_status = Column(Enum(GroupMemberJoinStatus), nullable=False, default=GroupMemberJoinStatus.PENDING)
	invited_by = Column(String(36), ForeignKey('users.id'), nullable=True)
	invited_at = Column(DateTime, nullable=False, default=func.now())
	responded_at = Column(DateTime, nullable=True)
	create_date = Column(DateTime, nullable=False, default=func.now())
	update_date = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

	# Relationships
	group = relationship('Group', back_populates='members')
	user = relationship('User', foreign_keys=[user_id])
	inviter = relationship('User', foreign_keys=[invited_by])

	def __repr__(self):
		return f"<GroupMember(id='{self.id}', group_id='{self.group_id}', user_id='{self.user_id}', role='{self.role}')>"
