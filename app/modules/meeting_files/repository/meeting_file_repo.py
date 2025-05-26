"""Meeting file repository"""

import io
import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

from fastapi import Depends, UploadFile
from pytz import timezone
from sqlalchemy.orm import Session
from fastapi import status

from app.core.base_model import Pagination
from app.core.base_repo import BaseRepo
from app.core.database import get_db
from app.core.event_hooks import EventHooks
from app.enums.meeting_enums import FileTypeEnum, ProcessingStatusEnum
from app.exceptions.exception import CustomHTTPException, NotFoundException
from app.middleware.translation_manager import _
from app.modules.meeting_files.dal.meeting_file_dal import MeetingFileDAL
from app.modules.meeting_files.models.meeting_file import MeetingFile
from app.modules.meetings.dal.meeting_dal import MeetingDAL
from app.modules.meetings.dal.meeting_note_dal import MeetingNoteDAL
from app.modules.meetings.repository.meeting_repo import MeetingRepo
from app.utils.minio.minio_handler import minio_handler
from app.utils.pdf import MDToPDFConverter

logger = logging.getLogger(__name__)


class MeetingFileRepo(BaseRepo):
	"""MeetingFileRepo for meeting file operations and management"""

	def __init__(self, db: Session = Depends(get_db)):
		"""Initialize the MeetingFileRepo

		Args:
		    db (Session): Database session
		"""
		self.db = db
		self.meeting_dal = MeetingDAL(db)
		self.meeting_file_dal = MeetingFileDAL(db)
		self.meeting_repo = MeetingRepo(db)
		self.event_hooks = EventHooks()

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
			files = self.meeting_file_dal.get_meeting_files(meeting_id, file_type)
			file_dicts = []

			for file in files:
				file_dict = file.to_dict()
				# If file has an object_name but no file_url, generate a URL
				if file.object_name and not file.file_url:
					try:
						file_dict['file_url'] = minio_handler.get_file_url(file.object_name)
					except Exception as ex:
						logger.warning(f'Failed to generate URL for file {file.id}: {ex}')

				file_dicts.append(file_dict)

			return file_dicts
		except Exception as ex:
			logger.error(f'[ERROR] Get meeting files failed: {ex}')
			raise CustomHTTPException(
				message=_('get_files_failed'),
			)

	def get_file_by_id(self, file_id: str, user_id: str) -> Dict[str, Any]:
		"""Get a file by ID

		Args:
		    file_id (str): File ID
		    user_id (str): User ID

		Returns:
		    Dict[str, Any]: File metadata

		Raises:
		    CustomHTTPException: If file not found
		"""
		# Get file
		file = self.meeting_file_dal.get_meeting_file_by_id(file_id)
		if not file:
			raise CustomHTTPException(
				message=_('file_not_found'),
				status_code=status.HTTP_404_NOT_FOUND,
			)

		# Ensure file belongs to user through meeting
		self.meeting_repo.get_meeting_by_id(file.meeting_id, user_id)

		file_dict = file.to_dict()

		# Generate URL if file has object_name but no file_url
		if file.object_name and not file.file_url:
			try:
				file_dict['file_url'] = minio_handler.get_file_url(file.object_name)
			except Exception as ex:
				logger.warning(f'Failed to generate URL for file {file.id}: {ex}')

		return file_dict

	async def upload_meeting_file(
		self,
		meeting_id: str,
		user_id: str,
		file: UploadFile,
		file_type: str = FileTypeEnum.AUDIO.value,
	) -> Dict[str, Any]:
		"""Upload a file for a meeting using MinIO storage

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
			# Upload to MinIO
			object_name = await minio_handler.upload_fastapi_file(file=file, meeting_id=meeting_id, file_type=file_type)

			# Generate public URL
			file_url = minio_handler.get_file_url(object_name)

			# Get file size from the UploadFile
			content = await file.read()
			file_size = len(content)
			await file.seek(0)  # Reset file cursor

			# Create file record in database
			file_data = {
				'meeting_id': meeting_id,
				'file_type': file_type,
				'file_path': None,  # No local file path when using MinIO
				'object_name': object_name,
				'file_url': file_url,
				'file_size_bytes': file_size,
				'mime_type': file.content_type,
				'uploaded_at': datetime.now(timezone('Asia/Ho_Chi_Minh')),
				'processed': False,
				'processing_status': ProcessingStatusEnum.PENDING.value,
			}
			with self.meeting_file_dal.transaction():
				file_record = self.meeting_file_dal.create(file_data)

			# Queue processing if it's an audio file
			if file_type == FileTypeEnum.AUDIO.value:
				# Here you would typically queue a background task to process the audio
				logger.info(f'Audio file uploaded, would queue for processing: {object_name}')

			# Trigger meeting_file_created event
			self.event_hooks.trigger('meeting_file_created', meeting_id)

			return file_record.to_dict()
		except Exception as ex:
			logger.error(f'[ERROR] File upload failed: {ex}')
			raise CustomHTTPException(
				message=_('file_upload_failed'),
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
		file = self.meeting_file_dal.get_meeting_file_by_id(file_id)
		if not file:
			raise CustomHTTPException(
				message=_('file_not_found'),
			)

		# Ensure file belongs to user through meeting
		self.meeting_repo.get_meeting_by_id(file.meeting_id, user_id)

		try:
			# Try to delete the file from MinIO if it has an object_name
			if file.object_name:
				try:
					minio_handler.remove_file(file.object_name)
				except Exception as minio_ex:
					logger.warning(f'Failed to remove file from MinIO: {minio_ex}')

			# Soft delete file record
			updated: MeetingFile = self.meeting_file_dal.update(file_id, {'is_deleted': True})
			if not updated:
				raise CustomHTTPException(
					message=_('delete_file_failed'),
				)
			self.db.commit()
			self.db.refresh(updated)
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
			file = self.meeting_file_dal.update_processing_status(file_id, status, error)
			if not file:
				raise CustomHTTPException(
					message=_('update_status_failed'),
				)

			file_dict = file.to_dict()

			# Generate URL if file has object_name but no file_url
			if file.object_name and not file.file_url:
				try:
					file_dict['file_url'] = minio_handler.get_file_url(file.object_name)
					# Update the file_url in the database
					self.meeting_file_dal.update(file_id, {'file_url': file_dict['file_url']})
				except Exception as ex:
					logger.warning(f'Failed to generate URL for file {file.id}: {ex}')

			# Trigger meeting_file_updated event
			if file.meeting_id:
				self.event_hooks.trigger('meeting_file_updated', file.meeting_id)

			return file_dict
		except Exception as ex:
			logger.error(f'[ERROR] Update processing status failed: {ex}')
			raise CustomHTTPException(
				message=_('update_status_failed'),
			)

	def download_file(self, file_id: str, user_id: str) -> Dict[str, Any]:
		"""Download a file from MinIO

		Args:
		    file_id (str): File ID
		    user_id (str): User ID

		Returns:
		    Dict[str, Any]: File content and metadata

		Raises:
		    NotFoundException: If file not found
		"""
		# Get file
		file = self.meeting_file_dal.get_meeting_file_by_id(file_id)
		if not file:
			raise CustomHTTPException(
				message=_('file_not_found'),
			)

		# Ensure file belongs to user through meeting
		self.meeting_repo.get_meeting_by_id(file.meeting_id, user_id)

		if not file.object_name:
			raise CustomHTTPException(
				message=_('file_not_in_storage'),
			)

		try:
			# Download file from MinIO
			file_content, file_name = minio_handler.download_file(file.object_name)

			return {
				'content': file_content,
				'filename': file_name,
				'content_type': file.mime_type or 'application/octet-stream',
				'file_size': file.file_size_bytes,
			}
		except Exception as ex:
			logger.error(f'[ERROR] Download file failed: {ex}')
			raise CustomHTTPException(
				message=_('download_file_failed'),
			)

	def search_files(self, user_id: str, request: dict) -> Pagination[MeetingFile]:
		"""Search meeting files with filters for a specific user

		Args:
		    user_id (str): User ID to filter meetings by
		    request (dict): Search parameters and filters

		Returns:
		    Pagination[MeetingFile]: Paginated file results

		Raises:
		    CustomHTTPException: If search operation fails
		"""
		try:
			# Add user_id to filter parameters to restrict search to user's files
			filter_params = request.copy()

			return self.meeting_file_dal.search_files(user_id, filter_params)
		except Exception as ex:
			logger.error(f'[ERROR] Search meeting files failed: {ex}')
			raise CustomHTTPException(
				message=_('search_files_failed'),
			)

	def admin_search_files(self, request: dict) -> Pagination[MeetingFile]:
		"""Admin search for meeting files across all users

		Args:
		    request (dict): Search parameters and filters

		Returns:
		    Pagination[MeetingFile]: Paginated file results

		Raises:
		    CustomHTTPException: If search operation fails
		"""
		try:
			return self.meeting_file_dal.admin_search_files(request)
		except Exception as ex:
			logger.error(f'[ERROR] Admin search meeting files failed: {ex}')
			raise CustomHTTPException(
				message=_('search_files_failed'),
			)

	def generate_note_pdf(self, note_id: str, user_id: str) -> Tuple[bytes, str]:
		"""Generate a PDF from a meeting note

		Args:
		    note_id (str): Meeting note ID
		    user_id (str): User ID

		Returns:
		    Tuple[bytes, str]: PDF content bytes and filename

		Raises:
		    NotFoundException: If note not found
		    CustomHTTPException: If PDF generation fails
		"""
		# Get the meeting note
		meeting_note_dal = MeetingNoteDAL(self.db)
		note = meeting_note_dal.get_note_by_id(note_id)

		if not note:
			raise CustomHTTPException(message=_('note_not_found'))

		# Ensure note belongs to user through meeting
		meeting = self.meeting_repo.get_meeting_by_id(note.meeting_id, user_id)
		if not meeting:
			raise CustomHTTPException(message=_('meeting_not_found'))

		try:
			# Convert markdown content to PDF
			md_to_pdf_converter = MDToPDFConverter(note.content.get('text', '') if isinstance(note.content, dict) else note.content)
			pdf_bytes = md_to_pdf_converter.convert()

			# Generate a filename based on meeting title and date
			meeting_title = meeting.title or 'Meeting'
			sanitized_title = ''.join(c for c in meeting_title if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
			filename = f'{sanitized_title}_note_{datetime.now(timezone("Asia/Ho_Chi_Minh")).strftime("%Y%m%d")}.pdf'

			return pdf_bytes, filename
		except Exception as ex:
			logger.error(f'[ERROR] PDF generation failed: {ex}')
			raise CustomHTTPException(
				message=_('pdf_generation_failed'),
			)

	async def save_note_as_pdf(self, note_id: str, user_id: str) -> Dict[str, Any]:
		"""Generate a PDF from a meeting note and save it as a file

		Args:
		    note_id (str): Meeting note ID
		    user_id (str): User ID

		Returns:
		    Dict[str, Any]: File metadata of the saved PDF

		Raises:
		    NotFoundException: If note not found
		    CustomHTTPException: If PDF generation or saving fails
		"""
		# Get the meeting note
		meeting_note_dal = MeetingNoteDAL(self.db)
		note = meeting_note_dal.get_note_by_id(note_id)

		if not note:
			raise CustomHTTPException(message=_('note_not_found'))

		# Ensure note belongs to user through meeting
		meeting = self.meeting_repo.get_meeting_by_id(note.meeting_id, user_id)
		if not meeting:
			raise CustomHTTPException(message=_('meeting_not_found'))

		try:
			# Generate PDF content and filename
			pdf_bytes, filename = self.generate_note_pdf(note_id, user_id)

			# Create BytesIO object from PDF bytes
			io.BytesIO(pdf_bytes)

			# Upload to MinIO
			object_name = await minio_handler.upload_bytes(
				content=pdf_bytes,
				filename=filename,
				meeting_id=note.meeting_id,
				file_type=FileTypeEnum.PDF.value,
				content_type='application/pdf',
			)

			# Generate public URL
			file_url = minio_handler.get_file_url(object_name)

			# Create file record in database
			file_data = {
				'meeting_id': note.meeting_id,
				'file_type': FileTypeEnum.PDF.value,
				'object_name': object_name,
				'file_url': file_url,
				'file_size_bytes': len(pdf_bytes),
				'mime_type': 'pdf',
				'uploaded_at': datetime.now(),
				'processed': True,
				'processing_status': ProcessingStatusEnum.COMPLETED.value,
			}

			with self.meeting_file_dal.transaction():
				file_record = self.meeting_file_dal.create(file_data)

			# Trigger meeting_file_created event
			self.event_hooks.trigger('meeting_file_created', note.meeting_id)

			return file_record.to_dict()
		except Exception as ex:
			logger.error(f'[ERROR] PDF generation and saving failed: {ex}')
			raise CustomHTTPException(
				message=_('pdf_generation_failed'),
			)
