"""File service for chat system"""

import hashlib
import mimetypes
from typing import List, Optional
from fastapi import UploadFile
from app.utils.minio.minio_handler import minio_handler
from app.modules.chat.models.file import File
import logging

logger = logging.getLogger(__name__)


class FileService:
	"""Service for handling file operations"""

	@staticmethod
	def validate_file(file: UploadFile) -> bool:
		"""Validate uploaded file"""
		if not file.filename:
			return False

		# Check file size (max 50MB)
		if file.size and file.size > 50 * 1024 * 1024:
			return False

		# Check allowed file types
		allowed_types = [
			'image/',
			'video/',
			'audio/',
			'text/',
			'application/pdf',
			'application/msword',
			'application/vnd.openxmlformats-officedocument',
		]

		if file.content_type:
			if not any(file.content_type.startswith(allowed_type) for allowed_type in allowed_types):
				return False

		return True

	@staticmethod
	async def calculate_checksum(file: UploadFile) -> str:
		"""Calculate MD5 checksum for file integrity"""
		content = await file.read()
		await file.seek(0)  # Reset file pointer
		return hashlib.md5(content).hexdigest()

	@staticmethod
	def get_content_type(filename: str) -> str:
		"""Get content type from filename"""
		content_type, _ = mimetypes.guess_type(filename)
		return content_type or 'application/octet-stream'

	@staticmethod
	async def upload_to_storage(file: UploadFile, user_id: str, conversation_id: Optional[str] = None) -> str:
		"""Upload file to MinIO storage"""
		try:
			# Upload to MinIO
			object_path = await minio_handler.upload_fastapi_file(
				file=file,
				meeting_id=conversation_id or user_id,
				file_type='chat_files',
			)

			logger.info(f'File uploaded to MinIO: {object_path}')
			return object_path

		except Exception as e:
			logger.error(f'Error uploading file to storage: {e}')
			raise

	@staticmethod
	async def delete_from_storage(file_path: str) -> bool:
		"""Delete file from MinIO storage"""
		try:
			success = minio_handler.remove_file(file_path)
			if success:
				logger.info(f'File deleted from MinIO: {file_path}')
			return success
		except Exception as e:
			logger.error(f'Error deleting file from storage: {e}')
			return False

	@staticmethod
	def get_download_url(file_path: str, expires: int = 3600) -> str:
		"""Get temporary download URL for file"""
		try:
			return minio_handler.get_file_url(file_path, expires=expires)
		except Exception as e:
			logger.error(f'Error generating download URL: {e}')
			raise


# Singleton instance
file_service = FileService()
