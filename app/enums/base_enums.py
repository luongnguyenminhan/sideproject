"""Base enums and constants"""

from enum import Enum, EnumMeta


class BaseMetadataEnum(EnumMeta):
	"""Base metadata enum class that allows for checking if a value is in the enum"""

	def __contains__(self, other):
		try:
			self(other)
		except ValueError:
			return False
		else:
			return True


class BaseEnum(str, Enum, metaclass=BaseMetadataEnum):
	"""Base enum class."""


class BaseErrorCode:
	"""BaseErrorCode"""

	ERROR_CODE_SUCCESS = 0
	ERROR_CODE_FAIL = 1


class Constants(BaseEnum):
	"""Constants"""

	PAGE_SIZE = 10
