"""Group data access layer"""

import logging
from typing import List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.base_dal import BaseDAL
from app.core.base_model import Pagination
from app.enums.base_enums import Constants
from app.modules.groups.models.group import Group
from app.modules.groups.models.group_member import (
	GroupMember,
	GroupMemberRole,
	GroupMemberJoinStatus,
)
from app.utils.filter_utils import apply_dynamic_filters


class GroupDAL(BaseDAL[Group]):
	"""GroupDAL for database operations on groups"""

	def __init__(self, db: Session):
		"""Initialize the GroupDAL

		Args:
		    db (Session): Database session
		"""
		super().__init__(db, Group)

	def get_group_by_name(self, name: str, user_id: str) -> Optional[Group]:
		"""Get a group by name

		Args:
		    name (str): Group name

		Returns:
		    Optional[Group]: Group if found, None otherwise
		"""
		return (
			self.db.query(Group)
			.filter(
				and_(
					Group.name == name,
					Group.created_by == user_id,
					Group.is_deleted == False,
				)
			)
			.first()
		)

	def get_groups_by_user_id(self, user_id: str, search_params: dict = None) -> Pagination[Group]:
		"""Get all groups a user is a member of

		Args:
		    user_id (str): User ID
		    search_params (dict, optional): Search parameters. Defaults to None.

		Returns:
		    Pagination[Group]: Paginated list of groups
		"""
		search_params = search_params or {}
		page = int(search_params.get('page', 1))
		page_size = int(search_params.get('page_size', Constants.PAGE_SIZE))

		# Query groups through membership
		print(f'User ID: {user_id}')
		print(f'Search Params: {search_params}')
		query = (
			self.db.query(Group)
			.join(GroupMember, and_(GroupMember.group_id == Group.id))
			.filter(
				and_(
					GroupMember.user_id == user_id,
					GroupMember.join_status == GroupMemberJoinStatus.ACCEPTED,
					Group.is_deleted == False,
					GroupMember.is_deleted == True,
				)
			)
			.distinct()
		)

		# Apply dynamic filters
		query = apply_dynamic_filters(query, Group, search_params)

		# Count total
		total_count = query.count()

		# Apply pagination
		groups = query.order_by(Group.create_date.desc()).offset((page - 1) * page_size).limit(page_size).all()

		return Pagination(items=groups, total_count=total_count, page=page, page_size=page_size)

	def get_public_groups(self, search_params: dict = None) -> Pagination[Group]:
		"""Get all public groups

		Args:
		    search_params (dict, optional): Search parameters. Defaults to None.

		Returns:
		    Pagination[Group]: Paginated list of public groups
		"""
		search_params = search_params or {}
		page = int(search_params.get('page', 1))
		page_size = int(search_params.get('page_size', Constants.PAGE_SIZE))

		# Query public groups
		query = self.db.query(Group).filter(
			and_(
				Group.is_public == True,
				Group.is_active == True,
				Group.is_deleted == False,
			)
		)

		# Apply dynamic filters
		query = apply_dynamic_filters(query, Group, search_params)

		# Count total
		total_count = query.count()

		# Apply pagination
		groups = query.order_by(Group.create_date.desc()).offset((page - 1) * page_size).limit(page_size).all()

		return Pagination(items=groups, total_count=total_count, page=page, page_size=page_size)

	def search_groups(self, user_id: str, params: dict = None) -> Pagination[dict]:
		"""Search groups with dynamic filtering and include membership details

		Args:
		    user_id (str): ID of the user performing the search
		    params (dict, optional): Search parameters including:
		        - page: Page number
		        - page_size: Items per page
		        - filters: List of filter objects with field, operator, and value

		Returns:
		    Pagination[dict]: Paginated list of filtered groups with membership details including:
		        - member_id: The ID of the membership record
		        - join_status: The user's join status in the group
		        - member_role: The user's role in the group
		"""
		params = params or {}
		page = int(params.get('page', 1))
		page_size = int(params.get('page_size', Constants.PAGE_SIZE))

		# Base query for groups with membership details
		base_query = (
			self.db.query(Group, GroupMember.id, GroupMember.join_status, GroupMember.role)
			.outerjoin(
				GroupMember,
				and_(
					GroupMember.group_id == Group.id,
					GroupMember.user_id == user_id,
					GroupMember.is_deleted == False,
				),
			)
			.filter(Group.is_deleted == False)
		)

		# Filter for user's groups or public groups
		user_groups_filter = and_(
			GroupMember.user_id == user_id,
		)
		public_groups_filter = Group.is_public == True

		# Combine filters based on include_public parameter
		include_public = params.get('include_public', False)
		if include_public:
			# If include_public is true, fetch user's groups OR public groups
			# This requires a more complex query or multiple queries.
			# For simplicity, we'll adjust the filtering strategy.
			# We will fetch all groups and then determine if they are user's or public.
			# This is not the most efficient way for very large datasets but simplifies the example.
			# A more robust solution might involve UNIONs or separate queries.
			query = base_query.filter(or_(user_groups_filter, public_groups_filter))
		else:
			# Default to user's groups if include_public is not specified or false
			query = base_query.filter(user_groups_filter)

		# Apply dynamic filters from params
		query = apply_dynamic_filters(query, Group, params)  # Assuming apply_dynamic_filters can handle the tuple result

		# Count total records
		total_count = query.count()

		# Apply pagination
		results = query.order_by(Group.create_date.desc()).offset((page - 1) * page_size).limit(page_size).all()

		# Format results
		formatted_groups = []
		for group, member_id, join_status, role in results:
			group_dict = group.__dict__
			group_dict['member_id'] = member_id
			group_dict['join_status'] = join_status
			group_dict['member_role'] = role
			# Keep legacy field for backward compatibility
			group_dict['membership_status'] = join_status
			formatted_groups.append(group_dict)

		return Pagination(
			items=formatted_groups,
			total_count=total_count,
			page=page,
			page_size=page_size,
		)
