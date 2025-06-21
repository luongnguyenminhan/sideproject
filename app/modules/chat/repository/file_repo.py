from pytz import timezone
from sqlalchemy.orm import Session
from fastapi import Depends, UploadFile

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.database import get_db

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.base_repo import BaseRepo
from ..dal.file_dal import FileDAL
from ..schemas.file_request import FileListRequest
from .services.file_service import file_service

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.exceptions.exception import NotFoundException, ValidationException

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.middleware.translation_manager import _
from datetime import datetime
from typing import List, Optional
import logging
import asyncio

logger = logging.getLogger(__name__)


class FileRepo(BaseRepo):
    def __init__(self, db: Session = Depends(get_db)):
        super().__init__(db)
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
                    raise ValidationException(_("invalid_file"))

                # Calculate checksum
                checksum = await file_service.calculate_checksum(file)

                # Skip duplicate check - allow all uploads

                # Upload to MinIO
                file_path, url = await file_service.upload_to_storage(
                    file, user_id, conversation_id
                )

                # Create file record in database
                file_data = {
                    "name": file.filename,
                    "original_name": file.filename,
                    "file_path": file_path,
                    "file_url": url,
                    "size": file.size or 0,
                    "type": file.content_type
                    or file_service.get_content_type(file.filename),
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "upload_date": datetime.now(
                        timezone("Asia/Ho_Chi_Minh")
                    ).isoformat(),
                    "checksum": checksum,
                    "minio_bucket": "default",
                }

                with self.file_dal.transaction():
                    db_file = self.file_dal.create(file_data)
                    uploaded_files.append(db_file)

            except Exception as e:
                raise ValidationException(
                    f"Failed to upload file {file.filename}: {str(e)}"
                )

        # Trigger indexing events cho uploaded files nếu có conversation_id
        if conversation_id and uploaded_files:
            try:
                await self._trigger_file_indexing_events(
                    uploaded_files, conversation_id, user_id
                )
            except Exception as e:
                logger.error(
                    f"\033[91m[FileRepo.upload_files] Error triggering indexing events: {str(e)}\033[0m"
                )
                # Don't fail the upload if indexing fails

        return uploaded_files

    def get_file_by_id(self, file_id: str, user_id: Optional[str] = None):
        """Get file by ID with optional user ownership check"""
        if user_id:
            file = self.file_dal.get_user_file_by_id(file_id, user_id)
        else:
            file = self.file_dal.get_by_id(file_id)

        if not file:
            raise NotFoundException(_("file_not_found"))
        return file

    def get_user_files(self, user_id: str, request: FileListRequest):
        """Get user's files with pagination and filtering"""
        files = self.file_dal.get_user_files(
            user_id=user_id,
            page=request.page,
            page_size=request.page_size,
            file_type=request.file_type,
            search=request.search,
            conversation_id=request.conversation_id,
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
            raise ValidationException(f"Failed to delete file: {str(e)}")

    def get_file_download_url(
        self, file_id: str, user_id: Optional[str] = None, expires: int = 3600
    ):
        """Get temporary download URL for file"""
        file = self.get_file_by_id(file_id, user_id)

        # Increment download count
        with self.file_dal.transaction():
            self.file_dal.update(file_id, {"download_count": file.download_count + 1})

        # Generate download URL
        download_url = file_service.get_download_url(file.file_path, expires)
        return download_url

    def get_files_by_conversation(
        self,
        user_id: str,
        conversation_id: str,
        request: FileListRequest,
    ):
        """Get files for a specific conversation with pagination and filtering"""
        files = self.file_dal.get_conversation_files(
            user_id=user_id,
            conversation_id=conversation_id,
            page=request.page,
            page_size=request.page_size,
            file_type=request.file_type,
            search=request.search,
        )
        return files

    def get_unindexed_files_for_conversation(self, conversation_id: str):
        """Get all unindexed files for a specific conversation"""
        return self.file_dal.get_unindexed_files_for_conversation(conversation_id)

    def get_all_files_for_conversation(self, conversation_id: str):
        """Get all files for a specific conversation"""
        return self.file_dal.get_all_files_for_conversation(conversation_id)

    def mark_file_as_indexed(
        self, file_id: str, success: bool = True, error_message: str = None
    ):
        """Mark a file as indexed"""
        return self.file_dal.mark_file_as_indexed(file_id, success, error_message)

    async def get_file_content(self, file_id: str, user_id: str) -> bytes:
        """Download file content from MinIO for indexing purposes"""

        # Get file metadata
        file = self.file_dal.get_user_file_by_id(file_id, user_id)
        if not file:
            raise NotFoundException(_("file_not_found"))

        # Download file content from MinIO
        file_content = await file_service.get_file_content(file.file_path)
        return file_content

    async def get_files_for_indexing(self, conversation_id: str) -> List[dict]:
        """Get all files in conversation formatted for indexing service"""

        # Get all files for conversation
        files = self.file_dal.get_all_files_for_conversation(conversation_id)

        # Format files for indexing service
        files_data = []
        for file in files:
            try:
                # Download file content
                file_content = await file_service.get_file_content(file.file_path)

                file_data = {
                    "file_id": file.id,
                    "file_name": file.original_name,
                    "file_type": file.type,
                    "file_content": file_content,
                }
                files_data.append(file_data)

            except Exception as e:
                logger.error(
                    f"[FileRepo.get_files_for_indexing] Error preparing file {file.original_name}: {str(e)}"
                )
                continue

        return files_data

    def bulk_mark_files_as_indexed(self, file_ids: List[str], success: bool = True):
        """Mark multiple files as indexed"""

        with self.file_dal.transaction():
            for file_id in file_ids:
                self.file_dal.mark_file_as_indexed(file_id, success)

    async def _trigger_file_indexing_events(
        self, uploaded_files: List, conversation_id: str, user_id: str
    ):
        """Trigger file indexing events for uploaded files"""
        try:
            from app.modules.agent.events.file_indexing_events import (
                get_file_indexing_event_handler,
            )

            # Get event handler
            event_handler = get_file_indexing_event_handler(self.db)

            # Get file IDs
            file_ids = [file.id for file in uploaded_files]

            # Trigger batch indexing event
            result = await event_handler.handle_multiple_files_uploaded(
                file_ids, conversation_id, user_id
            )

            if result["success"]:
                pass
            else:
                logger.error(
                    f'\033[91m[FileRepo._trigger_file_indexing_events] Indexing failed: {result.get("error", "Unknown error")}\033[0m'
                )

        except Exception as e:
            logger.error(
                f"\033[91m[FileRepo._trigger_file_indexing_events] Error triggering indexing events: {str(e)}\033[0m"
            )
            raise
