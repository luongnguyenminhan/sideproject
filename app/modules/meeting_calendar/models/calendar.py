"""Calendar integration models"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.base_model import BaseEntity
from app.enums.calendar_enums import CalendarProviderEnum, EventStatusEnum

# Remove direct import of Meeting class to avoid circular dependency
# from app.modules.meetings.models.meeting import Meeting


class CalendarIntegration(BaseEntity):
	"""CalendarIntegration model for connecting to external calendar services"""

	__tablename__ = 'calendar_integrations'

	user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
	provider = Column(String(50), nullable=False, default=CalendarProviderEnum.GOOGLE.value)
	access_token = Column(Text, nullable=False)
	refresh_token = Column(Text, nullable=True)
	token_expiry = Column(DateTime(timezone=True), nullable=True)
	calendar_id = Column(String(255), nullable=True)  # External calendar ID
	scope = Column(Text, nullable=True)  # API access scope

	# Relationships
	calendar_events = relationship(
		'CalendarEvent',
		back_populates='calendar_integration',
		cascade='all, delete-orphan',
	)


class CalendarEvent(BaseEntity):
	"""CalendarEvent model for tracking calendar events"""

	__tablename__ = 'calendar_events'

	user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
	calendar_integration_id = Column(String(36), ForeignKey('calendar_integrations.id'), nullable=False)
	external_event_id = Column(String(255), nullable=False)
	title = Column(String(255), nullable=False)
	description = Column(Text, nullable=True)
	location = Column(String(255), nullable=True)
	start_time = Column(DateTime(timezone=True), nullable=False)
	end_time = Column(DateTime(timezone=True), nullable=False)
	meeting_id = Column(String(36), ForeignKey('meetings.id'), nullable=True)
	is_recurring = Column(Boolean, default=False)
	status = Column(String(50), default=EventStatusEnum.SCHEDULED.value)

	# Relationships
	calendar_integration = relationship('CalendarIntegration', back_populates='calendar_events', lazy='joined')
	meeting = relationship('Meeting', back_populates='calendar_events', lazy='joined')
