"""Base Repo"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db


class BaseRepo:
	"""BaseRepo with common database session management"""

	def __init__(self, db: Session = Depends(get_db)):
		self.db = db

	def begin_transaction(self):
		"""Bắt đầu transaction"""
		self.db.begin()

	def commit(self):
		"""Commit transaction"""
		try:
			self.db.commit()
		except Exception as e:
			self.rollback()
			raise e

	def rollback(self):
		"""Rollback transaction nếu có lỗi"""
		self.db.rollback()

	def close(self):
		"""Đóng session"""
		self.db.close()
