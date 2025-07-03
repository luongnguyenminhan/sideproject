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

logger.info(f'MinIO config: endpoint={settings.MINIO_ENDPOINT}, access_key={settings.MINIO_ACCESS_KEY}, bucket_name={settings.MINIO_BUCKET_NAME}, secure={secure_value}')


class MinioHandler:
	"""
	MinIO Handler for managing file operations with MinIO object storage.
	"""

	def __init__(self):
		"""Initialize MinIO client with configuration from settings."""
		logger.info(f'Initializing MinIO client with endpoint: {settings.MINIO_ENDPOINT}')
		logger.info(f'Using bucket name: {settings.MINIO_BUCKET_NAME}')

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
		# self._ensure_bucket_exists()

	def _ensure_bucket_exists(self):
		"""Check if the bucket exists and create it if it doesn't."""
		try:
			if not self.minio_client.bucket_exists(self.bucket_name):
				self.minio_client.make_bucket(self.bucket_name)
				logger.info(f'Bucket {self.bucket_name} created successfully')
			else:
				logger.info(f'Bucket {self.bucket_name} already exists')
		except S3Error as err:
			logger.error(f'Error checking/creating bucket: {err}')
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
		bucket_name: str = None,
		object_name: str = None,
		file_path: str = None,
		file_content: bytes = None,
		content_type: str = 'application/octet-stream',
	) -> str:
		"""
		Upload file to MinIO với flexible parameters cho CV generation

		Args:
		        bucket_name: Bucket name (optional, dùng default nếu None)
		        object_name: Object name/path trong bucket
		        file_path: Path tới file trên disk (nếu upload từ file)
		        file_content: Binary content (nếu upload từ memory)
		        content_type: MIME type của file

		Returns:
		        Object name sau khi upload
		"""
		try:
			bucket = bucket_name or self.bucket_name

			# Ensure bucket exists
			if not self.minio_client.bucket_exists(bucket):
				self.minio_client.make_bucket(bucket)
				logger.info(f'Created bucket: {bucket}')

			if file_content:
				# Upload từ memory
				file_data = io.BytesIO(file_content)
				file_size = len(file_content)
				logger.info(f'Uploading from memory: {object_name}, size: {file_size} bytes')
			elif file_path:
				# Upload từ file path
				file_size = os.path.getsize(file_path)
				with open(file_path, 'rb') as file_data:
					logger.info(f'Uploading from file: {file_path} -> {object_name}, size: {file_size} bytes')
					self.minio_client.put_object(
						bucket_name=bucket,
						object_name=object_name,
						data=file_data,
						length=file_size,
						content_type=content_type,
					)
				return object_name
			else:
				raise ValueError('Either file_path or file_content must be provided')

			# Upload the file
			self.minio_client.put_object(
				bucket_name=bucket,
				object_name=object_name,
				data=file_data,
				length=file_size,
				content_type=content_type,
			)

			logger.info(f'File uploaded successfully: {object_name}')
			return object_name

		except S3Error as err:
			logger.error(f'Error uploading file to MinIO: {err}')
			raise
		except Exception as e:
			logger.error(f'Unexpected error uploading file: {str(e)}')
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

			# Generate object name
			object_name = self._generate_safe_object_name(meeting_id, file.filename, file_type)

			# Use the new upload_file method
			return await self.upload_file(
				bucket_name=self.bucket_name,
				object_name=object_name,
				file_content=file_content,
				content_type=file.content_type or 'application/octet-stream',
			)

		except Exception as err:
			logger.error(f'Error uploading FastAPI file to MinIO: {err}')
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
			logger.info(f"Starting upload of '{filename}' as bytes, size: {len(content)} bytes")

			# Generate object name
			object_name = self._generate_safe_object_name(meeting_id, filename, file_type)

			# Use the new upload_file method
			return await self.upload_file(
				bucket_name=self.bucket_name,
				object_name=object_name,
				file_content=content,
				content_type=content_type,
			)

		except Exception as e:
			logger.error(f'Unexpected error uploading bytes to MinIO: {str(e)}')
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
			logger.info(f'Attempting to download: {object_name}')

			# Get file from MinIO
			response = self.minio_client.get_object(bucket_name=self.bucket_name, object_name=object_name)

			# Read all data
			file_content = response.read()

			# Get just the filename from the object path
			file_name = os.path.basename(object_name)

			# Close the response
			response.close()
			response.release_conn()

			logger.info(f"File '{object_name}' downloaded successfully from MinIO")
			return file_content, file_name

		except S3Error as err:
			logger.error(f'Error downloading file from MinIO: {err}')
			raise
		except Exception as err:
			logger.error(f'File not found in MinIO: {err}')
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

			logger.info(f'Generated presigned URL for: {object_name}')
			return url

		except S3Error as err:
			logger.error(f'Error generating presigned URL: {err}')
			raise
		except FileNotFoundError as err:
			logger.error(f'File not found when generating URL: {err}')
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
			logger.info(f"File '{object_name}' removed successfully from MinIO")
			return True

		except S3Error as err:
			logger.error(f'Error removing file from MinIO: {err}')
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
			logger.info(f'Getting file content: {object_name}')

			# Get file from MinIO
			response = self.minio_client.get_object(bucket_name=self.bucket_name, object_name=object_name)

			# Read all data
			file_content = response.read()

			# Close the response
			response.close()
			response.release_conn()

			logger.info(f'File content retrieved successfully: {len(file_content)} bytes')
			return file_content

		except S3Error as err:
			logger.error(f'Error getting file content from MinIO: {err}')
			raise
		except Exception as err:
			logger.error(f'File not found in MinIO: {err}')
			raise

	async def get_presigned_url(self, bucket_name: str, object_name: str, expires_in: int = 3600) -> str:
		"""
		Get presigned URL cho file download

		Args:
		        bucket_name: Bucket name
		        object_name: Object name trong bucket
		        expires_in: Thời gian expire (seconds)

		Returns:
		        Presigned URL
		"""
		try:
			from datetime import timedelta

			url = self.minio_client.presigned_get_object(
				bucket_name=bucket_name,
				object_name=object_name,
				expires=timedelta(seconds=expires_in),
			)

			logger.info(f'Generated presigned URL for: {object_name} (expires in {expires_in}s)')
			return url

		except S3Error as err:
			logger.error(f'Error generating presigned URL: {err}')
			raise


# Create a singleton instance
minio_handler = MinioHandler()
