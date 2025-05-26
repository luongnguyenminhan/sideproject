"""Meeting note models"""

from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.base_model import BaseEntity
from app.enums.meeting_enums import MeetingItemTypeEnum


class MeetingNote(BaseEntity):
	"""MeetingNote model for storing generated meeting notes"""

	__tablename__ = 'meeting_notes'

	meeting_id = Column(String(36), ForeignKey('meetings.id'), nullable=False)
	transcript_id = Column(String(36), ForeignKey('transcripts.id'), nullable=False)
	content = Column(JSON, nullable=False)
	version = Column(Integer, nullable=False, default=1)
	is_latest = Column(Boolean, default=True)
	is_encrypted = Column(Boolean, default=False)
	encryption_key = Column(Text, nullable=True)

	# Relationships
	meeting = relationship('Meeting', back_populates='meeting_notes')
	transcript = relationship('Transcript', back_populates='meeting_notes')
	meeting_items = relationship('MeetingItem', back_populates='meeting_note', cascade='all, delete-orphan')
	vector_indices = relationship('VectorIndex', back_populates='meeting_note', cascade='all, delete-orphan')


class MeetingItem(BaseEntity):
	"""MeetingItem model for storing structured items from meeting notes (decisions, action items, questions)"""

	__tablename__ = 'meeting_items'

	meeting_note_id = Column(String(36), ForeignKey('meeting_notes.id'), nullable=False)
	type = Column(String(50), nullable=False, default=MeetingItemTypeEnum.DECISION.value)
	content = Column(JSON, nullable=False)

	# Relationships
	meeting_note = relationship('MeetingNote', back_populates='meeting_items')
