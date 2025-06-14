from typing import List, Optional
from app.exceptions.exception import CustomHTTPException
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.core.base_repo import BaseRepo
from app.modules.groups.dal.group_dal import GroupDAL, GroupMemberDAL, GroupRequestDAL
from app.modules.groups.models.groups import Group, GroupMember, GroupRequest
from app.modules.groups.schemas.groups import (
    GroupCreate, GroupUpdate, InviteMemberRequest, JoinGroupRequest,
    ApproveRequestRequest, UpdateNicknameRequest, GroupMemberFilter,
    GroupRequestFilter, BulkInviteRequest
)
from app.enums.group_enums import GroupMemberRoleEnum, GroupRequestType, GroupRequestStatus

logger = logging.getLogger(__name__)
class GroupRepo(BaseRepo):
    """Group Repository"""
    
    def __init__(self, db: Session):
        self.db = db
        self.group_dal = GroupDAL(db)
        self.member_dal = GroupMemberDAL(db)
        self.request_dal = GroupRequestDAL(db)
    
    # Group CRUD Operations
    def create_group(self, group_data: GroupCreate, leader_id: str) -> Group:
        """Tạo group mới"""
        try:
            return self.group_dal.create_group(
                group_name=group_data.group_name,
                leader_id=leader_id,
                group_picture=group_data.group_picture
            )
        except Exception as ex:
            logger.error(f"Error creating group: {ex}")
            
    
    def get_group_by_id(self, group_id: str) -> Optional[Group]:
        """Lấy group theo ID"""
        try:
            group = self.group_dal.get_group_by_id(group_id)
            if not group:
                raise CustomHTTPException(message='Group not found')
            return group
        except Exception as ex:
            logger.error(f"Error retrieving group: {ex}")
            raise ex
    
    def update_group(self, group_id: str, group_data: GroupUpdate, updater_id: str) -> Group:
        """Cập nhật thông tin group"""
        try:
            group = self.get_group_by_id(group_id)
            
            # Kiểm tra quyền cập nhật
            if not self.member_dal.is_leader(group_id, updater_id):
                raise CustomHTTPException(message="Only leader can update group information")
            
            # Cập nhật các field có giá trị
            if group_data.group_name is not None:
                group.group_name = group_data.group_name
            if group_data.group_picture is not None:
                group.group_picture = group_data.group_picture
                
            self.db.commit()
            self.db.refresh(group)
            return group
        except Exception as ex:
            logger.error(f"Error updating group: {ex}")
            raise ex
    
    def delete_group(self, group_id: str, deleter_id: str) -> bool:
        """Xóa group"""
        try:
            group = self.get_group_by_id(group_id)
            
            # Chỉ leader gốc mới có thể xóa group
            if group.leader != deleter_id:
                raise CustomHTTPException(message="Only leader can delete the group")
            
            # Xóa tất cả members và requests liên quan
            members = self.member_dal.get_group_members(group_id)
            for member in members:
                self.member_dal.remove_member(group_id, member.user_id)
                
            # Xóa group
            self.db.delete(group)
            self.db.commit()
            return True
        except Exception as ex:
            logger.error(f"Error deleting group: {ex}")
            raise ex
    
    # Member Management
    def invite_member(self, group_id: str, invite_data: InviteMemberRequest, inviter_id: str) -> GroupRequest:
        """Mời thành viên vào group"""
        try:
            # Kiểm tra group tồn tại
            self.get_group_by_id(group_id)
            
            # Kiểm tra người mời có quyền không
            if not self.member_dal.is_leader(group_id, inviter_id):
                raise CustomHTTPException(message='Only the leader can invite members')
            
            # Kiểm tra user đã là member chưa
            if self.member_dal.is_member(group_id, invite_data.user_id):
                raise CustomHTTPException(message='User is already a member')
            
            # Kiểm tra đã có pending invite chưa
            existing_requests = self.request_dal.get_user_pending_requests(invite_data.user_id)
            for req in existing_requests:
                if req.group_id == group_id and req.request_type == GroupRequestType.INVITE:
                    raise CustomHTTPException(message="User already has a pending invitation")
            
            return self.request_dal.create_invite_request(
                group_id, invite_data.user_id, inviter_id, invite_data.message
            )
        except Exception as ex:
            logger.error(f"Error inviting member: {ex}")
            raise ex
        
    
    def request_join(self, group_id: str, join_data: JoinGroupRequest, user_id: str) -> GroupRequest:
        """Request tham gia group"""
        try:
            # Kiểm tra group tồn tại
            self.get_group_by_id(group_id)
            
            # Kiểm tra user đã là member chưa
            if self.member_dal.is_member(group_id, user_id):
                raise CustomHTTPException(message="User is already a member")
            
            # Kiểm tra đã có pending join request chưa
            existing_requests = self.request_dal.get_user_pending_requests(user_id)
            for req in existing_requests:
                if req.group_id == group_id and req.request_type == GroupRequestType.JOIN:
                    raise CustomHTTPException(message="User already has a pending join request")
            
            return self.request_dal.create_join_request(group_id, user_id, join_data.message)
        except Exception as ex:
            logger.error(f"Error creating join request: {ex}")
            raise ex
    
    def approve_request(self, request_id: str, approve_data: ApproveRequestRequest, approver_id: str) -> GroupMember:
        """Duyệt request tham gia/mời vào group"""
        try:
            request = self.request_dal.get_request_by_id(request_id)
            if not request:
                raise CustomHTTPException(message="Request not found")
            
            if request.status != GroupRequestStatus.PENDING:
                raise CustomHTTPException(message="Request is no longer pending")
            
            # Kiểm tra người duyệt có quyền không
            if request.request_type == GroupRequestType.JOIN:
                if not self.member_dal.is_leader(request.group_id, approver_id):
                    raise CustomHTTPException(message="Only leaders can approve join requests")
            elif request.request_type == GroupRequestType.INVITE:
                # Chỉ user được mời mới có thể accept
                if request.user_id != approver_id:
                    raise CustomHTTPException(message="Only the invited user can accept invitations")
            
            # Kiểm tra user chưa phải member
            if self.member_dal.is_member(request.group_id, request.user_id):
                raise CustomHTTPException(message="User is already a member")
            
            # Approve request
            approved_request = self.request_dal.approve_request(request_id, approver_id)
            if not approved_request:
                raise CustomHTTPException(message="Cannot approve request")
            
            # Thêm user vào group
            return self.member_dal.add_member(
                group_id=request.group_id,
                user_id=request.user_id,
                nickname=approve_data.nickname,
                invited_by=request.requested_by
            )
        except Exception as ex:
            logger.error(f"Error approving request: {ex}")
            raise ex
    
    def reject_request(self, request_id: str, rejecter_id: str) -> GroupRequest:
        """Từ chối request"""
        try:
            request = self.request_dal.get_request_by_id(request_id)
            if not request:
                raise CustomHTTPException(message="Request not found")
            
            if request.status != GroupRequestStatus.PENDING:
                raise CustomHTTPException(message="Request is no longer pending")
            
            # Kiểm tra quyền từ chối
            if request.request_type == GroupRequestType.JOIN:
                if not self.member_dal.is_leader(request.group_id, rejecter_id):
                    raise CustomHTTPException(message="Only leaders can reject join requests")
            elif request.request_type == GroupRequestType.INVITE:
                # User có thể từ chối lời mời của chính họ
                if request.user_id != rejecter_id:
                    raise CustomHTTPException(message="Can only reject your own invitations")
            
            rejected_request = self.request_dal.reject_request(request_id, rejecter_id)
            if not rejected_request:
                raise CustomHTTPException(message="Cannot reject request")
            
            return rejected_request
        except Exception as ex:
            logger.error(f"Error rejecting request: {ex}")
            raise ex
    
    def cancel_request(self, request_id: str, user_id: str) -> GroupRequest:
        """Hủy request của chính mình"""
        try:
            request = self.request_dal.get_request_by_id(request_id)
            if not request:
                raise CustomHTTPException(message="Request not found")
            
            if request.status != GroupRequestStatus.PENDING:
                raise CustomHTTPException(message="Request is no longer pending")
            
            # Chỉ có thể hủy request của chính mình
            if request.requested_by != user_id:
                raise CustomHTTPException(message="Can only cancel your own requests")
            
            cancelled_request = self.request_dal.cancel_request(request_id)
            if not cancelled_request:
                raise CustomHTTPException(message="Cannot cancel request")
            
            return cancelled_request
        except Exception as ex:
            logger.error(f"Error cancelling request: {ex}")
            raise ex
    
    def leave_group(self, group_id: str, user_id: str) -> bool:
        """Rời khỏi group"""
        try:
            # Kiểm tra group tồn tại
            self.get_group_by_id(group_id)
            
            # Kiểm tra user có phải member không
            if not self.member_dal.is_member(group_id, user_id):
                raise CustomHTTPException(message="User is not a member of this group")
            
            # Kiểm tra nếu là leader cuối cùng thì không được rời
            if self.member_dal.is_leader(group_id, user_id):
                leaders = self.member_dal.get_group_leaders(group_id)
                if len(leaders) <= 1:
                    raise CustomHTTPException(message="Cannot leave group as the last leader")
            
            return self.member_dal.remove_member(group_id, user_id)
        except Exception as ex:
            logger.error(f"Error leaving group: {ex}")
            raise ex
    
    def kick_member(self, group_id: str, user_id: str, kicker_id: str) -> bool:
        """Đá thành viên ra khỏi group"""
        try:
            # Kiểm tra group tồn tại
            self.get_group_by_id(group_id)
            
            # Kiểm tra người đá có quyền không
            if not self.member_dal.is_leader(group_id, kicker_id):
                raise CustomHTTPException(message="Only leaders can kick members")
            
            # Kiểm tra target có phải member không
            if not self.member_dal.is_member(group_id, user_id):
                raise CustomHTTPException(message="User is not a member of this group")
            
            # Không được đá leader khác
            if self.member_dal.is_leader(group_id, user_id):
                raise CustomHTTPException(message="Cannot kick another leader")
            
            # Không được tự đá mình
            if user_id == kicker_id:
                raise CustomHTTPException(message="Cannot kick yourself")
            
            return self.member_dal.remove_member(group_id, user_id)
        except Exception as ex:
            logger.error(f"Error kicking member: {ex}")
            raise ex
    
    def promote_to_leader(self, group_id: str, user_id: str, promoter_id: str) -> GroupMember:
        """Phong user lên làm leader"""
        try:
            # Kiểm tra group tồn tại
            self.get_group_by_id(group_id)
            
            # Kiểm tra người phong có quyền không
            if not self.member_dal.is_leader(group_id, promoter_id):
                raise CustomHTTPException(message="Only leaders can promote members")
            
            # Kiểm tra user có phải member không
            if not self.member_dal.is_member(group_id, user_id):
                raise CustomHTTPException(message="User is not a member of this group")
            
            # Kiểm tra user đã là leader chưa
            if self.member_dal.is_leader(group_id, user_id):
                raise CustomHTTPException(message="User is already a leader")
            
            member = self.member_dal.promote_to_leader(group_id, user_id)
            if not member:
                raise CustomHTTPException(message="Member not found")
            return member
        except Exception as ex:
            logger.error(f"Error promoting member to leader: {ex}")
            raise ex
    
    def update_nickname(self, group_id: str, user_id: str, nickname_data: UpdateNicknameRequest) -> GroupMember:
        """Cập nhật nickname trong group"""
        try:
            # Kiểm tra group tồn tại
            self.get_group_by_id(group_id)
            
            # Kiểm tra user có phải member không
            if not self.member_dal.is_member(group_id, user_id):
                raise CustomHTTPException(message="User is not a member of this group")
            
            member = self.member_dal.update_nickname(group_id, user_id, nickname_data.nickname)
            if not member:
                raise CustomHTTPException(message="Member not found")
            return member
        except Exception as ex:
            logger.error(f"Error updating nickname: {ex}")
            raise ex
    
    # Bulk Operations
    def bulk_invite_members(self, group_id: str, bulk_data: BulkInviteRequest, inviter_id: str) -> dict:
        """Mời nhiều thành viên cùng lúc"""
        try:
            # Kiểm tra group tồn tại
            self.get_group_by_id(group_id)
            
            # Kiểm tra người mời có quyền không
            if not self.member_dal.is_leader(group_id, inviter_id):
                raise CustomHTTPException(message="Only leaders can invite members")
            
            successful_invites = []
            failed_invites = []
            
            for user_id in bulk_data.user_ids:
                try:
                    # Kiểm tra user đã là member chưa
                    if self.member_dal.is_member(group_id, user_id):
                        failed_invites.append({
                            "user_id": user_id,
                            "reason": "User is already a member"
                        })
                        continue
                    
                    # Tạo invite request
                    request = self.request_dal.create_invite_request(
                        group_id, user_id, inviter_id, bulk_data.message
                    )
                    successful_invites.append(request)
                    
                except Exception as e:
                    logger.error(f"Error inviting member {user_id}: {e}")
                    failed_invites.append({
                        "user_id": user_id,
                        "reason": str(e)
                    })
            
            return {
                "successful_invites": successful_invites,
                "failed_invites": failed_invites,
                "successful_count": len(successful_invites),
                "failed_count": len(failed_invites)
            }
        except Exception as ex:
            logger.error(f"Error performing bulk invite: {ex}")
            raise ex
    
    # Query Methods
    def get_group_members(self, group_id: str, filters: Optional[GroupMemberFilter] = None) -> List[GroupMember]:
        """Lấy danh sách thành viên trong group với filter"""
        try:
            # Kiểm tra group tồn tại
            self.get_group_by_id(group_id)
            
            members = self.member_dal.get_group_members(group_id)
            
            # Áp dụng filters nếu có
            if filters:
                if filters.role:
                    members = [m for m in members if m.role == filters.role]
                if filters.search:
                    search_term = filters.search.lower()
                    members = [m for m in members if 
                            (m.nickname and search_term in m.nickname.lower()) or
                            search_term in m.user_id.lower()]
            
            return members
        except Exception as ex:
            logger.error(f"Error getting group members: {ex}")
            raise ex
    
    def get_user_groups(self, user_id: str) -> List[Group]:
        """Lấy danh sách group của user"""
        try:
            return self.group_dal.get_user_groups(user_id)
        except Exception as ex:
            logger.error(f"Error getting user groups: {ex}")
            raise CustomHTTPException(message=f"Failed to get user groups: {str(ex)}")
    
    def get_pending_requests(self, group_id: str, filters: Optional[GroupRequestFilter] = None) -> List[GroupRequest]:
        """Lấy danh sách request pending của group với filter"""
        try:
            # Kiểm tra group tồn tại
            self.get_group_by_id(group_id)
            
            requests = self.request_dal.get_pending_requests(group_id)
            
            # Áp dụng filters nếu có
            if filters:
                if filters.request_type:
                    requests = [r for r in requests if r.request_type == filters.request_type]
                if filters.status:
                    requests = [r for r in requests if r.status == filters.status]
            
            return requests
        except Exception as ex:
            logger.error(f"Error getting pending requests: {ex}")
            raise ex
    
    def get_user_pending_requests(self, user_id: str, filters: Optional[GroupRequestFilter] = None) -> List[GroupRequest]:
        """Lấy danh sách request pending của user với filter"""
        try:
            requests = self.request_dal.get_user_pending_requests(user_id)
            
            # Áp dụng filters nếu có
            if filters:
                if filters.request_type:
                    requests = [r for r in requests if r.request_type == filters.request_type]
                if filters.status:
                    requests = [r for r in requests if r.status == filters.status]
            
            return requests
        except Exception as ex:
            logger.error(f"Error getting user pending requests: {ex}")
            raise ex
    
    # Statistics
    def get_group_stats(self, group_id: str) -> dict:
        """Lấy thống kê group"""
        try:
            # Kiểm tra group tồn tại
            self.get_group_by_id(group_id)
            
            members = self.member_dal.get_group_members(group_id)
            leaders = self.member_dal.get_group_leaders(group_id)
            pending_requests = self.request_dal.get_pending_requests(group_id)
            
            return {
                "total_members": len(members),
                "total_leaders": len(leaders),
                "pending_requests": len(pending_requests),
                "recent_joins": 0  # TODO: Implement recent joins logic
            }
        except Exception as ex:
            logger.error(f"Error getting group stats: {ex}")
            raise ex