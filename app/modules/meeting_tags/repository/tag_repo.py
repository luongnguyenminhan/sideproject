"""Tag repository"""

from datetime import datetime
from typing import Any, Dict, List

from fastapi import Depends
from pytz import timezone
from sqlalchemy.orm import Session

from app.core.base_model import Pagination
from app.core.base_repo import BaseRepo
from app.core.database import get_db
from app.exceptions.exception import CustomHTTPException, NotFoundException
from app.middleware.translation_manager import _
from app.modules.meeting_tags.dal.tag_dal import MeetingTagDAL, TagDAL
from app.modules.meeting_tags.models.tag import Tag
from fastapi import status


class TagRepo(BaseRepo):
	"""TagRepo for tag-related business logic"""

	def __init__(self, db: Session = Depends(get_db)):
		"""Initialize the TagRepo

		Args:
		    db (Session): Database session
		"""
		self.db = db
		self.tag_dal = TagDAL(db)
		self.meeting_tag_dal = MeetingTagDAL(db)

	def get_user_tags(self, user_id: str) -> List[Dict[str, Any]]:
		"""Get all tags for a user

		Args:
		    user_id (str): User ID

		Returns:
		    List[Dict[str, Any]]: List of user's tags
		"""
		try:
			tags = self.tag_dal.get_user_tags(user_id)
			return [tag.to_dict() for tag in tags]
		except Exception:
			raise CustomHTTPException(
				message=_('operation_failed'),
			)

	def get_tag_by_id(self, tag_id: str, user_id: str) -> Dict[str, Any]:
		"""Get a tag by ID, ensuring it belongs to the user

		Args:
		    tag_id (str): Tag ID
		    user_id (str): User ID

		Returns:
		    Dict[str, Any]: Tag data

		Raises:
		    NotFoundException: If tag not found
		"""
		tag = self.tag_dal.get_by_id(tag_id)
		if not tag or tag.user_id != user_id or tag.is_deleted:
			raise CustomHTTPException(message=_('tag_not_found'))
		return tag.to_dict()

	def create_tag(self, user_id: str, tag_data: Dict[str, Any]) -> Dict[str, Any]:
		"""Create a new tag

		Args:
		    user_id (str): User ID
		    tag_data (Dict[str, Any]): Tag data

		Returns:
		    Dict[str, Any]: Created tag

		Raises:
		    CustomHTTPException: If tag creation fails
		"""
		try:
			# Check if tag with same name already exists for this user
			existing_tag = self.tag_dal.get_tag_by_name(user_id, tag_data['name'])
			if existing_tag and not existing_tag.is_deleted:
				raise CustomHTTPException(
					message=_('tag_already_exists'),
				)

			# Add user_id to tag data
			tag_data['user_id'] = user_id
			tag_data['is_system'] = tag_data.get('is_system', False)

			# Create tag
			tag = self.tag_dal.create(tag_data)
			return tag.to_dict()
		except Exception:
			raise CustomHTTPException(
				message=_('create_tag_failed'),
			)

	def update_tag(self, tag_id: str, user_id: str, tag_data: Dict[str, Any]) -> Dict[str, Any]:
		"""Update an existing tag

		Args:
		    tag_id (str): Tag ID
		    user_id (str): User ID
		    tag_data (Dict[str, Any]): Updated tag data

		Returns:
		    Dict[str, Any]: Updated tag

		Raises:
		    NotFoundException: If tag not found
		    CustomHTTPException: If tag update fails
		"""
		# Ensure tag exists and belongs to user
		tag = self.tag_dal.get_by_id(tag_id)
		if not tag or tag.user_id != user_id or tag.is_deleted:
			raise CustomHTTPException(message=_('tag_not_found'))

		# Don't allow updating system tags
		if tag.is_system:
			raise CustomHTTPException(
				message=_('cannot_update_system_tag'),
			)

		try:
			# If name is being updated, check for duplicates
			if 'name' in tag_data and tag_data['name'] != tag.name:
				existing_tag = self.tag_dal.get_tag_by_name(user_id, tag_data['name'])
				if existing_tag and not existing_tag.is_deleted:
					raise CustomHTTPException(
						message=_('tag_already_exists'),
					)

			# Update tag
			updated_tag = self.tag_dal.update(tag_id, tag_data)
			if not updated_tag:
				raise CustomHTTPException(
					message=_('update_tag_failed'),
				)

			return updated_tag.to_dict()
		except Exception:
			raise CustomHTTPException(
				message=_('update_tag_failed'),
			)

	def delete_tag(self, tag_id: str, user_id: str) -> bool:
		"""Delete a tag

		Args:
		    tag_id (str): Tag ID
		    user_id (str): User ID

		Returns:
		    bool: True if successful

		Raises:
		    NotFoundException: If tag not found
		    CustomHTTPException: If tag deletion fails
		"""
		# Ensure tag exists and belongs to user
		tag = self.tag_dal.get_by_id(tag_id)
		if not tag or tag.user_id != user_id or tag.is_deleted:
			raise CustomHTTPException(message=_('tag_not_found'))

		# Don't allow deleting system tags
		if tag.is_system:
			raise CustomHTTPException(
				message=_('cannot_delete_system_tag'),
			)

		try:
			# Soft delete tag
			result = self.tag_dal.update(
				tag_id,
				{
					'is_deleted': True,
					'update_date': datetime.now(timezone('Asia/Ho_Chi_Minh')),
				},
			)

			if not result:
				raise CustomHTTPException(
					message=_('delete_tag_failed'),
				)

			return True
		except Exception:
			raise CustomHTTPException(
				message=_('delete_tag_failed'),
			)

	def get_tag_meetings(self, tag_id: str, user_id: str) -> List[str]:
		"""Get all meeting IDs for a tag

		Args:
		    tag_id (str): Tag ID
		    user_id (str): User ID

		Returns:
		    List[str]: List of meeting IDs

		Raises:
		    NotFoundException: If tag not found
		"""
		# Ensure tag exists and belongs to user
		tag = self.tag_dal.get_by_id(tag_id)
		if not tag or tag.user_id != user_id or tag.is_deleted:
			raise CustomHTTPException(message=_('tag_not_found'))

		try:
			# Get all meetings for this tag
			meeting_tags = self.meeting_tag_dal.get_meetings_by_tag(tag_id)
			return [mt.meeting_id for mt in meeting_tags]
		except Exception:
			raise CustomHTTPException(
				message=_('operation_failed'),
			)

	def search_tags(self, user_id: str, request: dict) -> Pagination[Tag]:
		"""Search tags with filters for a specific user

		Args:
		    user_id (str): User ID to filter tags by
		    request (dict): Search parameters and filters

		Returns:
		    Pagination[Tag]: Paginated tag results

		Raises:
		    CustomHTTPException: If search operation fails
		"""
		try:
			return self.tag_dal.search_tags(user_id, request)
		except Exception:
			raise CustomHTTPException(
				message=_('search_tags_failed'),
			)
