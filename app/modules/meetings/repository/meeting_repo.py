"""Meeting repository"""

from datetime import datetime
import logging
from typing import Any, Dict, List

from fastapi import Depends
from pytz import timezone
from sqlalchemy.orm import Session

from app.core.base_model import Pagination
from app.core.base_repo import BaseRepo
from app.core.database import get_db
from app.core.event_hooks import EventHooks
from app.enums.meeting_enums import MeetingStatusEnum
from app.exceptions.exception import CustomHTTPException, NotFoundException
from app.middleware.translation_manager import _
from app.modules.meeting_tags.dal.tag_dal import MeetingTagDAL, TagDAL
from app.modules.meetings.dal.meeting_dal import MeetingDAL
from app.modules.meetings.models.meeting import Meeting
from app.modules.users.dal.user_dal import UserDAL
from app.modules.groups.dal.group_dal import GroupDAL
from app.modules.groups.dal.group_member_dal import GroupMemberDAL
from fastapi import status


class MeetingRepo(BaseRepo):
	"""MeetingRepo for meeting-related business logic"""

	def __init__(self, db: Session = Depends(get_db)):
		"""Initialize the MeetingRepo

		Args:
		    db (Session): Database session
		"""
		self.db = db
		self.meeting_dal = MeetingDAL(db)
		self.tag_dal = TagDAL(db)
		self.meeting_tag_dal = MeetingTagDAL(db)
		self.user_dal = UserDAL(db)
		self.group_dal = GroupDAL(db)
		self.group_member_dal = GroupMemberDAL(db)
		self.event_hooks = EventHooks()

	def get_user_meetings(self, user_id: str, params: Dict[str, Any]) -> Pagination[Meeting]:
		"""Get all meetings for a user with pagination and filtering

		Args:
		    user_payload (dict): User payload containing user Email
		    params (Dict[str, Any]): Filter parameters

		Returns:
		    Pagination[Meeting]: Paginated list of meetings
		"""
		try:
			return self.meeting_dal.get_user_meetings(user_id, params)
		except Exception:
			raise CustomHTTPException(
				message=_('operation_failed'),
			)

	def get_meeting_by_id(self, meeting_id: str, user_id: str) -> Meeting:
		"""Get a meeting by ID, ensuring it belongs to the user

		Args:
		    meeting_id (str): Meeting ID
		    user_id (str): User ID

		Returns:
		    Meeting: Meeting object

		Raises:
		    NotFoundException: If meeting not found
		"""
		meeting = self.meeting_dal.get_meeting_by_id_and_user(meeting_id, user_id)
		if not meeting:
			raise CustomHTTPException(message=_('meeting_not_found'))
		return meeting

	def create_meeting(
		self,
		user_id: str,
		meeting_data: Dict[str, Any],
		tags: List[str] | None = None,
	) -> Meeting:
		"""Create a new meeting with optional tags

		Args:
		    user_id (str): User ID
		    meeting_data (Dict[str, Any]): Meeting data
		    tags (Optional[List[str]]): List of tag names

		Returns:
		    Meeting: Created meeting
		"""
		try:
			# Start transaction
			with self.meeting_dal.transaction():
				# Add user_id to meeting data
				meeting_data['user_id'] = user_id

				# Create meeting

				meeting = self.meeting_dal.create(meeting_data)
				if not meeting:
					raise CustomHTTPException(
						message=_('create_meeting_failed'),
					)

				# Add tags if provided
				if tags and len(tags) > 0:
					self._add_tags_to_meeting(user_id, meeting.id, tags)

				# Trigger meeting_created event
				self.event_hooks.trigger('meeting_created', meeting.id)

				return meeting
		except Exception:
			raise CustomHTTPException(
				message=_('create_meeting_failed'),
			)

	def update_meeting(self, meeting_id: str, user_id: str, meeting_data: Dict[str, Any]) -> Meeting:
		"""Update an existing meeting

		Args:
		    meeting_id (str): Meeting ID
		    user_id (str): User ID
		    meeting_data (Dict[str, Any]): Updated meeting data

		Returns:
		    Meeting: Updated meeting

		Raises:
		    NotFoundException: If meeting not found
		"""
		# Ensure meeting exists and belongs to user
		meeting = self.get_meeting_by_id(meeting_id, user_id)
		if not meeting:
			raise CustomHTTPException(message=_('meeting_not_found'))
		if meeting.user_id != user_id:
			raise CustomHTTPException(message=_('meeting_not_found'))
		if meeting.is_deleted:
			raise CustomHTTPException(message=_('meeting_not_found'))
		try:
			# Update meeting
			updated_meeting = self.meeting_dal.update(meeting_id, meeting_data)
			if not updated_meeting:
				raise CustomHTTPException(
					message=_('update_meeting_failed'),
				)

			# Trigger meeting_updated event
			self.event_hooks.trigger('meeting_updated', meeting_id)

			return updated_meeting
		except Exception:
			raise CustomHTTPException(
				message=_('update_meeting_failed'),
			)

	def delete_meeting(self, meeting_id: str, user_id: str) -> bool:
		"""Delete a meeting

		Args:
		    meeting_id (str): Meeting ID
		    user_id (str): User ID

		Returns:
		    bool: True if successful

		Raises:
		    NotFoundException: If meeting not found
		"""
		# Ensure meeting exists and belongs to user
		meeting = self.get_meeting_by_id(meeting_id, user_id)
		if not meeting:
			raise CustomHTTPException(message=_('meeting_not_found'))
		if meeting.user_id != user_id:
			raise CustomHTTPException(message=_('meeting_not_found'))
		if meeting.is_deleted:
			raise CustomHTTPException(message=_('meeting_not_found'))

		try:
			# Delete meeting (soft delete)
			result = self.meeting_dal.delete_meeting(meeting_id)
			if not result:
				raise CustomHTTPException(
					message=_('delete_meeting_failed'),
				)

			return True
		except Exception:
			raise CustomHTTPException(
				message=_('delete_meeting_failed'),
			)

	def _add_tags_to_meeting(self, user_id: str, meeting_id: str, tag_names: List[str]) -> None:
		"""Add tags to a meeting, creating tags if they don't exist

		Args:
		    user_id (str): User ID
		    meeting_id (str): Meeting ID
		    tag_names (List[str]): List of tag names
		"""
		for tag_name in tag_names:
			# Check if tag exists
			tag = self.tag_dal.get_tag_by_name(user_id, tag_name)

			# Create tag if it doesn't exist
			if not tag:
				tag_data = {'name': tag_name, 'user_id': user_id, 'is_system': False}
				tag = self.tag_dal.create(tag_data)

			# Add tag to meeting
			self.meeting_tag_dal.add_tag_to_meeting(meeting_id, tag.id)

	def add_tags_to_meeting(self, meeting_id: str, user_id: str, tag_names: List[str]) -> Meeting:
		"""Add tags to a meeting

		Args:
		    meeting_id (str): Meeting ID
		    user_id (str): User ID
		    tag_names (List[str]): List of tag names

		Returns:
		    Meeting: Updated meeting

		Raises:
		    NotFoundException: If meeting not found
		"""
		# Ensure meeting exists and belongs to user
		meeting = self.get_meeting_by_id(meeting_id, user_id)

		try:
			with self.meeting_dal.transaction():
				# Add tags
				self._add_tags_to_meeting(user_id, meeting_id, tag_names)

			return meeting
		except Exception:
			raise CustomHTTPException(
				message=_('add_tags_failed'),
			)

	def remove_tag_from_meeting(self, meeting_id: str, user_id: str, tag_name: str) -> Meeting:
		"""Remove a tag from a meeting

		Args:
		    meeting_id (str): Meeting ID
		    user_id (str): User ID
		    tag_name (str): Tag name

		Returns:
		    Meeting: Updated meeting

		Raises:
		    NotFoundException: If meeting or tag not found
		"""
		# Ensure meeting exists and belongs to user
		meeting = self.get_meeting_by_id(meeting_id, user_id)

		# Find tag
		tag = self.tag_dal.get_tag_by_name(user_id, tag_name)
		if not tag:
			raise CustomHTTPException(message=_('tag_not_found'))

		try:
			# Remove tag from meeting
			result = self.meeting_tag_dal.remove_tag_from_meeting(meeting_id, tag.id)
			if not result:
				raise CustomHTTPException(
					message=_('remove_tag_failed'),
				)

			return meeting
		except Exception:
			raise CustomHTTPException(
				message=_('remove_tag_failed'),
			)

	def join_meeting(self, user_id: str, meeting_data: Dict[str, Any]) -> Meeting:
		"""Record that a user has joined a meeting

		Args:
		    user_id (str): User ID
		    meeting_data (Dict[str, Any]): Meeting join data including title, platform, timestamp, and optional group_id

		Returns:
		    Meeting: Meeting that was joined, or a newly created one if it didn't exist

		Raises:
		    CustomHTTPException: If joining meeting fails or group validation fails
		"""
		try:
			with self.meeting_dal.transaction():
				# Get current user
				current_user = self.user_dal.get_user_by_id(user_id)
				current_timestamp = datetime.now(timezone('Asia/Ho_Chi_Minh'))

				# Check if group_id is provided for group meeting validation
				group_id = meeting_data.get('group_id')
				if group_id:
					# Validate group exists
					group = self.group_dal.get_by_id(group_id)
					if not group:
						raise CustomHTTPException(message=_('group_not_found'))

					if group.is_deleted:
						raise CustomHTTPException(message=_('group_not_found'))

					# Check if user is an accepted member of the group
					is_accepted_member = self.group_member_dal.is_user_accepted_member(group_id, user_id)
					if not is_accepted_member:
						raise CustomHTTPException(message=_('user_not_group_member'))

				# Try to find an existing meeting with the title for this user
				filter_params = {
					'title': meeting_data['title'],
					'page': 1,
					'page_size': 1,
					'status': 'scheduled',
				}

				result = self.meeting_dal.get_user_meetings(user_id, filter_params)

				# If meeting exists, update it
				if result.items and len(result.items) > 0:
					meeting = result.items[0]

					# Check if meeting already belongs to a different group
					if group_id and meeting.group_id and meeting.group_id != group_id:
						raise CustomHTTPException(message=_('meeting_already_belongs_to_different_group'))

					update_data = {
						'platform': meeting_data['platform'],
						'last_joined_at': current_timestamp,
						'meeting_type': 'Not Calendar Event',
						'organizer_email': current_user.email,
						'organizer_name': current_user.name,
						'meeting_link': meeting_data['url'],
						'updated_at': current_timestamp,
					}

					# Add group_id if provided and meeting doesn't have one
					if group_id and not meeting.group_id:
						update_data['group_id'] = group_id

					return self.meeting_dal.update(meeting.id, update_data)

				# Otherwise create a new meeting
				new_meeting_data = {
					'user_id': user_id,
					'title': meeting_data['title'],
					'platform': meeting_data['platform'],
					'meeting_date': current_timestamp,
					'last_joined_at': current_timestamp,
					'status': MeetingStatusEnum.IN_PROGRESS.value,
					'organizer_email': current_user.email,
					'organizer_name': current_user.name,
					'meeting_link': meeting_data['url'],
					'meeting_type': 'Not Calendar Event',
				}

				# Add group_id if provided
				if group_id:
					new_meeting_data['group_id'] = group_id

				logger = logging.getLogger(__name__)
				logger.info(f'Creating new meeting with data: {new_meeting_data}')
				return self.meeting_dal.create(new_meeting_data)

		except Exception as e:
			# Re-raise known exceptions
			if isinstance(e, CustomHTTPException):
				raise e
			# For unexpected exceptions
			raise CustomHTTPException(
				message=_('join_meeting_failed'),
			)

	def search_meetings(self, user_id: str, request: dict) -> Pagination[Meeting]:
		"""Search meetings with filters for a specific user

		Args:
		    user_id (str): User ID to filter meetings by
		    request (dict): Search parameters and filters

		Returns:
		    Pagination[Meeting]: Paginated meeting results

		Raises:
		    CustomHTTPException: If search operation fails
		"""
		try:
			# Add user_id to filter parameters to restrict search to user's meetings
			filter_params = request.copy()
			filter_params['user_id'] = user_id

			return self.meeting_dal.search_meetings(filter_params)
		except Exception:
			raise CustomHTTPException(
				message=_('search_meetings_failed'),
			)
