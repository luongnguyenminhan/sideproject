from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.base_repo import BaseRepo
from app.modules.groups.dal.group_dal import GroupDAL, GroupMemberDAL, GroupRequestDAL
from app.modules.groups.models.groups import Group, GroupMember, GroupRequest
from app.modules.groups.schemas.group_schemas import GroupCreate, GroupUpdate, NicknameUpdate
from app.enums.group_enums import GroupMemberRoleEnum, GroupRequestType, GroupRequestStatus

class GroupRepo(BaseRepo):
    """Group Repository"""
    
    def __init__(self, db: Session):
        self.db = db
        self.group_dal = GroupDAL(db)
        self.member_dal = GroupMemberDAL(db)
        self.request_dal = GroupRequestDAL(db)
        
    def create_group(self, group_data: GroupCreate, leader_id: str) -> Group:
        """Tạo group mới"""
        return self.group_dal.create_group(group_name=group_data.group_name,
        
        )