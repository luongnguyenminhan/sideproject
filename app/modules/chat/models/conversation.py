from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.base_model import BaseEntity


class Conversation(BaseEntity):
	"""Conversation model representing user chat conversations"""

	__tablename__ = 'conversations'

	name = Column(String(255), nullable=False, default='New Conversation')
	user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
	message_count = Column(Integer, nullable=False, default=0)
	last_activity = Column(DateTime, nullable=True)
	system_prompt = Column(Text, nullable=True, default=None)  # Per-conversation agent customization
	extra_metadata = Column(Text, nullable=True, default=None)  # Store additional metadata like CV context as JSON
	# Relationships
	user = relationship('User', back_populates='conversations')
	messages = relationship('Message', back_populates='conversation', cascade='all, delete-orphan')
	files = relationship('File', back_populates='conversation', cascade='all, delete-orphan')
	message_files = relationship('MessageFile', back_populates='conversation', cascade='all, delete-orphan')
