"""Base DAL"""

from contextlib import contextmanager
from typing import Generic, Type, TypeVar

from sqlalchemy.orm import Session

from app.exceptions.exception import CustomHTTPException

T = TypeVar('T')  # Kiểu dữ liệu chung cho model


class BaseDAL(Generic[T]):
	"""BaseDAL"""

	def __init__(self, db: Session, model: Type[T]):
		self.db = db
		self.model = model

	def get_by_id(self, item_id: str):
		"""Lấy một bản ghi theo ID"""
		return self.db.query(self.model).filter(self.model.id == item_id).first()

	def get_all(self):
		"""Lấy tất cả bản ghi"""
		return self.db.query(self.model).all()

	def create(self, obj_data: dict):
		"""Tạo một bản ghi mới"""
		new_obj = self.model(**obj_data)
		self.db.add(new_obj)
		# Always flush to ensure the object gets an ID
		self.db.flush()
		# Only commit if we're not in a transaction context
		if not self.db.in_transaction():
			self.db.commit()
		# Always refresh to get the latest state
		self.db.refresh(new_obj)
		return new_obj

	def update(self, item_id: str, update_data: dict):
		"""Cập nhật một bản ghi"""
		obj = self.get_by_id(item_id)
		if not obj:
			return None
		for key, value in update_data.items():
			setattr(obj, key, value)
		if not self.db.in_transaction():
			self.db.commit()
			self.db.refresh(obj)
		return obj

	def delete(self, item_id: str):
		"""Xóa một bản ghi"""
		obj = self.get_by_id(item_id)
		if obj:
			if not self.db.in_transaction():
				self.db.delete(obj)
				self.db.commit()
			return True
		return False

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

	@contextmanager
	def transaction(self):
		"""Context manager để quản lý transaction."""
		try:
			# Nếu chưa có transaction nào, thì bắt đầu
			if not self.db.in_transaction():
				self.begin_transaction()

			yield  # Chạy code trong `with transaction()`

			# Commit nếu không có lỗi
			self.commit()
		except CustomHTTPException as ce:
			self.rollback()
			raise ce
		except Exception as e:
			self.rollback()
			raise e
