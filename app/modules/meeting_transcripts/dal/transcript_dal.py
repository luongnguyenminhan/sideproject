"""Transcript data access layer"""

import logging
from typing import List

from sqlalchemy import and_
from sqlalchemy.orm import Session
from sqlalchemy.sql.sqltypes import String

from app.core.base_dal import BaseDAL
from app.core.base_model import Pagination
from app.enums.base_enums import Constants
from app.modules.meeting_transcripts.models.transcript import Transcript
from app.modules.meetings.models.meeting import Meeting
from app.utils.filter_utils import apply_dynamic_filters


class TranscriptDAL(BaseDAL[Transcript]):
	"""TranscriptDAL for database operations on transcripts"""

	def __init__(self, db: Session):
		"""Initialize the TranscriptDAL

		Args:
		    db (Session): Database session
		"""
		super().__init__(db, Transcript)

	def get_meeting_transcripts(self, meeting_id: str) -> List[Transcript]:
		"""Get all transcripts for a meeting

		Args:
		    meeting_id (str): Meeting ID

		Returns:
		    List[Transcript]: List of transcripts
		"""
		return self.db.query(Transcript).filter(and_(Transcript.meeting_id == meeting_id, Transcript.is_deleted == False)).all()

	def get_transcript_by_id(self, transcript_id: str) -> Transcript | None:
		"""Get a transcript by ID

		Args:
		    transcript_id (str): Transcript ID

		Returns:
		    Optional[Transcript]: Transcript if found, None otherwise
		"""
		return self.db.query(Transcript).filter(and_(Transcript.id == transcript_id, Transcript.is_deleted == False)).first()

	def search_transcripts(self, user_id: str, params: dict) -> Pagination[Transcript]:
		"""Search transcripts with dynamic filters for a specific user

		Args:
		    user_id (str): User ID to filter by
		    params (dict): Search parameters and filters

		Returns:
		    Pagination[Transcript]: Paginated transcript results
		"""
		logger = logging.getLogger(__name__)

		logger.info(f'Searching transcripts for user {user_id} with parameters: {params}')
		page = int(params.get('page', 1))
		page_size = int(params.get('page_size', Constants.PAGE_SIZE))

		# Start building the query - join with meetings to filter by user_id
		query = (
			self.db.query(Transcript)
			.join(Meeting, Transcript.meeting_id == Meeting.id)
			.filter(
				and_(
					Meeting.user_id == user_id,
					Transcript.is_deleted == False,
					Meeting.is_deleted == False,
				)
			)
		)

		# Handle special case for content_search which needs JSON handling
		content_search = params.get('content_search')
		if content_search:
			search_term = f'%{content_search}%'
			# For JSON fields, implementation depends on the database
			# This is a PostgreSQL-specific JSONB search example
			query = query.filter(Transcript.content.cast(String).ilike(search_term))
			logger.debug(f'Applied JSON content search: %{content_search}%')

			# Remove from params to avoid duplicate filtering
			params_copy = params.copy()
			params_copy.pop('content_search', None)
		else:
			params_copy = params

		# Apply dynamic filters to Transcript model
		query = apply_dynamic_filters(query, Transcript, params_copy)

		# Apply related Meeting model filters if present
		for filter_item in params.get('filters', []):
			field_name = filter_item.get('field')
			operator = filter_item.get('operator')
			value = filter_item.get('value')

			# Check if the field belongs to Meeting model
			if hasattr(Meeting, field_name) and not hasattr(Transcript, field_name):
				column = getattr(Meeting, field_name)
				# Use the apply_filter utility
				from app.utils.filter_utils import apply_filter

				query = apply_filter(query, column, operator, value)
				logger.debug(f'Applied {operator} filter on Meeting.{field_name}: {value}')

		# Order by creation date (most recent first)
		query = query.order_by(Transcript.create_date.desc())

		# Get total count
		total_count = query.count()

		# Apply pagination
		transcripts = query.offset((page - 1) * page_size).limit(page_size).all()

		logger.info(f'Found {total_count} transcripts, returning page {page} with {len(transcripts)} items')

		return Pagination(items=transcripts, total_count=total_count, page=page, page_size=page_size)

	def admin_search_transcripts(self, params: dict) -> Pagination[Transcript]:
		"""Admin search for transcripts across all users

		Args:
		    params (dict): Search parameters and filters

		Returns:
		    Pagination[Transcript]: Paginated transcript results
		"""
		logger = logging.getLogger(__name__)

		logger.info(f'Admin searching transcripts with parameters: {params}')
		page = int(params.get('page', 1))
		page_size = int(params.get('page_size', Constants.PAGE_SIZE))

		# Start building the query without user filtering
		query = self.db.query(Transcript).filter(Transcript.is_deleted == False)

		# Handle special case for content_search which needs JSON handling
		content_search = params.get('content_search')
		if content_search:
			search_term = f'%{content_search}%'
			# For JSON fields, implementation depends on the database
			query = query.filter(Transcript.content.cast(String).ilike(search_term))
			logger.debug(f'Applied JSON content search: %{content_search}%')

			# Remove from params to avoid duplicate filtering
			params_copy = params.copy()
			params_copy.pop('content_search', None)
		else:
			params_copy = params

		# Apply dynamic filters
		query = apply_dynamic_filters(query, Transcript, params_copy)

		# Order by creation date (most recent first)
		query = query.order_by(Transcript.create_date.desc())

		# Get total count
		total_count = query.count()

		# Apply pagination
		transcripts = query.offset((page - 1) * page_size).limit(page_size).all()

		logger.info(f'Found {total_count} transcripts, returning page {page} with {len(transcripts)} items')

		return Pagination(items=transcripts, total_count=total_count, page=page, page_size=page_size)
