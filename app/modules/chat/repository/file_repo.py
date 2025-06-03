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

				# Check for duplicates
				logger.info(f'\033[94m[FileRepo.upload_files] Checking for duplicates with checksum: {checksum}\033[0m')
				existing_files = self.file_dal.get_files_by_checksum(checksum, user_id)
				if existing_files:
					logger.info(f'\033[95m[FileRepo.upload_files] Duplicate found, returning existing file: {existing_files[0].id}\033[0m')
					uploaded_files.append(existing_files[0])
					continue

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
		logger.info(
			f'\033[93m[FileRepo.get_user_files] Getting files for user: {user_id}, page: {request.page}, page_size: {request.page_size}, file_type: {request.file_type}, search: {request.search}, conversation_id: {request.conversation_id}\033[0m'
		)
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
		logger.info(
			f'\033[93m[FileRepo.get_files_by_conversation] Getting files for conversation: {conversation_id}, user: {user_id}, page: {request.page}, page_size: {request.page_size}, file_type: {request.file_type}, search: {request.search}\033[0m'
		)
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
