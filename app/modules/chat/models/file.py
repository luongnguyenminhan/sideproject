from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.base_model import BaseEntity


class File(BaseEntity):
	"""File model for chat file attachments"""

	__tablename__ = 'files'

	name = Column(String(255), nullable=False)
	original_name = Column(String(255), nullable=False)
	file_path = Column(String(1000), nullable=False)  # MinIO object path
	file_url = Column(String(1000), nullable=True)
	size = Column(Integer, nullable=False)
	type = Column(String(100), nullable=False)  # MIME type
	user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
	conversation_id = Column(String(36), ForeignKey('conversations.id'), nullable=True)
	upload_date = Column(DateTime, nullable=False)
	checksum = Column(String(64), nullable=True)
	download_count = Column(Integer, default=0)
	minio_bucket = Column(String(255), nullable=True)

	# Relationships
	user = relationship('User', back_populates='files')
	conversation = relationship('Conversation', back_populates='files')
	message_files = relationship('MessageFile', back_populates='file', cascade='all, delete-orphan')

	@property
	def formatted_size(self) -> str:
		"""Format file size for display"""
		if self.size == 0:
			return '0 Bytes'
		k = 1024
		sizes = ['Bytes', 'KB', 'MB', 'GB']
		i = int(self.size.bit_length() / 10) if self.size > 0 else 0
		if i >= len(sizes):
			i = len(sizes) - 1
		return f'{self.size / (k**i):.2f} {sizes[i]}'

	@property
	def file_extension(self) -> str:
		"""Get file extension"""
		return self.original_name.split('.')[-1].lower() if '.' in self.original_name else ''

	@property
	def is_image(self) -> bool:
		"""Check if file is an image"""
		return self.type.startswith('image/')

	@property
	def is_video(self) -> bool:
		"""Check if file is a video"""
		return self.type.startswith('video/')

	@property
	def is_audio(self) -> bool:
		"""Check if file is audio"""
		return self.type.startswith('audio/')

	@property
	def is_document(self) -> bool:
		"""Check if file is a document"""
		doc_types = [
			'application/pdf',
			'application/msword',
			'application/vnd.openxmlformats-officedocument',
		]
		return any(self.type.startswith(doc_type) for doc_type in doc_types)
