from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.base_dal import BaseDAL
from app.core.base_model import Pagination
from app.modules.chat.models.file import File
from typing import Optional


class FileDAL(BaseDAL[File]):
    def __init__(self, db: Session):
        print(
            f"\033[96m[FileDAL.__init__] Initializing FileDAL with db session: {db}\033[0m"
        )
        super().__init__(db, File)
        print(f"\033[92m[FileDAL.__init__] FileDAL initialized successfully\033[0m")

    def get_user_files(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 10,
        file_type: Optional[str] = None,
        search: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ):
        """Get files for a user with pagination and filtering"""
        print(
            f"\033[93m[FileDAL.get_user_files] Getting files for user: {user_id}, page: {page}, page_size: {page_size}, file_type: {file_type}, search: {search}, conversation_id: {conversation_id}\033[0m"
        )
        query = self.db.query(self.model).filter(
            self.model.user_id == user_id, self.model.is_deleted == False
        )
        print(
            f"\033[94m[FileDAL.get_user_files] Base query created for user files\033[0m"
        )

        # Apply file type filter
        if file_type:
            print(
                f"\033[94m[FileDAL.get_user_files] Applying file type filter: {file_type}\033[0m"
            )
            query = query.filter(self.model.type.ilike(f"{file_type}%"))

        # Apply search filter
        if search:
            print(
                f"\033[94m[FileDAL.get_user_files] Applying search filter: {search}\033[0m"
            )
            query = query.filter(self.model.name.ilike(f"%{search}%"))

        # Apply conversation filter
        if conversation_id:
            print(
                f"\033[94m[FileDAL.get_user_files] Applying conversation filter: {conversation_id}\033[0m"
            )
            query = query.filter(self.model.conversation_id == conversation_id)

        # Order by upload date descending
        print(
            f"\033[94m[FileDAL.get_user_files] Ordering by upload date descending\033[0m"
        )
        query = query.order_by(desc(self.model.upload_date))

                # Count total records
        total_count = query.count()

        # Apply pagination
        conversations = query.offset((page - 1) * page_size).limit(page_size).all()

        print(f'Found {total_count} conversations, returning page {page} with {len(conversations)} items')

        paginated_result = Pagination(items=conversations, total_count=total_count, page=page, page_size=page_size)
        print(
            f"\033[92m[FileDAL.get_user_files] Pagination completed, returning results\033[0m"
        )
        return paginated_result

    def get_user_file_by_id(self, file_id: str, user_id: str) -> Optional[File]:
        """Get a specific file for a user"""
        print(
            f"\033[93m[FileDAL.get_user_file_by_id] Getting file by ID: {file_id} for user: {user_id}\033[0m"
        )
        file = (
            self.db.query(self.model)
            .filter(
                self.model.id == file_id,
                self.model.user_id == user_id,
                self.model.is_deleted == False,
            )
            .first()
        )
        if file:
            print(
                f"\033[92m[FileDAL.get_user_file_by_id] Found file: {file.name}, size: {file.size}, type: {file.type}\033[0m"
            )
        else:
            print(
                f"\033[95m[FileDAL.get_user_file_by_id] File not found: {file_id}\033[0m"
            )
        return file

    def get_files_by_checksum(self, checksum: str, user_id: Optional[str] = None):
        """Get files by checksum (for duplicate detection)"""
        print(
            f"\033[93m[FileDAL.get_files_by_checksum] Getting files by checksum: {checksum}, user_id: {user_id}\033[0m"
        )
        query = self.db.query(self.model).filter(
            self.model.checksum == checksum, self.model.is_deleted == False
        )

        if user_id:
            print(
                f"\033[94m[FileDAL.get_files_by_checksum] Filtering by user_id: {user_id}\033[0m"
            )
            query = query.filter(self.model.user_id == user_id)

        files = query.all()
        print(
            f"\033[92m[FileDAL.get_files_by_checksum] Found {len(files)} files with checksum: {checksum}\033[0m"
        )
        return files
