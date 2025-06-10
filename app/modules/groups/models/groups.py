"""Group model"""

from sqlalchemy import Boolean, Column, DateTime, Enum, String, Integer, ForeignKey
from sqlalchemy.orm import validates, relationship
from datetime import datetime

from app.core.base_model import BaseEntity
from app.enums.group_enums import GroupMemberRoleEnum, GroupMemberStatus

class Group(BaseEntity):
    """Group entity"""
    
    __tablename__ = 'groups'
    group_picture = Column(String(255), nullable = True)
    group_name = Column(String(100), nullable = False)
    leader = Column(String(100), ForeignKey("users.id"))
    create_at = Column(DateTime, default=datetime.utc)
    
    members = relationship("GroupMember", back_populates="group")
    
class GroupMember(BaseEntity):
    """Group member entity"""
    group_id = Column(Integer, ForeignKey("groups.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    nickname = Column(String(255))
    status = Column(Enum(GroupMemberStatus), nullable=False, default=GroupMemberStatus.PENDING)
    role = Column(Integer, nullable = False, default=GroupMemberRoleEnum.MEMBER)
    invited_by = Column(Integer, ForeignKey("users.email"), nullable=True)
    requested_at = Column(DateTime, default=datetime.utc)

    group = relationship("Group", back_populates="members")

    
    
    