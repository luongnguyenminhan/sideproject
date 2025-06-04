from pytz import timezone
from sqlalchemy.orm import Session
from fastapi import Depends, UploadFile
from app.core.database import get_db
from app.modules.chat.dal.file_dal import FileDAL
from app.modules.chat.schemas.file_request import FileListRequest
from app.modules.chat.services.file_service import file_service
from app.exceptions.exception import NotFoundException, ValidationException
from app.middleware.translation_manager import _
from datetime import datetime
from typing import List, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)


class FileRepo:
	def __init__(self, db: Session = Depends(get_db)):
		logger.info(f'\033[96m[FileRepo.__init__] Initializing FileRepo with db session: {db}\033[0m')
		self.db = db
		self.file_dal = FileDAL(db)
		logger.info(f'\033[92m[FileRepo.__init__] FileRepo initialized successfully\033[0m')

	async def upload_files(
		self,
		files: List[UploadFile],
		user_id: str,
		conversation_id: Optional[str] = None,
	):
		"""Upload multiple files and save metadata to database"""
		logger.info(f'\033[93m[FileRepo.upload_files] Starting upload for {len(files)} files, user_id: {user_id}, conversation_id: {conversation_id}\033[0m')
		uploaded_files = []

		for i, file in enumerate(files):
			logger.info(f'\033[94m[FileRepo.upload_files] Processing file {i + 1}/{len(files)}: {file.filename}\033[0m')
			try:
				# Validate file
				logger.info(f'\033[94m[FileRepo.upload_files] Validating file: {file.filename}\033[0m')
				if not file_service.validate_file(file):
					logger.info(f'\033[91m[FileRepo.upload_files] File validation failed: {file.filename}\033[0m')
					raise ValidationException(_('invalid_file'))
				logger.info(f'\033[92m[FileRepo.upload_files] File validation passed: {file.filename}\033[0m')

				# Calculate checksum
				logger.info(f'\033[94m[FileRepo.upload_files] Calculating checksum for: {file.filename}\033[0m')
				checksum = await file_service.calculate_checksum(file)
				logger.info(f'\033[92m[FileRepo.upload_files] Checksum calculated: {checksum}\033[0m')

				# Skip duplicate check - allow all uploads
				logger.info(f'\033[94m[FileRepo.upload_files] Skipping duplicate check - allowing all uploads\033[0m')

				# Upload to MinIO
				logger.info(f'\033[94m[FileRepo.upload_files] Uploading to MinIO storage: {file.filename}\033[0m')
				file_path, url = await file_service.upload_to_storage(file, user_id, conversation_id)
				logger.info(f'\033[92m[FileRepo.upload_files] File uploaded to path: {file_path}\033[0m')

				# Create file record in database
				file_data = {
					'name': file.filename,
					'original_name': file.filename,
					'file_path': file_path,
					'file_url': url,
					'size': file.size or 0,
					'type': file.content_type or file_service.get_content_type(file.filename),
					'user_id': user_id,
					'conversation_id': conversation_id,
					'upload_date': datetime.now(timezone('Asia/Ho_Chi_Minh')).isoformat(),
					'checksum': checksum,
					'minio_bucket': 'default',
				}
				logger.info(f'\033[96m[FileRepo.upload_files] Created file_data: {file_data}\033[0m')

				with self.file_dal.transaction():
					logger.info(f'\033[94m[FileRepo.upload_files] Creating file record in database\033[0m')
					db_file = self.file_dal.create(file_data)
					logger.info(f'\033[92m[FileRepo.upload_files] File record created with ID: {db_file.id}\033[0m')
					uploaded_files.append(db_file)

			except Exception as e:
				logger.info(f'\033[91m[FileRepo.upload_files] Error uploading file {file.filename}: {str(e)}\033[0m')
				raise ValidationException(f'Failed to upload file {file.filename}: {str(e)}')

		logger.info(f'\033[92m[FileRepo.upload_files] Upload completed, {len(uploaded_files)} files processed\033[0m')

		# Trigger indexing events cho uploaded files nếu có conversation_id
		if conversation_id and uploaded_files:
			try:
				logger.info(f'\033[95m[FileRepo.upload_files] Triggering indexing events for {len(uploaded_files)} files\033[0m')
				await self._trigger_file_indexing_events(uploaded_files, conversation_id, user_id)
			except Exception as e:
				logger.error(f'\033[91m[FileRepo.upload_files] Error triggering indexing events: {str(e)}\033[0m')
				# Don't fail the upload if indexing fails

		return uploaded_files

	def get_file_by_id(self, file_id: str, user_id: Optional[str] = None):
		"""Get file by ID with optional user ownership check"""
		logger.info(f'\033[93m[FileRepo.get_file_by_id] Getting file by ID: {file_id}, user_id: {user_id}\033[0m')
		if user_id:
			logger.info(f'\033[94m[FileRepo.get_file_by_id] Checking user ownership\033[0m')
			file = self.file_dal.get_user_file_by_id(file_id, user_id)
		else:
			logger.info(f'\033[94m[FileRepo.get_file_by_id] Getting file without user check\033[0m')
			file = self.file_dal.get_by_id(file_id)

		if not file:
			logger.info(f'\033[91m[FileRepo.get_file_by_id] File not found: {file_id}\033[0m')
			raise NotFoundException(_('file_not_found'))
		logger.info(f'\033[92m[FileRepo.get_file_by_id] File found: {file.name}, size: {file.size}\033[0m')
		return file

	def get_user_files(self, user_id: str, request: FileListRequest):
		"""Get user's files with pagination and filtering"""
		logger.info(f'\033[93m[FileRepo.get_user_files] Getting files for user: {user_id}, page: {request.page}, page_size: {request.page_size}, file_type: {request.file_type}, search: {request.search}, conversation_id: {request.conversation_id}\033[0m')
		files = self.file_dal.get_user_files(
			user_id=user_id,
			page=request.page,
			page_size=request.page_size,
			file_type=request.file_type,
			search=request.search,
			conversation_id=request.conversation_id,
		)
		logger.info(f'\033[92m[FileRepo.get_user_files] Found {len(files.items) if hasattr(files, "items") else len(files)} files\033[0m')
		return files

	async def delete_file(self, file_id: str, user_id: str):
		"""Delete file from MinIO and mark as deleted in database"""
		logger.info(f'\033[93m[FileRepo.delete_file] Deleting file: {file_id} for user: {user_id}\033[0m')
		file = self.get_file_by_id(file_id, user_id)
		logger.info(f'\033[94m[FileRepo.delete_file] File found for deletion: {file.name}, path: {file.file_path}\033[0m')

		try:
			# Remove from MinIO
			logger.info(f'\033[94m[FileRepo.delete_file] Removing from MinIO storage: {file.file_path}\033[0m')
			await file_service.delete_from_storage(file.file_path)
			logger.info(f'\033[92m[FileRepo.delete_file] File removed from storage successfully\033[0m')

			# Soft delete in database
			with self.file_dal.transaction():
				logger.info(f'\033[94m[FileRepo.delete_file] Performing soft delete in database\033[0m')
				self.file_dal.delete(file_id)
				logger.info(f'\033[92m[FileRepo.delete_file] File soft deleted in database\033[0m')

			logger.info(f'\033[92m[FileRepo.delete_file] File deletion completed successfully\033[0m')
			return True

		except Exception as e:
			logger.info(f'\033[91m[FileRepo.delete_file] Error deleting file: {str(e)}\033[0m')
			raise ValidationException(f'Failed to delete file: {str(e)}')

	def get_file_download_url(self, file_id: str, user_id: Optional[str] = None, expires: int = 3600):
		"""Get temporary download URL for file"""
		logger.info(f'\033[93m[FileRepo.get_file_download_url] Getting download URL for file: {file_id}, user_id: {user_id}, expires: {expires}\033[0m')
		file = self.get_file_by_id(file_id, user_id)
		logger.info(f'\033[94m[FileRepo.get_file_download_url] File found: {file.name}, current download_count: {file.download_count}\033[0m')

		# Increment download count
		with self.file_dal.transaction():
			logger.info(f'\033[94m[FileRepo.get_file_download_url] Incrementing download count\033[0m')
			self.file_dal.update(file_id, {'download_count': file.download_count + 1})
			logger.info(f'\033[92m[FileRepo.get_file_download_url] Download count updated to: {file.download_count + 1}\033[0m')

		# Generate download URL
		logger.info(f'\033[94m[FileRepo.get_file_download_url] Generating download URL for path: {file.file_path}\033[0m')
		download_url = file_service.get_download_url(file.file_path, expires)
		logger.info(f'\033[92m[FileRepo.get_file_download_url] Download URL generated successfully\033[0m')
		return download_url

	def get_files_by_conversation(
		self,
		user_id: str,
		conversation_id: str,
		request: FileListRequest,
	):
		"""Get files for a specific conversation with pagination and filtering"""
		logger.info(f'\033[93m[FileRepo.get_files_by_conversation] Getting files for conversation: {conversation_id}, user: {user_id}, page: {request.page}, page_size: {request.page_size}, file_type: {request.file_type}, search: {request.search}\033[0m')
		files = self.file_dal.get_conversation_files(
			user_id=user_id,
			conversation_id=conversation_id,
			page=request.page,
			page_size=request.page_size,
			file_type=request.file_type,
			search=request.search,
		)
		logger.info(f'\033[92m[FileRepo.get_files_by_conversation] Found {len(files.items) if hasattr(files, "items") else len(files)} files\033[0m')
		return files

	def get_unindexed_files_for_conversation(self, conversation_id: str):
		"""Get all unindexed files for a specific conversation"""
		logger.info(f'[FileRepo.get_unindexed_files_for_conversation] Getting unindexed files for conversation: {conversation_id}')
		return self.file_dal.get_unindexed_files_for_conversation(conversation_id)

	def get_all_files_for_conversation(self, conversation_id: str):
		"""Get all files for a specific conversation"""
		logger.info(f'[FileRepo.get_all_files_for_conversation] Getting all files for conversation: {conversation_id}')
		return self.file_dal.get_all_files_for_conversation(conversation_id)

	def mark_file_as_indexed(self, file_id: str, success: bool = True, error_message: str = None):
		"""Mark a file as indexed"""
		logger.info(f'[FileRepo.mark_file_as_indexed] Marking file {file_id} as indexed: success={success}')
		return self.file_dal.mark_file_as_indexed(file_id, success, error_message)

	async def get_file_content(self, file_id: str, user_id: str) -> bytes:
		"""Download file content from MinIO for indexing purposes"""
		logger.info(f'[FileRepo.get_file_content] Getting file content for file: {file_id}, user: {user_id}')

		# Get file metadata
		file = self.file_dal.get_user_file_by_id(file_id, user_id)
		if not file:
			raise NotFoundException(_('file_not_found'))

		# Download file content from MinIO
		file_content = await file_service.get_file_content(file.file_path)
		logger.info(f'[FileRepo.get_file_content] Retrieved {len(file_content)} bytes for file: {file.name}')
		return file_content

	async def get_files_for_indexing(self, conversation_id: str) -> List[dict]:
		"""Get all files in conversation formatted for indexing service"""
		logger.info(f'[FileRepo.get_files_for_indexing] Getting files for indexing in conversation: {conversation_id}')

		# Get all files for conversation
		files = self.file_dal.get_all_files_for_conversation(conversation_id)

		logger.info(f'[FileRepo.get_files_for_indexing] Found {len(files)} files for conversation: {conversation_id}')
		# Format files for indexing service
		files_data = []
		for file in files:
			try:
				# Download file content
				file_content = await file_service.get_file_content(file.file_path)

				file_data = {
					'file_id': file.id,
					'file_name': file.original_name,
					'file_type': file.type,
					'file_content': file_content,
				}
				files_data.append(file_data)
				logger.info(f'[FileRepo.get_files_for_indexing] Prepared file {file.original_name} ({len(file_content)} bytes)')

			except Exception as e:
				logger.error(f'[FileRepo.get_files_for_indexing] Error preparing file {file.original_name}: {str(e)}')
				continue

		logger.info(f'[FileRepo.get_files_for_indexing] Prepared {len(files_data)} files for indexing')
		return files_data

	def bulk_mark_files_as_indexed(self, file_ids: List[str], success: bool = True):
		"""Mark multiple files as indexed"""
		logger.info(f'[FileRepo.bulk_mark_files_as_indexed] Marking {len(file_ids)} files as indexed: success={success}')

		with self.file_dal.transaction():
			for file_id in file_ids:
				self.file_dal.mark_file_as_indexed(file_id, success)

	async def _trigger_file_indexing_events(self, uploaded_files: List, conversation_id: str, user_id: str):
		"""Trigger file indexing events for uploaded files"""
		try:
			from app.modules.agent.events.file_indexing_events import (
				get_file_indexing_event_handler,
			)

			logger.info(f'\033[94m[FileRepo._trigger_file_indexing_events] Starting indexing for {len(uploaded_files)} files\033[0m')

			# Get event handler
			event_handler = get_file_indexing_event_handler(self.db)

			# Get file IDs
			file_ids = [file.id for file in uploaded_files]

			# Trigger batch indexing event
			result = await event_handler.handle_multiple_files_uploaded(file_ids, conversation_id, user_id)

			if result['success']:
				logger.info(f'\033[92m[FileRepo._trigger_file_indexing_events] Indexing completed successfully for conversation: {conversation_id}\033[0m')
			else:
				logger.error(f'\033[91m[FileRepo._trigger_file_indexing_events] Indexing failed: {result.get("error", "Unknown error")}\033[0m')

		except Exception as e:
			logger.error(f'\033[91m[FileRepo._trigger_file_indexing_events] Error triggering indexing events: {str(e)}\033[0m')
			raise
