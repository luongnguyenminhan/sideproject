"""
Workflow configuration for question generation.
"""

from typing import Dict, Any
from pydantic import BaseModel


class QuestionGenerationWorkflowConfig(BaseModel):
	"""Configuration for question generation workflow"""

	# Model settings
	model_name: str = 'gemini-2.0-flash-lite'
	temperature: float = 0.7
	max_tokens: int = 10000

	# Workflow settings
	max_questions_per_round: int = 4
	max_iterations: int = 5
	min_completeness_threshold: float = 0.8

	# Node settings
	generation_retries: int = 3
	analysis_retries: int = 2

	class Config:
		env_prefix = 'QUESTION_WORKFLOW_'

	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary"""
		return {'model_name': self.model_name, 'temperature': self.temperature, 'max_tokens': self.max_tokens, 'max_questions_per_round': self.max_questions_per_round, 'max_iterations': self.max_iterations, 'min_completeness_threshold': self.min_completeness_threshold, 'generation_retries': self.generation_retries, 'analysis_retries': self.analysis_retries}

	@classmethod
	def from_env(cls) -> 'QuestionGenerationWorkflowConfig':
		"""Create from environment variables"""
		return cls()
