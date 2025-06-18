"""Group model"""

from sqlalchemy import Boolean, Column, DateTime, Enum, String, Integer, ForeignKey
from sqlalchemy.orm import validates, relationship
from datetime import datetime, timezone

from app.core.base_model import BaseEntity
from app.enums.group_enums import GroupMemberRoleEnum, GroupRequestType, GroupRequestStatus

class Group(BaseEntity):
    """Group entity"""
    __tablename__ = 'groups'
    group_picture = Column(String(255), nullable = True)
    group_name = Column(String(100), nullable = False)
    leader = Column(String(36), ForeignKey("users.id"))
    create_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    requests = relationship("GroupRequest", back_populates="group", cascade="all, delete-orphan")

class GroupRequest(BaseEntity):
    """Group request entity"""
    __tablename__ = 'group_requests'
    
    group_id = Column(String(36), ForeignKey("groups.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    request_type = Column(Enum(GroupRequestType), nullable=False)
    status = Column(Enum(GroupRequestStatus), nullable=False, default=GroupRequestStatus.PENDING)
    message = Column(String(500), nullable=True)
    requested_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    requested_at = Column(DateTime, default=datetime.now(timezone.utc))
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    group = relationship("Group", back_populates="requests", foreign_keys=[group_id])
    user = relationship("User", foreign_keys=[user_id], back_populates="group_requests")
    requester = relationship("User", foreign_keys=[requested_by], back_populates="requested_group_requests")
    processor = relationship("User", foreign_keys=[processed_by], back_populates="processed_group_requests")

class GroupMember(BaseEntity):
    """Group member entity"""
    
    __tablename__ = 'group_members'
    group_id = Column(String(36), ForeignKey("groups.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    nickname = Column(String(255))
    role = Column(Integer, nullable = False, default=GroupMemberRoleEnum.MEMBER)
    invited_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    requested_at = Column(DateTime, default=datetime.now(timezone.utc))

    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="group_memberships")
    inviter = relationship("User", foreign_keys=[invited_by], back_populates="invited_group_memberships")

# In your User model, you should add:
# group_memberships = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")
# group_requests = relationship("GroupRequest", back_populates="user", foreign_keys="[GroupRequest.user_id]")
# requested_group_requests = relationship("GroupRequest", back_populates="requester", foreign_keys="[GroupRequest.requested_by]")
# processed_group_requests = relationship("GroupRequest", back_populates="processor", foreign_keys="[GroupRequest.processed_by]")
# invited_group_memberships = relationship("GroupMember", back_populates="inviter", foreign_keys="[GroupMember.invited_by]")