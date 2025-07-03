from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.core.base_model import BaseEntity


class CVGeneration(BaseEntity):
	"""Model cho CV Generation jobs"""

	__tablename__ = 'cv_generation'

	# Basic info
	user_id = Column(String(255), nullable=True, index=True)
	job_id = Column(String(255), unique=True, nullable=False, index=True)

	# Input data
	cv_extraction_id = Column(String(255), nullable=True)  # ID từ cv_extraction
	template_type = Column(String(50), nullable=False, default='modern')  # modern, classic, creative
	color_theme = Column(String(50), nullable=False, default='blue')
	custom_prompt = Column(Text, nullable=True)

	# Generation status
	status = Column(String(50), nullable=False, default='pending')  # pending, processing, completed, failed
	progress = Column(Float, nullable=True, default=0.0)  # 0-100

	# Output data
	latex_source = Column(Text, nullable=True)
	pdf_file_path = Column(String(500), nullable=True)
	pdf_file_url = Column(String(500), nullable=True)
	file_size = Column(Integer, nullable=True)

	# Processing info
	generation_time = Column(Float, nullable=True)  # seconds
	error_message = Column(Text, nullable=True)

	# AI/LLM info
	llm_model_used = Column(String(100), nullable=True)
	llm_input_tokens = Column(Integer, nullable=True)
	llm_output_tokens = Column(Integer, nullable=True)
	llm_total_tokens = Column(Integer, nullable=True)
	llm_cost_usd = Column(Float, nullable=True)

	# Metadata
	generation_config = Column(JSON, nullable=True)  # Store full config
	cv_data_snapshot = Column(JSON, nullable=True)  # Store input CV data

	# Timestamps
	started_at = Column(DateTime(timezone=True), nullable=True)
	completed_at = Column(DateTime(timezone=True), nullable=True)

	def __repr__(self):
		return f'<CVGeneration(id={self.id}, job_id={self.job_id}, status={self.status})>'
