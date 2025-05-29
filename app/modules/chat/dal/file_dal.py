from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.base_dal import BaseDAL
from app.modules.chat.models.file import File
from typing import Optional


class FileDAL(BaseDAL[File]):
    def __init__(self, db: Session):
        super().__init__(db, File)

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
        query = self.db.query(self.model).filter(
            self.model.user_id == user_id, self.model.is_deleted == False
        )

        # Apply file type filter
        if file_type:
            query = query.filter(self.model.type.ilike(f"{file_type}%"))

        # Apply search filter
        if search:
            query = query.filter(self.model.name.ilike(f"%{search}%"))

        # Apply conversation filter
        if conversation_id:
            query = query.filter(self.model.conversation_id == conversation_id)

        # Order by upload date descending
        query = query.order_by(desc(self.model.upload_date))

        return self.paginate(query, page, page_size)

    def get_user_file_by_id(self, file_id: str, user_id: str) -> Optional[File]:
        """Get a specific file for a user"""
        return (
            self.db.query(self.model)
            .filter(
                self.model.id == file_id,
                self.model.user_id == user_id,
                self.model.is_deleted == False,
            )
            .first()
        )

    def get_files_by_checksum(self, checksum: str, user_id: Optional[str] = None):
        """Get files by checksum (for duplicate detection)"""
        query = self.db.query(self.model).filter(
            self.model.checksum == checksum, self.model.is_deleted == False
        )

        if user_id:
            query = query.filter(self.model.user_id == user_id)

        return query.all()
