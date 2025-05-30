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


class FileRepo:
	def __init__(self, db: Session = Depends(get_db)):
		self.db = db
		self.file_dal = FileDAL(db)

	async def upload_files(
		self,
		files: List[UploadFile],
		user_id: str,
		conversation_id: Optional[str] = None,
	):
		"""Upload multiple files and save metadata to database"""
		uploaded_files = []

		for i, file in enumerate(files):
			try:
				# Validate file
				if not file_service.validate_file(file):
					raise ValidationException(_('invalid_file'))

				# Calculate checksum
				checksum = await file_service.calculate_checksum(file)

				# Check for duplicates
				existing_files = self.file_dal.get_files_by_checksum(checksum, user_id)
				if existing_files:
					uploaded_files.append(existing_files[0])
					continue

				# Upload to MinIO
				file_path, url = await file_service.upload_to_storage(file, user_id, conversation_id)

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

				with self.file_dal.transaction():
					db_file = self.file_dal.create(file_data)
					uploaded_files.append(db_file)

			except Exception as e:
				raise ValidationException(f'Failed to upload file {file.filename}: {str(e)}')

		return uploaded_files

	def get_file_by_id(self, file_id: str, user_id: Optional[str] = None):
		"""Get file by ID with optional user ownership check"""
		if user_id:
			file = self.file_dal.get_user_file_by_id(file_id, user_id)
		else:
			file = self.file_dal.get_by_id(file_id)

		if not file:
			raise NotFoundException(_('file_not_found'))
		return file

	def get_user_files(self, user_id: str, request: FileListRequest):
		"""Get user's files with pagination and filtering"""
		print(
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
		return files

	def get_files_by_conversation(self, user_id: str, conversation_id: str, request: FileListRequest):
		"""Get files for a specific conversation with pagination and filtering"""
		print(
			f'\033[93m[FileRepo.get_files_by_conversation] Getting files for conversation: {conversation_id}, user: {user_id}, page: {request.page}, page_size: {request.page_size}, file_type: {request.file_type}, search: {request.search}\033[0m'
		)

		# Ensure conversation_id is set in request
		request.conversation_id = conversation_id

		files = self.file_dal.get_conversation_files(
			user_id=user_id,
			conversation_id=conversation_id,
			page=request.page,
			page_size=request.page_size,
			file_type=request.file_type,
			search=request.search,
		)
		return files

	async def delete_file(self, file_id: str, user_id: str):
		"""Delete file from MinIO and mark as deleted in database"""
		file = self.get_file_by_id(file_id, user_id)

		try:
			# Remove from MinIO
			await file_service.delete_from_storage(file.file_path)

			# Soft delete in database
			with self.file_dal.transaction():
				self.file_dal.delete(file_id)

			return True

		except Exception as e:
			raise ValidationException(f'Failed to delete file: {str(e)}')

	def get_file_download_url(self, file_id: str, user_id: Optional[str] = None, expires: int = 3600):
		"""Get temporary download URL for file"""
		file = self.get_file_by_id(file_id, user_id)

		# Increment download count
		with self.file_dal.transaction():
			self.file_dal.update(file_id, {'download_count': file.download_count + 1})

		# Generate download URL
		download_url = file_service.get_download_url(file.file_path, expires)
		return download_url
