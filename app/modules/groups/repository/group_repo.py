from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.base_repo import BaseRepo
from app.modules.groups.dal.group_dal import GroupDAL, GroupMemberDAL
from app.modules.groups.models.groups import Group, GroupMember
from app.modules.groups.schemas.group_schemas import GroupCreate, GroupUpdate, NicknameUpdate
from app.enums.group_enums import GroupMemberRoleEnum

class GroupRepo(BaseRepo):
    """Group Repository"""
    
    def __init__(self, db: Session):
        self.db = db
        self.group_dal = GroupDAL(db)
        self.member_dal = GroupMemberDAL(db)
    
    def create_group(self, group_data: GroupCreate, leader_email: str) -> Group:
        """Tạo group mới"""
        return self.group_dal.create_group(
            group_name=group_data.group_name,
            leader_email=leader_email,
            group_picture=group_data.group_picture
        )
    
    def invite_member(self, group_id: int, user_email: str, invited_by: str, nickname: str = None) -> GroupMember:
        """Mời thành viên vào group"""
        # Kiểm tra người mời có quyền không
        if not self.member_dal.is_leader(group_id, invited_by):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only leaders can invite members"
            )
        
        # Kiểm tra user đã là member chưa
        if self.member_dal.is_member(group_id, user_email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member"
            )
        
        return self.member_dal.invite_member(group_id, user_email, invited_by, nickname)
    
    def accept_invite(self, group_id: int, user_email: str) -> GroupMember:
        """Accept lời mời vào group"""
        member = self.member_dal.accept_invite_or_request(group_id, user_email)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )
        return member
    
    def request_join(self, group_id: int, user_email: str, nickname: str = None) -> GroupMember:
        """Request tham gia group"""
        # Kiểm tra user đã là member chưa
        if self.member_dal.is_member(group_id, user_email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member"
            )
        
        return self.member_dal.request_join(group_id, user_email, nickname)
    
    def approve_request(self, group_id: int, user_email: str, approver_email: str) -> GroupMember:
        """Duyệt request tham gia group"""
        # Kiểm tra người duyệt có quyền không
        if not self.member_dal.is_leader(group_id, approver_email):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only leaders can approve requests"
            )
        
        member = self.member_dal.accept_invite_or_request(group_id, user_email)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Join request not found"
            )
        return member
    
    def leave_group(self, group_id: int, user_email: str) -> bool:
        """Rời khỏi group"""
        # Kiểm tra nếu là leader cuối cùng thì không được rời
        if self.member_dal.is_leader(group_id, user_email):
            leaders = self.member_dal.get_group_leaders(group_id)
            if len(leaders) <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot leave group as the last leader"
                )
        
        return self.member_dal.remove_member(group_id, user_email)
    
    def kick_member(self, group_id: int, user_email: str, kicker_email: str) -> bool:
        """Đá thành viên ra khỏi group"""
        # Kiểm tra người đá có quyền không
        if not self.member_dal.is_leader(group_id, kicker_email):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only leaders can kick members"
            )
        
        # Không được đá leader khác
        if self.member_dal.is_leader(group_id, user_email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot kick another leader"
            )
        
        return self.member_dal.remove_member(group_id, user_email)
    
    def promote_to_leader(self, group_id: int, user_email: str, promoter_email: str) -> GroupMember:
        """Phong user lên làm leader"""
        # Kiểm tra người phong có quyền không
        if not self.member_dal.is_leader(group_id, promoter_email):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only leaders can promote members"
            )
        
        member = self.member_dal.promote_to_leader(group_id, user_email)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        return member
    
    def update_nickname(self, group_id: int, user_email: str, nickname_data: NicknameUpdate) -> GroupMember:
        """Cập nhật nickname trong group"""
        member = self.member_dal.update_nickname(group_id, user_email, nickname_data.nickname)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        return member
    
    def get_group_members(self, group_id: int) -> List[GroupMember]:
        """Lấy danh sách thành viên trong group"""
        return self.member_dal.get_group_members(group_id)
    
    def get_user_groups(self, user_email: str) -> List[Group]:
        """Lấy danh sách group của user"""
        return self.group_dal.get_user_groups(user_email)