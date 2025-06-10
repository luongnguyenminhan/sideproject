from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.base_dal import BaseDAL
from app.modules.groups.models.groups import Group, GroupMember
from app.enums.group_enums import GroupMemberStatus, GroupMemberRoleEnum

class GroupDAL(BaseDAL[Group]):
    """Group Data Access Layer"""
    
    def __init__(self, db: Session):
        super().__init__(db, Group)
    
    def create_group(self, group_name: str, leader_id: int, group_picture: str = None) -> Group:
        """Tạo group mới"""
        group = Group(
            group_name=group_name,
            leader=leader_id,
            group_picture=group_picture
        )
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        
        # Thêm leader vào group
        leader_member = GroupMember(
            group_id=group.group_id,
            user_id=leader_id,
            status=GroupMemberStatus.ACCEPTED,
            role=GroupMemberRoleEnum.LEADER
        )
        self.db.add(leader_member)
        self.db.commit()
        
        return group
    
    def get_group_by_id(self, group_id: int) -> Optional[Group]:
        """Lấy group theo ID"""
        return self.db.query(Group).filter(Group.group_id == group_id).first()
    
    def get_user_groups(self, user_id: int) -> List[Group]:
        """Lấy danh sách group của user"""
        return (self.db.query(Group)
                .join(GroupMember)
                .filter(and_(
                    GroupMember.user_id == user_id,
                    GroupMember.status == GroupMemberStatus.ACCEPTED
                ))
                .all())

class GroupMemberDAL(BaseDAL[GroupMember]):
    """Group Member Data Access Layer"""
    
    def __init__(self, db: Session):
        super().__init__(db, GroupMember)
    
    def invite_member(self, group_id: int, user_id: int, invited_by: int, nickname: str = None) -> GroupMember:
        """Mời thành viên vào group"""
        member = GroupMember(
            group_id=group_id,
            user_id=user_id,
            nickname=nickname,
            status=GroupMemberStatus.PENDING,
            role=GroupMemberRoleEnum.MEMBER,
            invited_by=invited_by
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member
    
    def request_join(self, group_id: int, user_id: int, nickname: str = None) -> GroupMember:
        """Request tham gia group"""
        member = GroupMember(
            group_id=group_id,
            user_id=user_id,
            nickname=nickname,
            status=GroupMemberStatus.PENDING,
            role=GroupMemberRoleEnum.MEMBER
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member
    
    def accept_invite_or_request(self, group_id: int, user_id: int) -> Optional[GroupMember]:
        """Accept lời mời hoặc duyệt request"""
        member = self.db.query(GroupMember).filter(and_(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
            GroupMember.status == GroupMemberStatus.PENDING
        )).first()
        
        if member:
            member.status = GroupMemberStatus.ACCEPTED
            self.db.commit()
            self.db.refresh(member)
        
        return member
    
    def remove_member(self, group_id: int, user_id: int) -> bool:
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
    
    def promote_to_leader(self, group_id: int, user_id: int) -> Optional[GroupMember]:
        """Phong user lên làm leader"""
        member = self.db.query(GroupMember).filter(and_(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
            GroupMember.status == GroupMemberStatus.ACCEPTED
        )).first()
        
        if member:
            member.role = GroupMemberRoleEnum.LEADER
            self.db.commit()
            self.db.refresh(member)
        
        return member
    
    def update_nickname(self, group_id: int, user_id: int, nickname: str) -> Optional[GroupMember]:
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
    
    def get_group_members(self, group_id: int) -> List[GroupMember]:
        """Lấy danh sách thành viên trong group"""
        return self.db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    
    def get_group_leaders(self, group_id: int) -> List[GroupMember]:
        """Lấy danh sách leader trong group"""
        return self.db.query(GroupMember).filter(and_(
            GroupMember.group_id == group_id,
            GroupMember.role == GroupMemberRoleEnum.LEADER,
            GroupMember.status == GroupMemberStatus.ACCEPTED
        )).all()
    
    def is_member(self, group_id: int, user_id: int) -> bool:
        """Kiểm tra user có phải member không"""
        member = self.db.query(GroupMember).filter(and_(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
            GroupMember.status == GroupMemberStatus.ACCEPTED
        )).first()
        return member is not None
    
    def is_leader(self, group_id: int, user_id: int) -> bool:
        """Kiểm tra user có phải leader không"""
        member = self.db.query(GroupMember).filter(and_(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
            GroupMember.role == GroupMemberRoleEnum.LEADER,
            GroupMember.status == GroupMemberStatus.ACCEPTED
        )).first()
        return member is not None