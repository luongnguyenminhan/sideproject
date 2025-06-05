from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.base_dal import BaseDAL
from app.core.base_model import Pagination
from app.modules.chat.models.file import File
from typing import Optional
import logging

logger = logging.getLogger(__name__)


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
		query = self.db.query(self.model).filter(self.model.user_id == user_id, self.model.is_deleted == False)

		# Apply file type filter
		if file_type:
			query = query.filter(self.model.type.ilike(f'{file_type}%'))

		# Apply search filter
		if search:
			query = query.filter(self.model.name.ilike(f'%{search}%'))

		# Apply conversation filter
		if conversation_id:
			query = query.filter(self.model.conversation_id == conversation_id)

		# Order by upload date descending
		query = query.order_by(desc(self.model.upload_date))

		# Count total records
		total_count = query.count()

		# Apply pagination
		conversations = query.offset((page - 1) * page_size).limit(page_size).all()


		paginated_result = Pagination(items=conversations, total_count=total_count, page=page, page_size=page_size)
		return paginated_result

	def get_user_file_by_id(self, file_id: str, user_id: str) -> Optional[File]:
		"""Get a specific file for a user"""
		file = (
			self.db.query(self.model)
			.filter(
				self.model.id == file_id,
				self.model.user_id == user_id,
				self.model.is_deleted == False,
			)
			.first()
		)
		return file

	def get_files_by_checksum(self, checksum: str, user_id: Optional[str] = None):
		"""Get files by checksum (for duplicate detection)"""
		query = self.db.query(self.model).filter(self.model.checksum == checksum, self.model.is_deleted == False)

		if user_id:
			query = query.filter(self.model.user_id == user_id)

		files = query.all()
		return files

	def get_conversation_files(
		self,
		user_id: str,
		conversation_id: str,
		page: int = 1,
		page_size: int = 10,
		file_type: Optional[str] = None,
		search: Optional[str] = None,
	):
		"""Get files for a specific conversation with pagination and filtering"""

		query = self.db.query(self.model).filter(
			self.model.user_id == user_id,
			self.model.conversation_id == conversation_id,
			self.model.is_deleted == False,
		)

		# Apply file type filter
		if file_type:
			query = query.filter(self.model.type.ilike(f'{file_type}%'))

		# Apply search filter
		if search:
			query = query.filter(self.model.name.ilike(f'%{search}%'))

		# Order by upload date descending
		query = query.order_by(desc(self.model.upload_date))

		# Count total records
		total_count = query.count()

		# Apply pagination
		files = query.offset((page - 1) * page_size).limit(page_size).all()

		paginated_result = Pagination(items=files, total_count=total_count, page=page, page_size=page_size)
		return paginated_result

	def get_unindexed_files_for_conversation(self, conversation_id: str) -> list[File]:
		"""Get all unindexed files for a specific conversation"""

		files = (
			self.db.query(self.model)
			.filter(
				self.model.conversation_id == conversation_id,
				self.model.is_deleted == False,
				self.model.is_indexed == False,
			)
			.all()
		)

		return files

	def get_all_files_for_conversation(self, conversation_id: str) -> list[File]:
		"""Get all files for a specific conversation (indexed and unindexed)"""

		files = (
			self.db.query(self.model)
			.filter(
				self.model.conversation_id == conversation_id,
				self.model.is_deleted == False,
			)
			.all()
		)

		return files

	def mark_file_as_indexed(self, file_id: str, success: bool = True, error_message: str = None):
		"""Mark a file as indexed (successfully or with error)"""
		from datetime import datetime


		file = self.db.query(self.model).filter(self.model.id == file_id).first()
		if file:
			file.is_indexed = success
			file.indexed_at = datetime.utcnow() if success else None
			file.indexing_error = error_message if not success else None
			self.db.commit()
		else:
			logger.warning(f'[FileDAL.mark_file_as_indexed] File {file_id} not found')
