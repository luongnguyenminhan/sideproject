"""Meeting file data access layer"""

import logging
import time
from typing import List

import jwt
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.base_dal import BaseDAL
from app.core.base_model import Pagination
from app.core.config import get_settings
from app.enums.base_enums import Constants
from app.enums.meeting_enums import FileTypeEnum, ProcessingStatusEnum
from app.modules.meeting_files.models.meeting_file import MeetingFile
from app.modules.meetings.models.meeting import Meeting
from app.utils.filter_utils import apply_dynamic_filters

logger = logging.getLogger(__name__)


class MeetingFileDAL(BaseDAL[MeetingFile]):
	"""MeetingFileDAL for database operations on meeting files"""

	def __init__(self, db: Session):
		"""Initialize the MeetingFileDAL

		Args:
		    db (Session): Database session
		"""
		super().__init__(db, MeetingFile)

	def get_meeting_files(self, meeting_id: str, file_type: str | None = None) -> List[MeetingFile]:
		"""Get all files for a meeting, optionally filtered by file type

		Args:
		    meeting_id (str): Meeting ID
		    file_type (Optional[str]): File type filter

		Returns:
		    List[MeetingFile]: List of meeting files
		"""
		query = self.db.query(MeetingFile).filter(and_(MeetingFile.meeting_id == meeting_id, MeetingFile.is_deleted == False))

		if file_type:
			query = query.filter(MeetingFile.file_type == file_type)

		return query.all()

	def generate_public_download_link(self, file_id: str) -> str:
		"""Generate a public download link with JWT token for a meeting file
		that does not require authentication when accessed

		Args:
		    file_id (str): Meeting file ID

		Returns:
		    str: Secure public download URL
		"""
		try:
			# Get the file to ensure it exists and validate it
			file = self.get_by_id(file_id)

			if not file or not file.object_name or file.is_deleted:
				logger.warning(f'Invalid file_id or missing object_name: {file_id}')
				return ''

			# Generate a JWT token containing the file information
			settings = get_settings()

			# Create a token with the file information that expires in 30 days
			payload = {
				'file_id': file.id,
				'object_name': file.object_name,
				'exp': int(time.time()) + (30 * 24 * 60 * 60),  # 30 days expiration
			}

			# Sign the token with the app's secret key
			token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

			# Get the API base URL
			base_url = 'https://meobeo.ai'  # Replace with your actual base URL

			# Remove trailing slash if present
			if base_url.endswith('/'):
				base_url = base_url[:-1]

			# Construct the download URL to our public endpoint
			download_url = f'{base_url}/api/v1/calendar-events/files/public-download?token={token}'

			logger.debug(f'Generated public download URL for file {file_id}')
			return download_url

		except Exception as ex:
			logger.error(f'Error generating public download URL: {ex}')
			return 'lmao'

	def get_meeting_file_by_id(self, file_id: str) -> MeetingFile:
		"""Get a meeting file by ID

		Args:
		    file_id (str): File ID

		Returns:
		    MeetingFile: Meeting file if found, None otherwise
		"""
		return self.db.query(MeetingFile).filter(and_(MeetingFile.id == file_id, MeetingFile.is_deleted == False)).first()

	def get_audio_files_by_meeting(self, meeting_id: str) -> List[MeetingFile]:
		"""Get all audio files for a meeting

		Args:
		    meeting_id (str): Meeting ID

		Returns:
		    List[MeetingFile]: List of audio files
		"""
		return self.get_meeting_files(meeting_id, FileTypeEnum.AUDIO.value)

	def get_transcript_files_by_meeting(self, meeting_id: str) -> List[MeetingFile]:
		"""Get all transcript files for a meeting

		Args:
		    meeting_id (str): Meeting ID

		Returns:
		    List[MeetingFile]: List of transcript files
		"""
		return self.get_meeting_files(meeting_id, FileTypeEnum.TRANSCRIPT.value)

	def update_processing_status(self, file_id: str, status: str, error: str | None = None) -> MeetingFile:
		"""Update the processing status of a file

		Args:
		    file_id (str): File ID
		    status (str): New processing status
		    error (Optional[str]): Error message if status is FAILED

		Returns:
		    MeetingFile: Updated meeting file
		"""
		update_data = {
			'processing_status': status,
			'processed': status == ProcessingStatusEnum.COMPLETED.value,
		}

		if error and status == ProcessingStatusEnum.FAILED.value:
			update_data['processing_error'] = error

		return self.update(file_id, update_data)

	def search_files(self, user_id: str, params: dict) -> Pagination[MeetingFile]:
		"""Search meeting files with dynamic filters for a specific user

		Args:
		    user_id (str): User ID to filter by
		    params (dict): Search parameters and filters

		Returns:
		    Pagination[MeetingFile]: Paginated file results
		"""
		logger.info(f'Searching files for user {user_id} with parameters: {params}')
		page = int(params.get('page', 1))
		page_size = int(params.get('page_size', Constants.PAGE_SIZE))

		# Start building the query - join with meetings to filter by user_id
		query = (
			self.db.query(MeetingFile)
			.join(Meeting, MeetingFile.meeting_id == Meeting.id)
			.filter(
				and_(
					Meeting.user_id == user_id,
					MeetingFile.is_deleted == False,
					Meeting.is_deleted == False,
				)
			)
		)

		# Apply dynamic filters using the common utility function
		query = apply_dynamic_filters(query, MeetingFile, params)

		# Apply related Meeting model filters if present
		for filter_item in params.get('filters', []):
			field_name = filter_item.get('field')
			operator = filter_item.get('operator')
			value = filter_item.get('value')

			# Check if the field belongs to Meeting model
			if hasattr(Meeting, field_name) and not hasattr(MeetingFile, field_name):
				column = getattr(Meeting, field_name)
				# Use the apply_filter utility
				from app.utils.filter_utils import apply_filter

				query = apply_filter(query, column, operator, value)
				logger.debug(f'Applied {operator} filter on Meeting.{field_name}: {value}')

		# Order by upload date (most recent first)
		query = query.order_by(MeetingFile.uploaded_at.desc())

		# Get total count
		total_count = query.count()

		# Apply pagination
		files = query.offset((page - 1) * page_size).limit(page_size).all()

		logger.info(f'Found {total_count} files, returning page {page} with {len(files)} items')

		return Pagination(items=files, total_count=total_count, page=page, page_size=page_size)

	def admin_search_files(self, params: dict) -> Pagination[MeetingFile]:
		"""Admin search for meeting files across all users

		Args:
		    params (dict): Search parameters and filters

		Returns:
		    Pagination[MeetingFile]: Paginated file results
		"""
		logger.info(f'Admin searching files with parameters: {params}')
		page = int(params.get('page', 1))
		page_size = int(params.get('page_size', Constants.PAGE_SIZE))

		# Start building the query
		query = self.db.query(MeetingFile).filter(MeetingFile.is_deleted == False)

		# Apply dynamic filters using the common utility function
		query = apply_dynamic_filters(query, MeetingFile, params)

		# Order by upload date (most recent first)
		query = query.order_by(MeetingFile.uploaded_at.desc())

		# Get total count
		total_count = query.count()

		# Apply pagination
		files = query.offset((page - 1) * page_size).limit(page_size).all()

		logger.info(f'Found {total_count} files, returning page {page} with {len(files)} items')

		return Pagination(items=files, total_count=total_count, page=page, page_size=page_size)
