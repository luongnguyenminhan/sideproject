"""Meeting model"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.base_model import BaseEntity
from app.enums.meeting_enums import MeetingStatusEnum


class Meeting(BaseEntity):
	"""Meeting model for storing meeting information"""

	__tablename__ = 'meetings'

	user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
	group_id = Column(String(36), ForeignKey('groups.id'), nullable=True)
	title = Column(String(255), nullable=False)
	description = Column(Text, nullable=True)
	meeting_date = Column(DateTime(timezone=True), nullable=False)
	duration_seconds = Column(Integer, nullable=True)
	meeting_type = Column(String(50), nullable=True)
	status = Column(String(50), default=MeetingStatusEnum.SCHEDULED.value)
	is_encrypted = Column(Boolean, default=False)
	encryption_key = Column(Text, nullable=True)
	is_recurring = Column(Boolean, default=False)
	language = Column(String(50), default='vi')
	platform = Column(String(100), nullable=True)
	meeting_link = Column(String(255), nullable=True)
	organizer_email = Column(String(255), nullable=True)
	organizer_name = Column(String(255), nullable=True)
	last_joined_at = Column(DateTime(timezone=True), nullable=True)

	# Relationships - References to other modules
	group = relationship('Group', back_populates='meetings')
	files = relationship('MeetingFile', back_populates='meeting', cascade='all, delete-orphan')
	transcripts = relationship('Transcript', back_populates='meeting', cascade='all, delete-orphan')
	meeting_notes = relationship('MeetingNote', back_populates='meeting', cascade='all, delete-orphan')
	tags = relationship('MeetingTag', back_populates='meeting', cascade='all, delete-orphan')
	notifications = relationship('Notification', back_populates='meeting', cascade='all, delete-orphan')
	token_usages = relationship('TokenUsage', back_populates='meeting', cascade='all, delete-orphan')
	# calendar_events relationship moved to the bottom of the file to avoid circular imports
	vector_indices = relationship('VectorIndex', back_populates='meeting', cascade='all, delete-orphan')


# Add the calendar_events relationship after both Meeting and CalendarEvent classes are defined
# Import must be at the bottom to avoid circular imports
from app.modules.meeting_calendar.models.calendar import CalendarEvent

Meeting.calendar_events = relationship('CalendarEvent', back_populates='meeting', cascade='all, delete-orphan')
