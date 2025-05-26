"""Meeting data access layer"""

import logging
from datetime import datetime

from pytz import timezone
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.base_dal import BaseDAL
from app.core.base_model import Pagination
from app.enums.base_enums import Constants
from app.modules.meetings.models.meeting import Meeting
from app.utils.filter_utils import apply_dynamic_filters


class MeetingDAL(BaseDAL[Meeting]):
	"""MeetingDAL for database operations on meetings"""

	def __init__(self, db: Session):
		"""Initialize the MeetingDAL

		Args:
		    db (Session): Database session
		"""
		super().__init__(db, Meeting)

	def get_user_meetings(self, user_id: str, params: dict) -> Pagination[Meeting]:
		"""Get all meetings for a user with pagination and dynamic filtering

		Args:
		    user_id (str): User ID
		    params (dict): Filter parameters including:
		        - page: Page number
		        - page_size: Items per page
		        - filters: List of filter objects with field, operator, and value

		Returns:
		    Pagination[Meeting]: Paginated list of meetings
		"""
		logger = logging.getLogger(__name__)

		logger.info(f'Searching meetings for user {user_id} with parameters: {params}')
		page = int(params.get('page', 1))
		page_size = int(params.get('page_size', Constants.PAGE_SIZE))

		# Base query for user's meetings
		query = self.db.query(Meeting).filter(and_(Meeting.user_id == user_id, Meeting.is_deleted == False))

		# Apply dynamic filters using the common utility function
		query = apply_dynamic_filters(query, Meeting, params)

		# Order by most recent meetings first
		query = query.order_by(Meeting.meeting_date.desc())

		# Count total results
		total_count = query.count()

		# Paginate results
		meetings = query.offset((page - 1) * page_size).limit(page_size).all()

		logger.info(f'Found {total_count} meetings, returning page {page} with {len(meetings)} items')

		return Pagination(items=meetings, total_count=total_count, page=page, page_size=page_size)

	def get_meeting_by_id_and_user(self, meeting_id: str, user_id: str) -> Meeting:
		"""Get a specific meeting by ID and user ID

		Args:
		    meeting_id (str): Meeting ID
		    user_id (str): User ID

		Returns:
		    Meeting: Meeting object if found, None otherwise
		"""
		return (
			self.db.query(Meeting)
			.filter(
				and_(
					Meeting.id == meeting_id,
					Meeting.user_id == user_id,
					Meeting.is_deleted == False,
				)
			)
			.first()
		)

	def delete_meeting(self, meeting_id: str) -> bool:
		"""Soft delete a meeting

		Args:
		    meeting_id (str): Meeting ID

		Returns:
		    bool: True if successful, False otherwise
		"""
		return (
			self.update(
				meeting_id,
				{
					'is_deleted': True,
					'update_date': datetime.now(timezone('Asia/Ho_Chi_Minh')),
				},
			)
			is not None
		)

	def search_meetings(self, params: dict) -> Pagination[Meeting]:
		"""Search meetings with dynamic filters

		Args:
		    params (dict): Search parameters including:
		        - page: Page number
		        - page_size: Items per page
		        - filters: List of filter objects with field, operator, and value
		        - user_id: Optional filter by user ID

		Returns:
		    Pagination[Meeting]: Paginated meeting results
		"""
		logger = logging.getLogger(__name__)

		logger.info(f'Searching meetings with parameters: {params}')
		page = int(params.get('page', 1))
		page_size = int(params.get('page_size', Constants.PAGE_SIZE))

		# Start building the query
		query = self.db.query(Meeting).filter(Meeting.is_deleted == False)

		# Apply dynamic filters using the common utility function
		query = apply_dynamic_filters(query, Meeting, params)

		# Filter by user_id if provided (for user-specific searches)
		if 'user_id' in params and params['user_id']:
			query = query.filter(Meeting.user_id == params['user_id'])

		# Order by meeting date (most recent first)
		query = query.order_by(Meeting.meeting_date.desc())

		# Get total count
		total_count = query.count()

		# Apply pagination
		meetings = query.offset((page - 1) * page_size).limit(page_size).all()

		logger.info(f'Found {total_count} meetings, returning page {page} with {len(meetings)} items')

		return Pagination(items=meetings, total_count=total_count, page=page, page_size=page_size)
