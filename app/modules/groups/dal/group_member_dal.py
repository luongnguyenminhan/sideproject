"""Group member data access layer"""

import logging
from typing import List, Optional
from datetime import datetime

from pytz import timezone
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.base_dal import BaseDAL
from app.core.base_model import Pagination
from app.enums.base_enums import Constants
from app.modules.groups.models.group_member import (
	GroupMember,
	GroupMemberRole,
	GroupMemberJoinStatus,
)
from app.utils.filter_utils import apply_dynamic_filters


class GroupMemberDAL(BaseDAL[GroupMember]):
	"""GroupMemberDAL for database operations on group members"""

	def __init__(self, db: Session):
		"""Initialize the GroupMemberDAL

		Args:
		    db (Session): Database session
		"""
		super().__init__(db, GroupMember)

	def get_group_member(self, group_id: str, user_id: str) -> Optional[GroupMember]:
		"""Get a group member by group ID and user ID

		Args:
		    group_id (str): Group ID
		    user_id (str): User ID

		Returns:
		    Optional[GroupMember]: Group member if found, None otherwise
		"""
		return (
			self.db.query(GroupMember)
			.filter(
				and_(
					GroupMember.group_id == group_id,
					GroupMember.user_id == user_id,
					GroupMember.is_deleted == False,
				)
			)
			.first()
		)

	def get_group_members(self, group_id: str, search_params: dict = None) -> Pagination[GroupMember]:
		"""Get all members of a group with pagination

		Args:
		    group_id (str): Group ID
		    search_params (dict, optional): Search parameters. Defaults to None.

		Returns:
		    Pagination[GroupMember]: Paginated list of group members
		"""
		search_params = search_params or {}
		page = int(search_params.get('page', 1))
		page_size = int(search_params.get('page_size', Constants.PAGE_SIZE))

		# Query members of the group
		query = self.db.query(GroupMember).filter(and_(GroupMember.group_id == group_id, GroupMember.is_deleted == False))

		# Apply join status filter if provided
		if 'join_status' in search_params:
			query = query.filter(GroupMember.join_status == search_params['join_status'])

		# Apply role filter if provided
		if 'role' in search_params:
			query = query.filter(GroupMember.role == search_params['role'])

		# Apply dynamic filters
		query = apply_dynamic_filters(query, GroupMember, search_params)

		# Count total
		total_count = query.count()

		# Apply pagination
		members = query.order_by(GroupMember.create_date.desc()).offset((page - 1) * page_size).limit(page_size).all()

		return Pagination(items=members, total_count=total_count, page=page, page_size=page_size)

	def get_invitation_status(self, group_id: str, user_id: str, search_params: dict = None) -> Pagination[GroupMember]:
		"""Get the invitation status for a user in a group

		Args:
		    user_id (str): User ID

		Returns:
		    GroupMember: Invitation status for the user in the group
		"""
		search_params = search_params or {}
		page = int(search_params.get('page', 1))
		page_size = int(search_params.get('page_size', Constants.PAGE_SIZE))

		# Query members of the group
		query = self.db.query(GroupMember).filter(
			and_(
				GroupMember.group_id == group_id,
				GroupMember.user_id == user_id,
				GroupMember.is_deleted == False,
			)
		)

		# Apply dynamic filters
		query = apply_dynamic_filters(query, GroupMember, search_params)

		# Count total
		total_count = query.count()

		# Apply pagination
		members = query.order_by(GroupMember.create_date.desc()).offset((page - 1) * page_size).limit(page_size).all()

		return Pagination(items=members, total_count=total_count, page=page, page_size=page_size)

	def update_join_status(self, member_id: str, status: GroupMemberJoinStatus) -> Optional[GroupMember]:
		"""Update the join status of a group member

		Args:
		    member_id (str): Group member ID
		    status (GroupMemberJoinStatus): New join status

		Returns:
		    Optional[GroupMember]: Updated group member if found and updated, None otherwise
		"""
		member: GroupMember = self.get_by_id(member_id)
		if not member:
			return None

		member.join_status = status
		member.responded_at = datetime.now(timezone('Asia/Ho_Chi_Minh'))

		self.db.commit()
		self.db.refresh(member)

		return member

	def is_user_leader(self, group_id: str, user_id: str) -> bool:
		"""Check if a user is a leader of a group

		Args:
		    group_id (str): Group ID
		    user_id (str): User ID

		Returns:
		    bool: True if user is a leader, False otherwise
		"""
		member = self.get_group_member(group_id, user_id)
		if not member:
			return False

		return member.role == GroupMemberRole.LEADER and member.join_status == GroupMemberJoinStatus.ACCEPTED

	def is_user_accepted_member(self, group_id: str, user_id: str) -> bool:
		"""Check if a user is an accepted member of a group

		Args:
		    group_id (str): Group ID
		    user_id (str): User ID

		Returns:
		    bool: True if user is an accepted member, False otherwise
		"""
		member = self.get_group_member(group_id, user_id)
		if not member:
			return False

		return member.join_status == GroupMemberJoinStatus.ACCEPTED
