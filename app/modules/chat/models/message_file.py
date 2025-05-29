from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.base_model import BaseEntity


class MessageFile(BaseEntity):
    """Association table between messages and files"""

    __tablename__ = "message_files"

    message_id = Column(String(36), ForeignKey("messages.id"), nullable=False)
    file_id = Column(String(36), ForeignKey("files.id"), nullable=False)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)

    # Relationships
    message = relationship("Message", back_populates="message_files")
    file = relationship("File", back_populates="message_files")
    conversation = relationship("Conversation", back_populates="message_files")
