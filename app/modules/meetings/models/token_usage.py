"""Token usage model"""

from sqlalchemy import DECIMAL, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.base_model import BaseEntity
from app.enums.meeting_enums import TokenOperationTypeEnum


class TokenUsage(BaseEntity):
	"""TokenUsage model for tracking AI API token usage"""

	__tablename__ = 'token_usage'

	user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
	meeting_id = Column(String(36), ForeignKey('meetings.id'), nullable=False)
	operation_type = Column(String(50), nullable=False, default=TokenOperationTypeEnum.SUMMARIZATION.value)
	input_tokens = Column(Integer, nullable=False, default=0)
	output_tokens = Column(Integer, nullable=False, default=0)
	context_tokens = Column(Integer, nullable=False, default=0)
	price_vnd = Column(DECIMAL(10, 2), nullable=False, default=0)

	# Relationships
	meeting = relationship('Meeting', back_populates='token_usages')

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.calculate_price_vnd()

	def calculate_price_vnd(self):
		"""Auto calculate price_vnd based on token usage"""
		# Define rates for different token types (in USD per token)
		if self.operation_type == TokenOperationTypeEnum.TRANSCRIPTION.value:
			input_rate = 0.0000007
		else:
			input_rate = 0.0000001

		output_rate = 0.0000004
		context_rate = 0.000000025

		# Calculate price in USD
		price = (self.input_tokens * input_rate) + (self.output_tokens * output_rate) + (self.context_tokens * context_rate)

		# Convert to VND (1 USD = 24000 VND)
		self.price_vnd = price * 24000
