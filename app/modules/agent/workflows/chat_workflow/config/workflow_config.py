"""
Centralized configuration cho Chat Workflow
Production-ready settings với Vietnamese financial context
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import os

# Import persona types
from .persona_prompts import PersonaType, PersonaPrompts


@dataclass
class WorkflowConfig:
	"""Centralized workflow configuration"""

	# Model settings
	model_name: str = 'gemini-2.0-flash-lite'
	temperature: float = 1.0
	max_tokens: int = 10000
	api_key: Optional[str] = None

	# RAG settings
	rag_enabled: bool = True
	similarity_threshold: float = 0.7
	max_retrieved_docs: int = 5
	collection_name: str = 'moneyez_knowledge'

	# Query processing
	enable_query_optimization: bool = True
	max_queries_per_request: int = 3

	# Error handling
	enable_graceful_degradation: bool = True
	max_retry_attempts: int = 3
	fallback_response_enabled: bool = True

	# Performance settings
	enable_caching: bool = True
	cache_ttl_seconds: int = 3600  # 1 hour
	enable_batch_processing: bool = True

	# Persona settings
	persona_enabled: bool = True
	persona_type: PersonaType = PersonaType.MARXIS_LENISMS_ASSISTANT

	def get_persona_prompt(self) -> Optional[str]:
		"""Get persona-based system prompt"""
		if not self.persona_enabled:
			return None
		return PersonaPrompts.get_persona_prompt(self.persona_type)

	def get_persona_name(self) -> str:
		"""Get persona name"""
		return PersonaPrompts.get_persona_name(self.persona_type)

	def __post_init__(self):
		"""Initialize từ environment variables nếu không được set"""
		if not self.api_key:
			self.api_key = os.getenv('GOOGLE_API_KEY')

	@classmethod
	def from_env(cls) -> 'WorkflowConfig':
		"""Create config từ environment variables"""
		return cls(
			model_name=os.getenv('MODEL_NAME', 'gemini-2.0-flash'),
			temperature=float(os.getenv('MODEL_TEMPERATURE', '0')),
			max_tokens=int(os.getenv('MAX_TOKENS', '2048')),
			api_key=os.getenv('GOOGLE_API_KEY'),
			rag_enabled=os.getenv('RAG_ENABLED', 'true').lower() == 'true',
			similarity_threshold=float(os.getenv('SIMILARITY_THRESHOLD', '0.7')),
			max_retrieved_docs=int(os.getenv('MAX_RETRIEVED_DOCS', '5')),
			collection_name=os.getenv('COLLECTION_NAME', 'moneyez_knowledge'),
		)

	def to_dict(self) -> Dict[str, Any]:
		"""Convert to dictionary cho serialization"""
		return {
			'model_name': self.model_name,
			'temperature': self.temperature,
			'max_tokens': self.max_tokens,
			'rag_enabled': self.rag_enabled,
			'similarity_threshold': self.similarity_threshold,
			'max_retrieved_docs': self.max_retrieved_docs,
			'collection_name': self.collection_name,
			'enable_query_optimization': self.enable_query_optimization,
			'max_queries_per_request': self.max_queries_per_request,
			'enable_graceful_degradation': self.enable_graceful_degradation,
			'max_retry_attempts': self.max_retry_attempts,
			'fallback_response_enabled': self.fallback_response_enabled,
			'enable_caching': self.enable_caching,
			'cache_ttl_seconds': self.cache_ttl_seconds,
			'enable_batch_processing': self.enable_batch_processing,
			'persona_enabled': self.persona_enabled,
			'persona_type': self.persona_type.value,
		}

	def validate(self) -> bool:
		"""Validate configuration parameters"""
		if not self.api_key:
			raise ValueError('Google API key is required')

		if self.temperature < 0 or self.temperature > 1:
			raise ValueError('Temperature must be between 0 and 1')

		if self.max_tokens <= 0:
			raise ValueError('Max tokens must be positive')

		if self.similarity_threshold < 0 or self.similarity_threshold > 1:
			raise ValueError('Similarity threshold must be between 0 and 1')

		if self.max_retrieved_docs <= 0:
			raise ValueError('Max retrieved docs must be positive')

		return True
