from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.core.base_model import BaseEntity
import enum


class MessageRole(str, enum.Enum):
	USER = 'user'
	ASSISTANT = 'assistant'


class Message(BaseEntity):
	"""Message model - stored entirely in MySQL"""

	__tablename__ = 'messages'

	conversation_id = Column(String(36), ForeignKey('conversations.id'), nullable=False)
	user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
	role = Column(Enum(MessageRole), nullable=False, default=MessageRole.USER)
	content = Column(Text, nullable=False)
	timestamp = Column(DateTime, nullable=False)
	model_used = Column(String(100), nullable=True)
	tokens_used = Column(Text, nullable=True)  # JSON string
	response_time_ms = Column(String(10), nullable=True)

	# Relationships
	user = relationship('User', back_populates='messages')
	message_files = relationship('MessageFile', back_populates='message', cascade='all, delete-orphan')
