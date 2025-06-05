"""
MinIO Handler for file storage operations.
This utility class provides methods for uploading, downloading, and managing files in MinIO object storage.
"""

import io
import logging
import os
import uuid
from typing import Tuple

from fastapi import UploadFile

from app.core.config import get_settings
from minio import Minio
from minio.error import S3Error  # type: ignore

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
settings = get_settings()

# Ensure the secure parameter is a boolean, not a string
secure_value = settings.MINIO_SECURE
if isinstance(secure_value, str):
	secure_value = secure_value.lower() == 'true'



class MinioHandler:
	"""
	MinIO Handler for managing file operations with MinIO object storage.
	"""

	def __init__(self):
		"""Initialize MinIO client with configuration from settings."""

		# Ensure secure is a boolean
		secure_param = settings.MINIO_SECURE
		if isinstance(secure_param, str):
			secure_param = secure_param.lower() == 'true'

		self.minio_client = Minio(
			endpoint=settings.MINIO_ENDPOINT,
			access_key=settings.MINIO_ACCESS_KEY,
			secret_key=settings.MINIO_SECRET_KEY,
			secure=secure_param,  # Use the parsed boolean value
		)
		self.bucket_name = settings.MINIO_BUCKET_NAME
		self._ensure_bucket_exists()

	def _ensure_bucket_exists(self):
		"""Check if the bucket exists and create it if it doesn't."""
		try:
			if not self.minio_client.bucket_exists(self.bucket_name):
				self.minio_client.make_bucket(self.bucket_name)
			else:
				logger.info(f'Bucket {self.bucket_name} already exists.')
		except S3Error as err:
			raise

	def _generate_safe_object_name(self, meeting_id: str, file_name: str, file_type: str = 'audio') -> str:
		"""
		Generate a safe object name using UUID to avoid path and character issues.

		Args:
		    meeting_id: Meeting ID for organizing files
		    file_name: Original file name
		    file_type: Type of file (audio, document, etc.)

		Returns:
		    A safe object name for MinIO storage
		"""
		# Generate a UUID for uniqueness
		unique_id = str(uuid.uuid4())

		# Get file extension if it exists
		_, ext = os.path.splitext(file_name)

		# Create a safe object name with file_type/ prefix, UUID, and original extension
		safe_name = f'{file_type}/{meeting_id}/{unique_id}{ext}'

		return safe_name

	async def upload_file(
		self,
		file_content: bytes,
		file_name: str,
		meeting_id: str,
		content_type: str = 'audio/mpeg',
		file_type: str = 'audio',
	) -> str:
		"""
		Upload a file to MinIO.

		Args:
		    file_content: The binary content of the file
		    file_name: The name to save the file as
		    meeting_id: Meeting ID for organizing files
		    content_type: The content type of the file
		    file_type: Type of file for folder organization

		Returns:
		    The object name (path) in MinIO storage
		"""
		try:

			# Convert bytes to file-like object
			file_data = io.BytesIO(file_content)
			file_size = len(file_content)

			# Generate a safe object name with UUID, meeting_id and file_type
			object_name = self._generate_safe_object_name(meeting_id, file_name, file_type)

			# Upload the file to MinIO
			self.minio_client.put_object(
				bucket_name=self.bucket_name,
				object_name=object_name,
				data=file_data,
				length=file_size,
				content_type=content_type,
			)

			return object_name

		except S3Error as err:
			raise
		except Exception as e:
			raise

	async def upload_fastapi_file(self, file: UploadFile, meeting_id: str, file_type: str = 'audio') -> str:
		"""
		Upload a FastAPI UploadFile to MinIO.

		Args:
		    file: The FastAPI UploadFile object
		    meeting_id: Meeting ID for organizing files
		    file_type: Type of file for folder organization

		Returns:
		    The object name (path) in MinIO storage
		"""
		try:
			# Read file content
			file_content = await file.read()

			# Reset file cursor
			await file.seek(0)

			# Use the upload_file method
			return await self.upload_file(
				file_content=file_content,
				file_name=file.filename,
				meeting_id=meeting_id,
				content_type=file.content_type or 'application/octet-stream',
				file_type=file_type,
			)

		except Exception as err:
			raise

	async def upload_bytes(
		self,
		content: bytes,
		filename: str,
		meeting_id: str,
		file_type: str = 'document',
		content_type: str = 'application/pdf',
	) -> str:
		"""
		Upload bytes directly to MinIO.

		Args:
		    content: The binary content to upload
		    filename: The name for the file
		    meeting_id: Meeting ID for organizing files
		    file_type: Type of file for folder organization
		    content_type: The MIME type of the content

		Returns:
		    The object name (path) in MinIO storage
		"""
		try:

			# Convert bytes to file-like object
			file_data = io.BytesIO(content)
			file_size = len(content)

			# Generate a safe object name with UUID, meeting_id and file_type
			object_name = self._generate_safe_object_name(meeting_id, filename, file_type)

			# Upload the content to MinIO
			self.minio_client.put_object(
				bucket_name=self.bucket_name,
				object_name=object_name,
				data=file_data,
				length=file_size,
				content_type=content_type,
			)

			return object_name

		except S3Error as err:
			raise
		except Exception as e:
			raise

	def download_file(self, object_name: str) -> Tuple[bytes, str]:
		"""
		Download a file from MinIO.

		Args:
		    object_name: The path of the object in MinIO storage

		Returns:
		    Tuple containing (file_content, file_name)
		"""
		try:
			# First normalize the path to avoid double slashes
			object_name = object_name.replace('//', '/')

			# Get file from MinIO
			response = self.minio_client.get_object(bucket_name=self.bucket_name, object_name=object_name)

			# Read all data
			file_content = response.read()

			# Get just the filename from the object path
			file_name = os.path.basename(object_name)

			# Close the response
			response.close()
			response.release_conn()

			return file_content, file_name

		except S3Error as err:
			raise
		except Exception as err:
			raise

	def get_file_url(self, object_name: str, expires: int | None = None) -> str:
		"""
		Get a presigned URL for a file.

		Args:
		    object_name: The path of the object in MinIO
		    expires: Expiration time in seconds (None for server default, typically 7 days)

		Returns:
		    A presigned URL for the file
		"""
		try:
			from datetime import timedelta

			expires_delta = timedelta(seconds=expires) if expires else timedelta(days=7)

			url = self.minio_client.presigned_get_object(
				bucket_name=self.bucket_name,
				object_name=object_name,
				expires=expires_delta,
			)

			return url

		except S3Error as err:
			raise
		except FileNotFoundError as err:
			raise

	def remove_file(self, object_name: str) -> bool:
		"""
		Remove a file from MinIO.

		Args:
		    object_name: The path of the object in MinIO

		Returns:
		    True if successful, False otherwise
		"""
		try:
			self.minio_client.remove_object(bucket_name=self.bucket_name, object_name=object_name)
			return True

		except S3Error as err:
			return False

	def get_file_content(self, object_name: str) -> bytes:
		"""
		Get file content as bytes from MinIO.

		Args:
		    object_name: The path of the object in MinIO storage

		Returns:
		    File content as bytes
		"""
		try:
			# First normalize the path to avoid double slashes
			object_name = object_name.replace('//', '/')

			# Get file from MinIO
			response = self.minio_client.get_object(bucket_name=self.bucket_name, object_name=object_name)

			# Read all data
			file_content = response.read()

			# Close the response
			response.close()
			response.release_conn()

			return file_content

		except S3Error as err:
			raise
		except Exception as err:
			raise


# Create a singleton instance
minio_handler = MinioHandler()
