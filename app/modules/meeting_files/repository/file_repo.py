"""File upload and processing repository"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List

import aiofiles  # type: ignore
from fastapi import Depends, UploadFile
from pytz import timezone
from sqlalchemy.orm import Session

from app.core.base_repo import BaseRepo
from app.core.database import get_db
from app.enums.meeting_enums import FileTypeEnum, ProcessingStatusEnum
from app.exceptions.exception import CustomHTTPException, NotFoundException
from app.middleware.translation_manager import _
from app.modules.meeting_files.dal.meeting_file_dal import MeetingFileDAL
from app.modules.meetings.dal.meeting_dal import MeetingDAL
from app.modules.meetings.repository.meeting_repo import MeetingRepo
from fastapi import status

logger = logging.getLogger(__name__)


class FileRepo(BaseRepo):
	"""FileRepo for file upload and processing"""

	def __init__(self, db: Session = Depends(get_db)):
		"""Initialize the FileRepo

		Args:
		    db (Session): Database session
		"""
		self.db = db
		self.meeting_dal = MeetingDAL(db)
		self.file_dal = MeetingFileDAL(db)
		self.meeting_repo = MeetingRepo(db)

		# Base directory for file uploads - should be configured properly in production
		self.base_upload_dir = os.environ.get('UPLOAD_DIR', '/tmp/uploads')

	async def upload_meeting_file(
		self,
		meeting_id: str,
		user_id: str,
		file: UploadFile,
		file_type: str = FileTypeEnum.AUDIO.value,
	) -> Dict[str, Any]:
		"""Upload a file for a meeting

		Args:
		    meeting_id (str): Meeting ID
		    user_id (str): User ID
		    file (UploadFile): File to upload
		    file_type (str): Type of file (audio, transcript, etc.)

		Returns:
		    Dict[str, Any]: File metadata

		Raises:
		    NotFoundException: If meeting not found
		    CustomHTTPException: If file upload fails
		"""
		# Ensure meeting exists and belongs to user
		self.meeting_repo.get_meeting_by_id(meeting_id, user_id)

		try:
			# Create directory structure if it doesn't exist
			meeting_upload_dir = os.path.join(self.base_upload_dir, user_id, meeting_id)
			os.makedirs(meeting_upload_dir, exist_ok=True)

			# Generate unique filename
			filename = f'{uuid.uuid4()}{os.path.splitext(file.filename)[1]}'
			file_path = os.path.join(meeting_upload_dir, filename)

			# Save file
			async with aiofiles.open(file_path, 'wb') as out_file:
				content = await file.read()
				await out_file.write(content)

			# Get file size
			file_size = os.path.getsize(file_path)

			# Create file record in database
			file_data = {
				'meeting_id': meeting_id,
				'file_type': file_type,
				'file_path': file_path,
				'file_size_bytes': file_size,
				'mime_type': file.content_type,
				'uploaded_at': datetime.now(timezone('Asia/Ho_Chi_Minh')),
				'processed': False,
				'processing_status': ProcessingStatusEnum.PENDING.value,
			}

			file_record = self.file_dal.create(file_data)

			# Queue processing if it's an audio file
			if file_type == FileTypeEnum.AUDIO.value:
				# Here you would typically queue a background task to process the audio
				# For now, we'll just update the status to indicate processing is needed
				# In a real implementation, you'd use Celery or similar to queue the task
				logger.info(f'Audio file uploaded, would queue for processing: {file_path}')

			return file_record.to_dict()
		except Exception as ex:
			logger.error(f'[ERROR] File upload failed: {ex}')
			raise CustomHTTPException(
				message=_('file_upload_failed'),
			)

	def get_meeting_files(self, meeting_id: str, user_id: str, file_type: str | None = None) -> List[Dict[str, Any]]:
		"""Get all files for a meeting

		Args:
		    meeting_id (str): Meeting ID
		    user_id (str): User ID
		    file_type (Optional[str]): Filter by file type

		Returns:
		    List[Dict[str, Any]]: List of file metadata

		Raises:
		    NotFoundException: If meeting not found
		"""
		# Ensure meeting exists and belongs to user
		self.meeting_repo.get_meeting_by_id(meeting_id, user_id)

		try:
			# Get files
			files = self.file_dal.get_meeting_files(meeting_id, file_type)
			return [file.to_dict() for file in files]
		except Exception as ex:
			logger.error(f'[ERROR] Get meeting files failed: {ex}')
			raise CustomHTTPException(
				message=_('get_files_failed'),
			)

	def delete_file(self, file_id: str, user_id: str) -> bool:
		"""Delete a file

		Args:
		    file_id (str): File ID
		    user_id (str): User ID

		Returns:
		    bool: True if successful

		Raises:
		    NotFoundException: If file not found
		"""
		# Get file
		file = self.file_dal.get_meeting_file_by_id(file_id)
		if not file:
			raise CustomHTTPException(
				message=_('file_not_found'),
			)

		# Ensure file belongs to user through meeting
		self.meeting_repo.get_meeting_by_id(file.meeting_id, user_id)

		try:
			# Soft delete file record
			updated = self.file_dal.update(file_id, {'is_deleted': True})
			if not updated:
				raise CustomHTTPException(
					message=_('delete_file_failed'),
				)

			# Note: We're not deleting the actual file from disk here,
			# which might be a consideration for production systems

			return True
		except Exception as ex:
			logger.error(f'[ERROR] Delete file failed: {ex}')
			raise CustomHTTPException(
				message=_('delete_file_failed'),
			)

	def update_processing_status(self, file_id: str, status: str, error: str | None = None) -> Dict[str, Any]:
		"""Update the processing status of a file

		Args:
		    file_id (str): File ID
		    status (str): New processing status
		    error (Optional[str]): Error message if status is FAILED

		Returns:
		    Dict[str, Any]: Updated file metadata
		"""
		try:
			file = self.file_dal.update_processing_status(file_id, status, error)
			if not file:
				raise CustomHTTPException(
					message=_('update_status_failed'),
					status_code=status.HTTP_404_NOT_FOUND,
				)

			return file.to_dict()
		except Exception as ex:
			logger.error(f'[ERROR] Update processing status failed: {ex}')
			raise CustomHTTPException(
				message=_('update_status_failed'),
			)
