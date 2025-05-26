"""Tag data access layer"""

import logging
from typing import List

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.base_dal import BaseDAL
from app.core.base_model import Pagination
from app.enums.base_enums import Constants
from app.modules.meeting_tags.models.tag import MeetingTag, Tag
from app.utils.filter_utils import apply_dynamic_filters


class TagDAL(BaseDAL[Tag]):
	"""TagDAL for database operations on tags"""

	def __init__(self, db: Session):
		"""Initialize the TagDAL

		Args:
		    db (Session): Database session
		"""
		super().__init__(db, Tag)

	def get_user_tags(self, user_id: str) -> List[Tag]:
		"""Get all tags for a user

		Args:
		    user_id (str): User ID

		Returns:
		    List[Tag]: List of user's tags
		"""
		return self.db.query(Tag).filter(and_(Tag.user_id == user_id, Tag.is_deleted == False)).all()

	def get_tag_by_name(self, user_id: str, name: str) -> Tag:
		"""Get a tag by name for a specific user

		Args:
		    user_id (str): User ID
		    name (str): Tag name

		Returns:
		    Tag: Tag object if found, None otherwise
		"""
		return self.db.query(Tag).filter(and_(Tag.user_id == user_id, Tag.name == name, Tag.is_deleted == False)).first()

	def search_tags(self, user_id: str, params: dict) -> Pagination[Tag]:
		"""Search tags with filters for a specific user

		Args:
		    user_id (str): User ID to filter by
		    params (dict): Search parameters and filters

		Returns:
		    Pagination[Tag]: Paginated tag results
		"""

		logger = logging.getLogger(__name__)

		logger.info(f'Searching tags for user {user_id} with parameters: {params}')
		page = int(params.get('page', 1))
		page_size = int(params.get('page_size', Constants.PAGE_SIZE))

		# Start building the query - filter by user_id
		query = self.db.query(Tag).filter(and_(Tag.user_id == user_id, Tag.is_deleted == False))

		# Apply dynamic filters using the common utility function
		query = apply_dynamic_filters(query, Tag, params)

		# Order by name
		query = query.order_by(Tag.name)

		# Get total count
		total_count = query.count()

		# Apply pagination
		tags = query.offset((page - 1) * page_size).limit(page_size).all()

		logger.info(f'Found {total_count} tags, returning page {page} with {len(tags)} items')

		return Pagination(items=tags, total_count=total_count, page=page, page_size=page_size)


class MeetingTagDAL(BaseDAL[MeetingTag]):
	"""MeetingTagDAL for database operations on meeting tags"""

	def __init__(self, db: Session):
		"""Initialize the MeetingTagDAL

		Args:
		    db (Session): Database session
		"""
		super().__init__(db, MeetingTag)

	def get_meeting_tags(self, meeting_id: str) -> List[MeetingTag]:
		"""Get all tags for a meeting

		Args:
		    meeting_id (str): Meeting ID

		Returns:
		    List[MeetingTag]: List of meeting tags
		"""
		return self.db.query(MeetingTag).filter(and_(MeetingTag.meeting_id == meeting_id, MeetingTag.is_deleted == False)).all()

	def get_meetings_by_tag(self, tag_id: str) -> List[MeetingTag]:
		"""Get all meetings for a tag

		Args:
		    tag_id (str): Tag ID

		Returns:
		    List[MeetingTag]: List of meeting tags
		"""
		return self.db.query(MeetingTag).filter(and_(MeetingTag.tag_id == tag_id, MeetingTag.is_deleted == False)).all()

	def add_tag_to_meeting(self, meeting_id: str, tag_id: str) -> MeetingTag:
		"""Add a tag to a meeting

		Args:
		    meeting_id (str): Meeting ID
		    tag_id (str): Tag ID

		Returns:
		    MeetingTag: Created meeting tag
		"""
		meeting_tag_data = {'meeting_id': meeting_id, 'tag_id': tag_id}
		return self.create(meeting_tag_data)

	def remove_tag_from_meeting(self, meeting_id: str, tag_id: str) -> bool:
		"""Remove a tag from a meeting

		Args:
		    meeting_id (str): Meeting ID
		    tag_id (str): Tag ID

		Returns:
		    bool: True if successful, False otherwise
		"""
		meeting_tag = (
			self.db.query(MeetingTag)
			.filter(
				and_(
					MeetingTag.meeting_id == meeting_id,
					MeetingTag.tag_id == tag_id,
					MeetingTag.is_deleted == False,
				)
			)
			.first()
		)

		if meeting_tag:
			return self.update(meeting_tag.id, {'is_deleted': True}) is not None

		return False
