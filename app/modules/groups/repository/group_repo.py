"""Group repository for business logic related to groups"""

import json
import logging
import os
import secrets
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import Depends
from pytz import timezone
from sqlalchemy.orm import Session

from app.core.base_repo import BaseRepo
from app.core.database import get_db
from app.core.base_model import Pagination
from app.modules.groups.dal.group_dal import GroupDAL
from app.modules.groups.dal.group_log_dal import GroupLogDAL
from app.modules.groups.dal.group_member_dal import GroupMemberDAL
from app.modules.groups.models.group import Group
from app.modules.groups.models.group_member import (
	GroupMember,
	GroupMemberRole,
	GroupMemberJoinStatus,
)
from app.exceptions.exception import (
	CustomHTTPException,
	NotFoundException,
	ForbiddenException,
)
from app.middleware.translation_manager import _
from app.modules.groups.schemas.group_schemas import GroupMemberResponse
from app.modules.users.dal.user_dal import UserDAL
from app.modules.users.schemas.users import UserResponse
from app.utils.otp_utils import OTPUtils

logger = logging.getLogger(__name__)


class GroupRepo(BaseRepo):
	"""Repository for Group operations"""

	def __init__(self, db: Session = Depends(get_db)):
		"""Initialize the GroupRepo

		Args:
		    db (Session): Database session
		"""
		self.db = db
		self.group_dal = GroupDAL(db)
		self.group_member_dal = GroupMemberDAL(db)
		self.user_dal = UserDAL(db)
		self.group_log_dal = GroupLogDAL(db)

	def _log_action(
		self,
		group_id: str,
		user_id: str,
		action: str,
		details: Optional[Dict[str, Any]] = None,
	):
		"""Helper function to log group actions."""
		print(f'[AUDIT_LOG] GroupID: {group_id}, UserID: {user_id}, Action: {action}, Details: {details}')
		log_entry = {
			'group_id': group_id,
			'user_id': user_id,
			'action': action,
			'details': json.dumps(details) if details else None,
		}
		# with self.group_log_dal.transaction():
		#     self.group_log_dal.create(log_entry)

	def create_group(self, name: str, description: Optional[str], is_public: bool, user_id: str) -> Group:
		"""Create a new group with the current user as leader

		Args:
		    name (str): Group name
		    description (Optional[str]): Group description
		    is_public (bool): Whether the group is public
		    user_id (str): ID of the user creating the group

		Returns:
		    Group: Created group

		Raises:
		    CustomHTTPException: If a group with the same name already exists
		"""
		print(f'[DEBUG] Creating group: name={name}, is_public={is_public}, user_id={user_id}')

		# Check if group name already exists
		existing_group = self.group_dal.get_group_by_name(name, user_id)
		if existing_group:
			print(f"[DEBUG] Group name '{name}' already exists")
			raise CustomHTTPException(message=_('group_name_exists'))

		# Create the group
		group = {
			'name': name,
			'description': description,
			'is_public': is_public,
			'created_by': user_id,
		}
		print(f'[DEBUG] Group object created: {group["name"]}, {group["description"]}, {group["is_public"]}, {group["created_by"]}')

		with self.group_dal.transaction():
			created_group = self.group_dal.create(group)
			self.group_dal.commit()
			print(f'[DEBUG] Group created: {created_group.id}')
		print(f'[DEBUG] Group created successfully with ID: {created_group.id}')

		# Add creator as leader
		print(f'[DEBUG] Adding user {user_id} as leader of group {created_group.id}')
		self.add_member(
			group_id=created_group.id,
			user_id=user_id,
			role=GroupMemberRole.LEADER,
			join_status=GroupMemberJoinStatus.ACCEPTED,
			invited_by=user_id,
		)
		print(f'[DEBUG] User {user_id} added as leader')

		return created_group

	def update_group(self, group_id: str, update_data: Dict[str, Any], user_id: str) -> Group:
		"""Update a group's information

		Args:
		    group_id (str): ID of the group to update
		    update_data (Dict[str, Any]): Data to update
		    user_id (str): ID of the user making the update

		Returns:
		    Group: Updated group

		Raises:
		    NotFoundException: If the group is not found
		    ForbiddenException: If the user is not a leader of the group
		    CustomHTTPException: If trying to update name to one that already exists
		"""
		print(f'[DEBUG] Updating group: group_id={group_id}, user_id={user_id}')
		print(f'[DEBUG] Update data: {update_data}')

		# Check if group exists
		group = self.group_dal.get_by_id(group_id)
		if not group:
			print(f'[DEBUG] Group {group_id} not found')
			raise NotFoundException(_('group_not_found'))
		print(f'[DEBUG] Group {group_id} found: {group.name}')

		# Check if user is a leader
		is_leader = self.group_member_dal.is_user_leader(group_id, user_id)
		print(f'[DEBUG] User {user_id} is leader of group {group_id}: {is_leader}')
		if not is_leader:
			print(f'[DEBUG] User {user_id} is not a leader of group {group_id}')
			raise ForbiddenException(_('not_group_leader'))

		# Check if updating name to an existing name
		if 'name' in update_data and update_data['name'] != group.name:
			print(f"[DEBUG] Checking if name '{update_data['name']}' already exists")
			existing_group = self.group_dal.get_group_by_name(update_data['name'], user_id)
			if existing_group:
				print(f"[DEBUG] Group name '{update_data['name']}' already exists")
				raise CustomHTTPException(message=_('group_name_exists'))
			print(f"[DEBUG] Group name '{update_data['name']}' is available")

		# Update the group
		print(f'[DEBUG] Updating group {group_id} with data: {update_data}')
		updated_group = self.group_dal.update(group_id, update_data)
		print(f'[DEBUG] Group updated successfully: {updated_group.id}, {updated_group.name}')
		self.group_dal.commit()
		print(f'[DEBUG] Group {updated_group.id} committed successfully')
		return updated_group

	def delete_group(self, group_id: str, user_id: str) -> bool:
		"""Soft delete a group

		Args:
		    group_id (str): ID of the group to delete
		    user_id (str): ID of the user deleting the group

		Returns:
		    bool: True if successful

		Raises:
		    NotFoundException: If the group is not found
		    ForbiddenException: If the user is not a leader of the group
		"""
		# Check if group exists
		group = self.group_dal.get_by_id(group_id)
		if not group:
			raise NotFoundException(_('group_not_found'))

		# Check if user is a leader
		if not self.group_member_dal.is_user_leader(group_id, user_id):
			raise ForbiddenException(_('not_group_leader'))

		# Delete the group (soft delete)
		self.group_dal.update(group_id, {'is_deleted': True})
		print(f'[DEBUG] Group {group_id} marked as deleted')
		self.group_dal.commit()
		return True

	def get_group_by_id(self, group_id: str, user_id: str) -> Group:
		"""Get a group by ID and verify user has access

		Args:
		    group_id (str): ID of the group to get
		    user_id (str): ID of the user requesting the group

		Returns:
		    Group: The requested group

		Raises:
		    NotFoundException: If the group is not found
		    ForbiddenException: If the user doesn't have access to the group
		"""
		# Check if group exists
		group = self.group_dal.get_by_id(group_id)
		if not group:
			raise CustomHTTPException(message=_('group_not_found'))
		if group.is_deleted:
			raise CustomHTTPException(message=_('group_not_found'))

		# If public group, allow access
		if group.is_public:
			return group

		# Check if user is a member
		member = self.group_member_dal.get_group_member(group_id, user_id)
		if not member or member.join_status != GroupMemberJoinStatus.ACCEPTED:
			raise ForbiddenException(_('not_group_member'))

		return group

	def add_member(
		self,
		group_id: str,
		user_id: Optional[str],
		role: GroupMemberRole,
		join_status: GroupMemberJoinStatus,
		invited_by: str,
		email_for_invitation: Optional[str] = None,
		invitation_token: Optional[str] = None,
	) -> GroupMember:
		"""Add a new member to a group or create a pending invitation.

		Args:
		    group_id (str): ID of the group
		    user_id (Optional[str]): ID of the user to add (if exists).
		    role (GroupMemberRole): Role of the new member/invitee.
		    join_status (GroupMemberJoinStatus): Join status (usually PENDING for invites).
		    invited_by (str): ID of the user who invited the new member.
		    email_for_invitation (Optional[str]): Email if user_id is not known (new user).
		    invitation_token (Optional[str]): Secure token for new user invitation link.

		Returns:
		    GroupMember: Created group member or invitation record.

		Raises:
		    NotFoundException: If the group is not found.
		    CustomHTTPException: If the user is already a member (for existing users).
		"""
		print(f'[DEBUG] Adding member/invitation: group_id={group_id}, user_id={user_id}, email={email_for_invitation}, role={role}, join_status={join_status}')

		# Check if group exists
		group = self.group_dal.get_by_id(group_id)
		if not group:
			print(f'[DEBUG] Group {group_id} not found')
			raise NotFoundException(_('group_not_found'))
		print(f'[DEBUG] Group {group_id} found: {group.name}')

		# Check if user is already a member (only if user_id is provided)
		if user_id:
			existing_member = self.group_member_dal.get_group_member(group_id, user_id)
			if existing_member and not existing_member.is_deleted:
				print(f'[DEBUG] User {user_id} is already a member of group {group_id}')
				if existing_member.join_status == GroupMemberJoinStatus.PENDING:
					raise CustomHTTPException(
						status_code=409,
						message=_('User has a pending invitation already.'),
					)
				elif existing_member.join_status == GroupMemberJoinStatus.ACCEPTED:
					raise CustomHTTPException(
						status_code=409,
						message=_('User is already a member of this group.'),
					)
			print(f'[DEBUG] User {user_id} is not already a member of group {group_id}')
		elif email_for_invitation:
			pass

		member_data = {
			'group_id': group_id,
			'user_id': user_id,
			'role': role,
			'join_status': join_status,
			'invited_by': invited_by,
			'invited_at': datetime.now(timezone('Asia/Ho_Chi_Minh')),
			'email_for_invitation': email_for_invitation,
			'invitation_token': invitation_token,
		}

		if join_status == GroupMemberJoinStatus.PENDING:
			member_data['expires_at'] = datetime.now(timezone('Asia/Ho_Chi_Minh')) + timedelta(hours=24)

		print(f'[DEBUG] Creating member/invitation with data: {member_data}')
		with self.group_member_dal.transaction():
			created_member = self.group_member_dal.create(member_data)
			log_action = 'MEMBER_ADDED' if join_status == GroupMemberJoinStatus.ACCEPTED else 'INVITATION_CREATED'
			details = {
				'role': role.value,
				'join_status': join_status.value,
				'invited_by': invited_by,
			}
			if user_id:
				details['member_user_id'] = user_id
			if email_for_invitation:
				details['invited_email'] = email_for_invitation
			if invitation_token:
				details['invitation_token_used'] = True

			self._log_action(
				group_id=group_id,
				user_id=invited_by,
				action=log_action,
				details=details,
			)
			self.group_member_dal.commit()

		return created_member

	def invite_member(self, group_id: str, email: str, role: GroupMemberRole, invited_by: str) -> GroupMember:
		"""Invite a new member to a group

		Args:
		    group_id (str): ID of the group
		    email (str): Email of the user to invite
		    role (GroupMemberRole): Role of the new member
		    invited_by (str): ID of the user who invited the new member

		Returns:
		    GroupMember: Created group member invitation

		Raises:
		    NotFoundException: If the group is not found
		    ForbiddenException: If the user is not a leader of the group
		    CustomHTTPException: If the user is already a member
		"""
		# Check if group exists
		group = self.group_dal.get_by_id(group_id)
		if not group:
			raise NotFoundException(_('group_not_found'))

		# Check if inviter is a leader
		if not self.group_member_dal.is_user_leader(group_id, invited_by):
			raise ForbiddenException(_('not_group_leader'))

		existing_user = self.user_dal.get_user_by_email(email)
		is_new_user = not existing_user
		user_id_to_invite = existing_user.id if existing_user else None

		if is_new_user:
			invitation_token = secrets.token_urlsafe(32)
			base_url = os.getenv('APP_BASE_URL', 'http://localhost:3000')
			invitation_link = f'{base_url}/register?invitation_token={invitation_token}&group_id={group_id}'

			otp_utils = OTPUtils()
			otp_utils.send_group_invitation_email(
				recipient_email=email,
				group_name=group.name,
				inviter_name=self.user_dal.get_by_id(invited_by).name or invited_by,
				invitation_link=invitation_link,
				is_new_user=True,
			)

			member_data = {
				'group_id': group_id,
				'user_id': None,
				'email_for_invitation': email,
				'role': role,
				'join_status': GroupMemberJoinStatus.PENDING,
				'invited_by': invited_by,
				'invited_at': datetime.now(timezone('Asia/Ho_Chi_Minh')),
				'expires_at': datetime.now(timezone('Asia/Ho_Chi_Minh')) + timedelta(hours=24),
				'invitation_token': invitation_token,
			}
			with self.group_member_dal.transaction():
				created_invite_member = self.group_member_dal.create(member_data)
				self._log_action(
					group_id=group_id,
					user_id=invited_by,
					action='INVITE_SENT_NEW_USER',
					details={
						'invited_email': email,
						'role': role.value,
						'token_used': True,
					},
				)
				self.group_member_dal.commit()
			return created_invite_member

		else:
			user_id_to_invite = existing_user.id
			existing_group_member = self.group_member_dal.get_group_member(group_id, user_id_to_invite)
			if existing_group_member and not existing_group_member.is_deleted:
				if existing_group_member.join_status == GroupMemberJoinStatus.PENDING:
					raise CustomHTTPException(
						status_code=409,
						message=_('User has a pending invitation already.'),
					)
				elif existing_group_member.join_status == GroupMemberJoinStatus.ACCEPTED:
					raise CustomHTTPException(
						status_code=409,
						message=_('User is already a member of this group.'),
					)

			invitation_token = secrets.token_urlsafe(32)
			base_url = os.getenv('APP_BASE_URL', 'http://localhost:3000')
			invitation_link = f'{base_url}/groups/{group_id}/invitations?token={invitation_token}'

			created_invite_member = self.add_member(
				group_id=group_id,
				user_id=user_id_to_invite,
				role=role,
				join_status=GroupMemberJoinStatus.PENDING,
				invited_by=invited_by,
			)

			otp_utils = OTPUtils()
			otp_utils.send_group_invitation_email(
				recipient_email=email,
				group_name=group.name,
				inviter_name=self.user_dal.get_by_id(invited_by).name or invited_by,
				invitation_link=invitation_link,
				is_new_user=False,
			)

			self._log_action(
				group_id=group_id,
				user_id=invited_by,
				action='INVITE_SENT_EXISTING_USER',
				details={
					'invited_email': email,
					'invited_user_id': user_id_to_invite,
					'role': role.value,
				},
			)
			self.group_member_dal.commit()
			return created_invite_member

	def respond_to_invite(self, member_id: str, user_id: str, action: str) -> GroupMember:
		"""Respond to a group invitation

		Args:
		    member_id (str): ID of the group member record
		    user_id (str): ID of the user responding
		    action (str): "accept" or "reject"

		Returns:
		    GroupMember: Updated group member

		Raises:
		    NotFoundException: If the invitation is not found
		    ForbiddenException: If the user is not the invitee
		    ValueError: If the action is invalid
		"""
		print(f'[DEBUG] Responding to invite: member_id={member_id}, user_id={user_id}, action={action}')

		# Check if invitation exists
		member = self.group_member_dal.get_by_id(member_id)
		if not member or member.is_deleted:
			print(f'[DEBUG] Invitation {member_id} not found or deleted')
			raise NotFoundException(_('invitation_not_found'))
		print(f'[DEBUG] Invitation found: member_id={member_id}, user_id={member.user_id}')

		# Check if user is the invitee
		if member.user_id != user_id:
			print(f'[DEBUG] User {user_id} is not the invitation recipient (expected {member.user_id})')
			raise ForbiddenException(_('not_invitation_recipient'))
		print(f'[DEBUG] User {user_id} is the invitation recipient')

		# Check if invitation is still pending
		if member.join_status != GroupMemberJoinStatus.PENDING:
			print(f'[DEBUG] Invitation already responded to: current status={member.join_status}')
			raise CustomHTTPException(message=_('invitation_already_responded'))
		print(f'[DEBUG] Invitation is still pending')

		# Process action
		if action.lower() == 'accept':
			print(f'[DEBUG] User {user_id} is accepting the invitation')
			new_status = GroupMemberJoinStatus.ACCEPTED
		elif action.lower() == 'reject':
			print(f'[DEBUG] User {user_id} is rejecting the invitation')
			new_status = GroupMemberJoinStatus.REJECTED
		else:
			print(f'[DEBUG] Invalid action provided: {action}')
			raise ValueError(_('invalid_action'))

		# Update member status
		print(f'[DEBUG] Updating member status to {new_status}')
		updated_member = self.group_member_dal.update_join_status(member_id, new_status)
		print(f'[DEBUG] Member status updated successfully: {updated_member.join_status}')

		return updated_member

	def remove_member(self, group_id: str, member_user_id: str, removed_by_user_id: str) -> bool:
		"""Remove a member from a group

		Args:
		    group_id (str): ID of the group
		    member_user_id (str): ID of the user to remove
		    removed_by_user_id (str): ID of the user performing the removal

		Returns:
		    bool: True if successful

		Raises:
		    NotFoundException: If the group or member is not found
		    ForbiddenException: If the user doesn't have permission to remove the member
		"""
		print(f'[DEBUG] Removing member: group_id={group_id}, member_user_id={member_user_id}, removed_by_user_id={removed_by_user_id}')

		# Check if group exists
		group = self.group_dal.get_by_id(group_id)
		if not group:
			print(f'[DEBUG] Group {group_id} not found')
			raise NotFoundException(_('group_not_found'))
		print(f'[DEBUG] Group {group_id} found: {group.name}')

		# Check if member exists
		member = self.group_member_dal.get_group_member(group_id, member_user_id)
		if not member or member.is_deleted:
			print(f'[DEBUG] Member {member_user_id} not found in group {group_id} or already deleted')
			raise NotFoundException(_('member_not_found'))
		print(f'[DEBUG] Member {member_user_id} found in group {group_id}')

		# Check permissions:
		# 1. A member can remove themselves
		# 2. A leader can remove any member
		is_self_removal = member_user_id == removed_by_user_id
		is_leader = self.group_member_dal.is_user_leader(group_id, removed_by_user_id)
		print(f'[DEBUG] Is self removal: {is_self_removal}, Is leader: {is_leader}')

		if not (is_self_removal or is_leader):
			print(f'[DEBUG] User {removed_by_user_id} not authorized to remove member {member_user_id}')
			raise ForbiddenException(_('not_authorized_remove_member'))
		print(f'[DEBUG] User {removed_by_user_id} authorized to remove member {member_user_id}')

		# Prevent removing the last leader
		if member.role == GroupMemberRole.LEADER:
			print(f'[DEBUG] Attempting to remove a leader, checking if this is the last leader')
			# Count leaders
			leaders_query = self.db.query(GroupMember).filter(
				GroupMember.group_id == group_id,
				GroupMember.role == GroupMemberRole.LEADER,
				GroupMember.join_status == GroupMemberJoinStatus.ACCEPTED,
				GroupMember.is_deleted == False,
			)
			leader_count = leaders_query.count()
			print(f'[DEBUG] Leader count for group {group_id}: {leader_count}')

			if leader_count <= 1:
				print(f'[DEBUG] Cannot remove the last leader of group {group_id}')
				raise CustomHTTPException(message=_('cannot_remove_last_leader'))
			print(f'[DEBUG] Not the last leader, can proceed with removal')

		# Remove member (soft delete)
		print(f'[DEBUG] Soft deleting member {member.id} from group {group_id}')
		with self.group_member_dal.transaction():
			member.is_deleted = True
			result = self.group_member_dal.update(member.id, {'is_deleted': True})
			print(f'[DEBUG] Member {member.id} removed from group {group_id} result: {result}')
		print(f'[DEBUG] Member removal completed successfully')
		return True

	def list_members(self, group_id: str, user_id: str, search_params: Dict[str, Any]) -> Pagination[GroupMemberResponse]:
		"""List members of a group

		Args:
		    group_id (str): ID of the group
		    user_id (str): ID of the requesting user
		    search_params (Dict[str, Any]): Search parameters

		Returns:
		    Pagination[GroupMemberResponse]: Paginated list of group members

		Raises:
		    NotFoundException: If the group is not found
		    ForbiddenException: If the user doesn't have access to the group
		"""
		print(f'[DEBUG] Listing members for group_id={group_id}, user_id={user_id}')
		print(f'[DEBUG] Search parameters: {search_params}')

		# Check if group exists and user has access
		group = self.get_group_by_id(group_id, user_id)
		if not group:
			print(f'[DEBUG] Group {group_id} not found')
			raise CustomHTTPException(message=_('group_not_found'))

		print(f'[DEBUG] Group {group_id} found: {group.name}')
		print(f'[DEBUG] User {user_id} has access to group {group_id}')

		# Get members
		members: Pagination[GroupMember] = self.group_member_dal.get_group_members(group_id, search_params)
		print(f'[DEBUG] Found {len(members.items)} members for group {group_id}')
		print(f'[DEBUG] Total members count: {members.total_count}, total pages: {members.total_pages}')
		responseItems: List[GroupMemberResponse] = [GroupMemberResponse.model_validate(member) for member in members.items]
		for member in responseItems:
			member.user_data = UserResponse.model_validate(self.user_dal.get_user_by_id(member.user_id)) if member.user_id else None

		return Pagination[GroupMemberResponse](
			items=responseItems,
			total_count=members.total_count,
			page=members.page,
			page_size=members.page_size,
		)

	def get_invitation_status(self, group_id: str, user_id: str, search_params: Dict[str, Any] = None) -> Pagination[GroupMember]:
		"""Get the invitation status for a user in a group

		Args:
		    group_id (str): ID of the group
		    user_id (str): ID of the user

		Returns:
		    GroupMember: Invitation status for the user in the group
		"""
		return self.group_member_dal.get_invitation_status(group_id, user_id, search_params)

	def search_groups(self, user_id: str, search_params: Dict[str, Any]) -> Pagination[Dict[str, Any]]:
		"""Search groups with dynamic filtering

		Args:
		    user_id (str): ID of the user performing the search
		    search_params (Dict[str, Any]): Search parameters including filters, pagination, etc.

		Returns:
		    Pagination[Dict[str, Any]]: Paginated search results with membership details including:
		        - member_id: The ID of the membership record
		        - join_status: The user's join status in the group
		        - member_role: The user's role in the group
		"""
		# Perform the search using the DAL
		result = self.group_dal.search_groups(user_id, search_params)

		# Log search results for debugging
		print(f'[DEBUG] Search found {result.total_count} groups')

		# Log membership details for debugging
		for group in result.items[:3]:  # Only log first 3 for brevity
			print(f'[DEBUG] Group: {group.get("name")}, Member ID: {group.get("member_id")}, Role: {group.get("member_role")}, Status: {group.get("join_status")}')

		return result
