"""Meeting enums"""

from enum import Enum


class MeetingStatusEnum(str, Enum):
	"""Meeting status enumeration"""

	SCHEDULED = 'scheduled'
	IN_PROGRESS = 'in_progress'
	COMPLETED = 'completed'
	CANCELLED = 'cancelled'


class MeetingTypeEnum(str, Enum):
	"""Meeting type enumeration"""

	ONE_ON_ONE = 'one_on_one'
	TEAM = 'team'
	CLIENT = 'client'
	INTERVIEW = 'interview'
	CONFERENCE = 'conference'
	OTHER = 'other'
	ANONYMOUS = 'anonymous'
	EXTENSION = 'extension'


class FileTypeEnum(str, Enum):
	"""File type enumeration"""

	AUDIO = 'audio'
	TRANSCRIPT = 'transcript'
	NOTE = 'note'
	PDF = 'pdf'
	OTHER = 'other'


class ProcessingStatusEnum(str, Enum):
	"""Processing status enumeration"""

	PENDING = 'pending'
	PROCESSING = 'processing'
	COMPLETED = 'completed'
	FAILED = 'failed'


class MeetingItemTypeEnum(str, Enum):
	"""Meeting item type enumeration"""

	DECISION = 'decision'
	ACTION_ITEM = 'action_item'
	QUESTION = 'question'
	OTHER = 'other'


class NotificationTypeEnum(str, Enum):
	"""Notification type enumeration"""

	PROCESSING_COMPLETE = 'processing_complete'
	TRANSCRIPT_READY = 'transcript_ready'
	NOTE_GENERATED = 'note_generated'
	ERROR = 'error'
	REMINDER = 'reminder'


class TokenOperationTypeEnum(str, Enum):
	"""Token operation type enumeration"""

	TRANSCRIPTION = 'transcription'
	SUMMARIZATION = 'summarization'
	ANALYSIS = 'analysis'
	TRANSLATION = 'translation'
	EXTRACTION = 'extraction'
	OTHER = 'other'


class VectorIndexTypeEnum(str, Enum):
	"""Vector index type enumeration"""

	TRANSCRIPT = 'transcript'
	MEETING_NOTE = 'meeting_note'
	CHUNK = 'chunk'
	OTHER = 'other'
