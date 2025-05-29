"""File service for chat system"""

import hashlib
import os
from datetime import datetime
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.modules.chat.models.file import File
from app.utils.minio.minio_handler import minio_handler
from app.exceptions.exception import ValidationException, NotFoundException


class FileService:
    """Service for file operations"""

    def __init__(self, db: Session):
        self.db = db

    async def upload_file(
        self, file: UploadFile, user_id: str, conversation_id: str = None
    ) -> File:
        """Upload file to MinIO and save metadata to database"""
        try:
            # Validate file
            if not file.filename:
                raise ValidationException("File name is required")

            # Read file content to get size and checksum
            file_content = await file.read()
            file_size = len(file_content)

            # Calculate MD5 checksum for integrity
            checksum = hashlib.md5(file_content).hexdigest()

            # Reset file pointer
            await file.seek(0)

            # Upload to MinIO
            minio_object_path = await minio_handler.upload_fastapi_file(
                file=file,
                meeting_id=conversation_id
                or user_id,  # Use conversation_id or user_id for organization
                file_type="chat_files",
            )

            # Create file record in database
            db_file = File(
                name=file.filename,
                original_name=file.filename,
                file_path=minio_object_path,
                size=file_size,
                type=file.content_type or "application/octet-stream",
                user_id=user_id,
                upload_date=datetime.utcnow(),
                checksum=checksum,
                minio_bucket=minio_handler.bucket_name,
                is_public=False,
            )

            self.db.add(db_file)
            self.db.commit()
            self.db.refresh(db_file)

            return db_file

        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to upload file: {str(e)}")

    def get_file_by_id(self, file_id: str, user_id: str = None) -> Optional[File]:
        """Get file by ID with optional user ownership check"""
        query = self.db.query(File).filter(File.id == file_id, File.is_deleted == False)

        if user_id:
            query = query.filter(File.user_id == user_id)

        return query.first()

    def get_user_files(
        self, user_id: str, page: int = 1, page_size: int = 10
    ) -> List[File]:
        """Get user's files with pagination"""
        offset = (page - 1) * page_size

        return (
            self.db.query(File)
            .filter(File.user_id == user_id, File.is_deleted == False)
            .order_by(File.upload_date.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

    async def delete_file(self, file_id: str, user_id: str) -> bool:
        """Delete file from MinIO and mark as deleted in database"""
        file = self.get_file_by_id(file_id, user_id)
        if not file:
            raise NotFoundException("File")

        try:
            # Remove from MinIO
            minio_handler.remove_file(file.file_path)

            # Soft delete in database
            file.is_deleted = True
            self.db.commit()

            return True

        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to delete file: {str(e)}")

    async def get_file_download_url(
        self, file_id: str, user_id: str = None, expires: int = 3600
    ) -> str:
        """Get temporary download URL for file"""
        file = self.get_file_by_id(file_id, user_id)
        if not file:
            raise NotFoundException("File")

        # Increment download count
        file.increment_download_count()
        self.db.commit()

        # Generate presigned URL
        return minio_handler.get_file_url(file.file_path, expires=expires)

    async def download_file(
        self, file_id: str, user_id: str = None
    ) -> tuple[bytes, str]:
        """Download file content"""
        file = self.get_file_by_id(file_id, user_id)
        if not file:
            raise NotFoundException("File")

        # Increment download count
        file.increment_download_count()
        self.db.commit()

        # Download from MinIO
        file_content, filename = minio_handler.download_file(file.file_path)
        return file_content, file.original_name
