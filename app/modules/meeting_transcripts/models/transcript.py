"""Transcript model"""

from sqlalchemy import JSON, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.base_model import BaseEntity
from app.enums.transcript_enums import AudioSourceEnum


class Transcript(BaseEntity):
	"""Transcript model for storing meeting transcripts"""

	__tablename__ = 'transcripts'

	meeting_id = Column(String(36), ForeignKey('meetings.id'), nullable=False)
	content = Column(JSON, nullable=False)
	source = Column(String(50), default=AudioSourceEnum.UPLOAD.value)
	language = Column(String(50), default='vi')

	# Relationships
	meeting = relationship('Meeting', back_populates='transcripts')
	meeting_notes = relationship('MeetingNote', back_populates='transcript', cascade='all, delete-orphan')
	vector_indices = relationship('VectorIndex', back_populates='transcript', cascade='all, delete-orphan')
