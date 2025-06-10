"""Group model"""

from sqlalchemy import Boolean, Column, DateTime, Enum, String, Integer, ForeignKey
from sqlalchemy.orm import validates, relationship
from datetime import datetime, timezone

from app.core.base_model import BaseEntity
from app.enums.group_enums import GroupMemberRoleEnum, GroupMemberStatus, GroupRequestType, GroupRequestStatus

class Group(BaseEntity):
    """Group entity"""
    __tablename__ = 'groups'
    group_picture = Column(String(255), nullable = True)
    group_name = Column(String(100), nullable = False)
    leader = Column(String(36), ForeignKey("users.id"))
    create_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    members = relationship("GroupMember", back_populates="group")
    
class GroupRequest(BaseEntity):
    """Group request entity"""
    
    __tablename__ = 'group_requests'
    
    group_id = Column(String(36), ForeignKey("groups.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    request_type = Column(Enum(GroupRequestType), nullable=False)
    status = Column(Enum(GroupRequestStatus), nullable=False, default=GroupRequestStatus.PENDING)
    message = Column(String(500), nullable=True)  # Tin nhắn kèm theo request
    requested_by = Column(String(36), ForeignKey("users.id"), nullable=True)  # Người tạo request (cho invite)
    requested_at = Column(DateTime, default=datetime.now(timezone.utc))
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(String(36), ForeignKey("users.id"), nullable=True)  # Người xử lý request
    
    # Relationships
    group = relationship("Group", foreign_keys=[group_id])
    user = relationship("User", foreign_keys=[user_id])
    requester = relationship("User", foreign_keys=[requested_by])
    processor = relationship("User", foreign_keys=[processed_by])
    
class GroupMember(BaseEntity):
    """Group member entity"""
    group_id = Column(String(36), ForeignKey("groups.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    nickname = Column(String(255))
    role = Column(Integer, nullable = False, default=GroupMemberRoleEnum.MEMBER)
    invited_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    requested_at = Column(DateTime, default=datetime.now(timezone.utc))

    group = relationship("Group", back_populates="members")

    
    
    