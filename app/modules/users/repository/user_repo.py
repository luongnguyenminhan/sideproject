"""User repo"""

import logging

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.base_model import Pagination
from app.core.base_repo import BaseRepo
from app.core.database import get_db
from app.exceptions.exception import CustomHTTPException, NotFoundException
from app.middleware.translation_manager import _
from app.modules.users.dal.user_dal import UserDAL
from app.modules.users.dal.user_logs_dal import UserLogDAL
from app.modules.users.models.users import User
from app.modules.users.schemas.users import SearchUserRequest
from app.utils.password_utils import PasswordUtils
from fastapi import status

logger = logging.getLogger(__name__)


class UserRepo(BaseRepo):
	"""UserRepo"""

	def __init__(self, db: Session = Depends(get_db)):
		"""__init__"""
		self.db = db
		self.user_dal = UserDAL(db)
		self.user_logs_dal = UserLogDAL(db)

	def search_users(self, request: SearchUserRequest) -> Pagination[User]:
		try:
			result = self.user_dal.search_users(request.model_dump())
			return result
		except Exception as ex:
			raise ex

	def get_user_by_id(self, user_id: str) -> User:
		"""
		Retrieve a user by their ID

		Args:
		    user_id: The ID of the user to retrieve

		Returns:
		    The user model if found, otherwise None
		"""
		try:
			return self.user_dal.get_by_id(user_id)
		except Exception as ex:
			raise ex

	def update_user(self, user_id: str, data: dict) -> User:
		"""
		Update a user's information

		Args:
		    user_id: The ID of the user to update
		    data: A dictionary containing the fields to update

		Returns:
		    The updated user model
		"""
		try:
			user = self.user_dal.get_by_id(user_id)
			if not user:
				raise CustomHTTPException(message=_('user_not_found'))

			# Hash the password if it is being updated
			if 'password' in data:
				data['password'] = PasswordUtils.hash_password(data['password'])
			if 'username' in data:
				existing_user = self.user_dal.get_user_by_username(data['username'])
				if existing_user and existing_user.id != user_id:
					raise CustomHTTPException(
						message=_('username_already_exists'),
					)

			# Update the user fields
			for key, value in data.items():
				setattr(user, key, value)

			with self.user_logs_dal.transaction():
				self._log_user_action(
					str(user.id),
					'updated_profile',
					'User profile updated successfully',
				)

			self.db.commit()
			return user
		except Exception as ex:
			raise ex

	def delete_user(self, user_id: str) -> bool:
		"""
		Soft delete a user by setting is_deleted to True

		Args:
		    user_id: The ID of the user to delete

		Returns:
		    True if the user was successfully deleted, False otherwise
		"""
		try:
			user = self.user_dal.get_by_id(user_id)
			if not user:
				raise CustomHTTPException(message=_('user_not_found'))

			# Set is_deleted to True instead of actually deleting the record
			user.is_deleted = True

			with self.user_logs_dal.transaction():
				self._log_user_action(
					str(user.id),
					'deleted_user',
					'User was soft deleted successfully',
				)

			self.db.commit()
			return True
		except Exception as ex:
			raise ex

	def _log_user_action(self, user_id: str, action: str, details: str):
		"""Log user action

		Args:
		    user_id (str): User ID
		    action (str): Action performed
		    details (str): Details of the action
		"""
		try:
			if not user_id or user_id == 'None':
				return

			if hasattr(self, 'user_logs_dal'):
				log_data = {'user_id': user_id, 'action': action, 'details': details}
				self.user_logs_dal.create(log_data)
		except Exception as ex:
			# Just log the error, don't raise an exception as logging failure
			# shouldn't affect the main functionality
			logger.error(f'Logging error for user {user_id}: {ex}')

	def update_password(self, user: User, param) -> bool:
		password_utils = PasswordUtils()
		current_password = user.password_hash

		password_utils.validate_password(param['new_password'])
		if not password_utils.verify_password(param['current_password'], current_password):
			raise CustomHTTPException(
				message=_('current_password_incorrect'),
			)

		user.password_hash = password_utils.hash_password(param['new_password'])
		with self.user_logs_dal.transaction():
			self._log_user_action(str(user.id), 'updated_password', 'User password updated successfully')

		self.db.commit()
		return True
