"""User data access layer"""

import logging
from contextlib import contextmanager

from sqlalchemy import and_

from app.core.base_dal import BaseDAL
from app.core.base_model import Pagination
from app.enums.base_enums import Constants
from app.modules.users.models.users import User
from app.utils.filter_utils import apply_dynamic_filters


class UserDAL(BaseDAL[User]):
	"""UserDAL"""

	def __init__(self, db):
		super().__init__(db, User)

	def get_user_by_email(self, email: str) -> User:
		"""Tìm user theo email"""
		return self.db.query(User).filter(User.email == email and User.is_deleted == 0).first()

	def get_user_by_google_id(self, google_id: str):
		"""Get user by Google ID

		Args:
		    google_id (str): Google user ID

		Returns:
		    User: User object if found, None otherwise
		"""
		try:
			return self.db.query(User).filter(User.google_id == google_id).first()
		except Exception as e:
			print(f'[ERROR] Failed to get user by Google ID: {e}')
			return None

	def get_user_by_id(self, user_id: str) -> User:
		"""Get user by ID

		Args:
		    user_id (int): The user's ID

		Returns:
		    User: User object if found, None otherwise
		"""
		return self.db.query(User).filter(and_(User.id == user_id, User.is_deleted == 0)).first()

	def get_user_by_username(self, username: str) -> User:
		"""Get user by username

		Args:
		    username (str): The user's username

		Returns:
		    User: User object if found, None otherwise
		"""
		return self.db.query(User).filter(and_(User.username == username, User.is_deleted == 0)).first()

	def search_users(self, params: dict) -> Pagination[User]:
		"""Search users with dynamic filters based on any User model field"""
		logger = logging.getLogger(__name__)

		logger.info(f'Searching users with parameters: {params}')
		page = int(params.get('page', 1))
		page_size = int(params.get('page_size', Constants.PAGE_SIZE))

		# Start with basic query
		query = self.db.query(User).filter(User.is_deleted == 0)

		# Apply dynamic filters using the common utility function
		query = apply_dynamic_filters(query, User, params)

		# Sort by creation date descending
		query = query.order_by(User.create_date.desc())

		# Count total records
		total_count = query.count()

		# Apply pagination
		users = query.offset((page - 1) * page_size).limit(page_size).all()

		logger.info(f'Found {total_count} users, returning page {page} with {len(users)} items')

		return Pagination(items=users, total_count=total_count, page=page, page_size=page_size)

	def count_users(self, params: dict = None) -> int:
		"""Count total number of users with optional filters
		
		Args:
		    params (dict): Optional filters to apply when counting users
		    
		Returns:
		    int: Total count of users matching the criteria
		"""
		logger = logging.getLogger(__name__)
		
		logger.info(f'Counting users with parameters: {params}')
		
		# Start with basic query
		query = self.db.query(User).filter(User.is_deleted == 0)
		
		# Apply dynamic filters if provided
		if params:
			query = apply_dynamic_filters(query, User, params)
		
		# Count total records
		total_count = query.count()
		
		logger.info(f'Total users count: {total_count}')
		
		return total_count

	@contextmanager
	def transaction(self):
		"""Create a transaction context

		This ensures that all database operations in the block are committed together,
		or rolled back if an exception occurs.

		Example:
		    with user_dal.transaction():
		        user = user_dal.create(user_data)
		        # Other operations that should be committed together
		"""
		try:
			yield
			self.db.commit()
		except Exception as e:
			self.db.rollback()
			raise e
