"""Meeting file model"""

from sqlalchemy import (
	BigInteger,
	Boolean,
	Column,
	DateTime,
	ForeignKey,
	Integer,
	String,
	Text,
)
from sqlalchemy.orm import relationship

from app.core.base_model import BaseEntity
from app.enums.meeting_enums import FileTypeEnum, ProcessingStatusEnum


class MeetingFile(BaseEntity):
	"""MeetingFile model for storing files related to meetings"""

	__tablename__ = 'meeting_files'

	meeting_id = Column(String(36), ForeignKey('meetings.id'), nullable=False)
	file_type = Column(String(50), nullable=False, default=FileTypeEnum.AUDIO.value)
	file_path = Column(String(512), nullable=True)
	object_name = Column(String(512), nullable=True)
	file_url = Column(String(1024), nullable=True)
	file_size_bytes = Column(BigInteger, nullable=True)
	duration_seconds = Column(Integer, nullable=True)
	mime_type = Column(String(255), nullable=True)
	uploaded_at = Column(DateTime(timezone=True), nullable=False)
	processed = Column(Boolean, default=False)
	processing_status = Column(String(50), default=ProcessingStatusEnum.PENDING.value)
	processing_error = Column(Text, nullable=True)

	# Relationships
	meeting = relationship('Meeting', back_populates='files')
