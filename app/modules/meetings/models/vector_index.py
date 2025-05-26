"""Vector index model"""

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.base_model import BaseEntity
from app.enums.meeting_enums import VectorIndexTypeEnum


class VectorIndex(BaseEntity):
	"""VectorIndex model for storing vector embeddings for search"""

	__tablename__ = 'vector_indices'

	meeting_id = Column(String(36), ForeignKey('meetings.id'), nullable=False)
	transcript_id = Column(String(36), ForeignKey('transcripts.id'), nullable=True)
	meeting_note_id = Column(String(36), ForeignKey('meeting_notes.id'), nullable=True)
	vector_db_id = Column(String(255), nullable=False)
	index_type = Column(String(50), nullable=False, default=VectorIndexTypeEnum.TRANSCRIPT.value)
	collection_name = Column(String(255), nullable=False)
	indexed_at = Column(DateTime(timezone=True), nullable=False)

	# Relationships
	meeting = relationship('Meeting', back_populates='vector_indices')
	transcript = relationship('Transcript', back_populates='vector_indices')
	meeting_note = relationship('MeetingNote', back_populates='vector_indices')
