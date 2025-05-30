from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.base_dal import BaseDAL
from app.core.base_model import Pagination
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
		print(
			f'\033[93m[FileDAL.get_user_files] Getting files for user: {user_id}, page: {page}, page_size: {page_size}, file_type: {file_type}, search: {search}, conversation_id: {conversation_id}\033[0m'
		)
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
		print(
			f'\033[93m[FileDAL.get_conversation_files] Getting files for conversation: {conversation_id}, user: {user_id}, page: {page}, page_size: {page_size}, file_type: {file_type}, search: {search}\033[0m'
		)

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
