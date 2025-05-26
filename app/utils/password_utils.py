"""
Password Management Utility

This file defines the PasswordUtils class for handling password operations including
hashing, verification, and validation.

Dependencies:
- passlib
- fastapi

Author: Minh An
Last Modified: 21 Jan 2024
Version: 1.0.0
"""

import random
import string

from fastapi import status
from passlib.hash import bcrypt

from app.exceptions.exception import CustomHTTPException
from app.middleware.translation_manager import _


class PasswordUtils:
	"""
	Utility class for password hashing, verification, and validation.

	This class provides static methods to securely hash passwords,
	verify passwords against hashed values, and validate password strength.
	"""

	@staticmethod
	def hash_password(password: str) -> str:
		"""
		Hashes a given password using bcrypt.

		Args:
		    password (str): The plaintext password to be hashed.

		Returns:
		    str: The hashed password.

		Raises:
		    CustomHTTPException: If the password is empty.
		"""
		if not password:
			raise CustomHTTPException(message=_('password_empty'))
		return bcrypt.hash(password)

	@staticmethod
	def verify_password(password: str, hashed_password: str) -> bool:
		"""
		Verifies a password against a given hashed password.

		Args:
		    password (str): The plaintext password to verify.
		    hashed_password (str): The stored hashed password.

		Returns:
		    bool: True if the password matches the hash, otherwise False.
		"""
		if not password or not hashed_password:
			return False
		return bcrypt.verify(password, hashed_password)

	@staticmethod
	def validate_password(password: str) -> str | None:
		"""
		Validates a password against predefined security criteria.

		The password must meet the following criteria:
		- At least 8 characters long
		- Contains at least one numeral
		- Contains at least one uppercase letter
		- Contains at least one lowercase letter
		- Contains at least one special character (!@#$%^&*()-_+=[]{}|;:,.<>?/)

		Args:
		    password (str): The password to validate.

		Returns:
		    str: The password if it passes validation.

		Raises:
		    CustomHTTPException: If the password does not meet the security requirements.
		"""
		if not password:
			raise CustomHTTPException(message=_('password_empty'))

		def response(erst: str):
			return CustomHTTPException(
				message=erst,
			)

		try:
			if len(password) < 8:
				raise response(_('password_too_short').format(min_length=8))
			if not any(char.isdigit() for char in password):
				raise response(_('password_too_short'))
			if not any(char.isupper() for char in password):
				raise response(_('password_require_uppercase'))
			if not any(char.islower() for char in password):
				raise response(_('password_require_lowercase'))
			if not any(char in '!@#$%^&*()-_+=[]{}|;:,.<>?/' for char in password):
				raise response(_('password_require_special'))
			return password
		except Exception:
			raise response(_('password_invalid'))

	def generate_strong_password(self, length: int = 12) -> str:
		"""
		Generates a strong random password.

		Args:
		    length (int): The length of the password to generate.

		Returns:
		    str: A randomly generated strong password.
		"""

		characters = string.ascii_letters + string.digits + '!@#$%^&*()-_+=[]{}|;:,.<>?/'
		return ''.join(random.choice(characters) for _ in range(length))
