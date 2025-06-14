from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timezone

from app.core.base_dal import BaseDAL
from app.modules.groups.models.groups import Group, GroupMember, GroupRequest
from app.enums.group_enums import GroupMemberStatus, GroupMemberRoleEnum, GroupRequestType, GroupRequestStatus
import logging
from app.utils.pagination import Pagination
from app.utils.dynamic_filter import apply_dynamic_filters
from app.constants import Constants

class GroupDAL(BaseDAL[Group]):
    """Group Data Access Layer"""
    
    def __init__(self, db: Session):
        super().__init__(db, Group)
    
    def create_group(self, group_name: str, leader_id: str, group_picture: str = None) -> Group:
        """Tạo group mới"""
        group = Group(
            group_name=group_name,
            leader=leader_id,
            group_picture=group_picture
        )
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        
        # Thêm leader vào group_members
        leader_member = GroupMember(
            group_id=group.id,  # Sử dụng id từ BaseEntity
            user_id=leader_id,
            role=GroupMemberRoleEnum.LEADER
        )
        self.db.add(leader_member)
        self.db.commit()
        
        return group
    
    def get_group_by_id(self, group_id: str) -> Optional[Group]:
        """Lấy group theo ID"""
        return self.db.query(Group).filter(Group.id == group_id).first()
    
    def get_user_groups(self, user_id: str) -> List[Group]:
        """Lấy danh sách group của user"""
        return (self.db.query(Group)
                .join(GroupMember)
                .filter(GroupMember.user_id == user_id)
                .all())

    def search_groups(self, params: dict) -> Pagination[Group]:
        """Search groups with dynamic filters based on any Group model field"""

        logger = logging.getLogger(__name__)
        logger.info(f'Searching groups with parameters: {params}')
        page = int(params.get('page', 1))
        page_size = int(params.get('page_size', Constants.PAGE_SIZE))

        query = self.db.query(Group)

        # Apply dynamic filters
        query = apply_dynamic_filters(query, Group, params)

        # Sort by creation date descending if available
        if hasattr(Group, "create_date"):
            query = query.order_by(Group.create_date.desc())

        total_count = query.count()
        groups = query.offset((page - 1) * page_size).limit(page_size).all()

        logger.info(f'Found {total_count} groups, returning page {page} with {len(groups)} items')

        return Pagination(items=groups, total_count=total_count, page=page, page_size=page_size)

class GroupMemberDAL(BaseDAL[GroupMember]):
    """Group Member Data Access Layer"""
    
    def __init__(self, db: Session):
        super().__init__(db, GroupMember)
    
    def get_group_members(self, group_id: str) -> List[GroupMember]:
        """Lấy danh sách thành viên trong group"""
        return self.db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    
    def get_group_leaders(self, group_id: str) -> List[GroupMember]:
        """Lấy danh sách leader trong group"""
        return self.db.query(GroupMember).filter(and_(
            GroupMember.group_id == group_id,
            GroupMember.role == GroupMemberRoleEnum.LEADER
        )).all()
    
    def is_member(self, group_id: str, user_id: str) -> bool:
        """Kiểm tra user có phải member không"""
        member = self.db.query(GroupMember).filter(and_(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id
        )).first()
        return member is not None
    
    def is_leader(self, group_id: str, user_id: str) -> bool:
        """Kiểm tra user có phải leader không"""
        member = self.db.query(GroupMember).filter(and_(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
            GroupMember.role == GroupMemberRoleEnum.LEADER
        )).first()
        return member is not None
    
    def add_member(self, group_id: str, user_id: str, nickname: str = None, invited_by: str = None) -> GroupMember:
        """Thêm thành viên vào group"""
        member = GroupMember(
            group_id=group_id,
            user_id=user_id,
            nickname=nickname,
            role=GroupMemberRoleEnum.MEMBER,
            invited_by=invited_by
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member
    
    def remove_member(self, group_id: str, user_id: str) -> bool:
        """Xóa thành viên khỏi group"""
        member = self.db.query(GroupMember).filter(and_(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id
        )).first()
        
        if member:
            self.db.delete(member)
            self.db.commit()
            return True
        return False
    
    def promote_to_leader(self, group_id: str, user_id: str) -> Optional[GroupMember]:
        """Phong user lên làm leader"""
        member = self.db.query(GroupMember).filter(and_(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id
        )).first()
        
        if member:
            member.role = GroupMemberRoleEnum.LEADER
            self.db.commit()
            self.db.refresh(member)
        
        return member
    
    def update_nickname(self, group_id: str, user_id: str, nickname: str) -> Optional[GroupMember]:
        """Cập nhật nickname trong group"""
        member = self.db.query(GroupMember).filter(and_(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id
        )).first()
        
        if member:
            member.nickname = nickname
            self.db.commit()
            self.db.refresh(member)
        
        return member

class GroupRequestDAL(BaseDAL[GroupRequest]):
    """Group Request Data Access Layer"""
    
    def __init__(self, db: Session):
        super().__init__(db, GroupRequest)
    
    def create_invite_request(self, group_id: str, user_id: str, requested_by: str, message: str = None) -> GroupRequest:
        """Tạo lời mời vào group"""
        request = GroupRequest(
            group_id=group_id,
            user_id=user_id,
            request_type=GroupRequestType.INVITE,
            status=GroupRequestStatus.PENDING,
            message=message,
            requested_by=requested_by
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request
    
    def create_join_request(self, group_id: str, user_id: str, message: str = None) -> GroupRequest:
        """Tạo yêu cầu tham gia group"""
        request = GroupRequest(
            group_id=group_id,
            user_id=user_id,
            request_type=GroupRequestType.JOIN,
            status=GroupRequestStatus.PENDING,
            message=message,
            requested_by=user_id  # User tự request
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request
    
    def get_pending_requests(self, group_id: str) -> List[GroupRequest]:
        """Lấy danh sách request pending của group"""
        return self.db.query(GroupRequest).filter(and_(
            GroupRequest.group_id == group_id,
            GroupRequest.status == GroupRequestStatus.PENDING
        )).all()
    
    def get_user_pending_requests(self, user_id: str) -> List[GroupRequest]:
        """Lấy danh sách request pending của user"""
        return self.db.query(GroupRequest).filter(and_(
            GroupRequest.user_id == user_id,
            GroupRequest.status == GroupRequestStatus.PENDING
        )).all()
    
    def approve_request(self, request_id: str, processed_by: str) -> Optional[GroupRequest]:
        """Chấp nhận request"""
        request = self.db.query(GroupRequest).filter(GroupRequest.id == request_id).first()
        
        if request and request.status == GroupRequestStatus.PENDING:
            request.status = GroupRequestStatus.APPROVED
            request.processed_at = datetime.now(timezone.utc)
            request.processed_by = processed_by
            self.db.commit()
            self.db.refresh(request)
        
        return request
    
    def reject_request(self, request_id: str, processed_by: str) -> Optional[GroupRequest]:
        """Từ chối request"""
        request = self.db.query(GroupRequest).filter(GroupRequest.id == request_id).first()
        
        if request and request.status == GroupRequestStatus.PENDING:
            request.status = GroupRequestStatus.REJECTED
            request.processed_by = processed_by
            request.processed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(request)
        
        return request
    
    def cancel_request(self, request_id: str) -> Optional[GroupRequest]:
        """Hủy request"""
        request = self.db.query(GroupRequest).filter(GroupRequest.id == request_id).first()
        
        if request and request.status == GroupRequestStatus.PENDING:
            request.status = GroupRequestStatus.CANCELLED
            self.db.commit()
            self.db.refresh(request)
        
        return request
    
    def get_request_by_id(self, request_id: str) -> Optional[GroupRequest]:
        """Lấy request theo ID"""
        return self.db.query(GroupRequest).filter(GroupRequest.id == request_id).first()