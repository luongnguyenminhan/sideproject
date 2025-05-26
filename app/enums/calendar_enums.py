"""Calendar enums"""

from enum import Enum


class CalendarProviderEnum(str, Enum):
	"""Calendar provider enumeration"""

	GOOGLE = 'google'
	OTHER = 'other'


class EventStatusEnum(str, Enum):
	"""Event status enumeration"""

	SCHEDULED = 'scheduled'
	CONFIRMED = 'confirmed'
	CANCELLED = 'cancelled'
	TENTATIVE = 'tentative'
