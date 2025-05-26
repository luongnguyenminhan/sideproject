"""Transcript enums"""

from enum import Enum


class AudioSourceEnum(str, Enum):
	"""Audio source enumeration"""

	UPLOAD = 'upload'
	RECORDING = 'recording'
	ZOOM = 'zoom'
	TEAMS = 'teams'
	GOOGLE_MEET = 'google_meet'
	OTHER = 'other'
