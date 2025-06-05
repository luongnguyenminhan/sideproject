"""
Configuration for the Agentic RAG module.
"""

import os
import logging
from pydantic import BaseModel

# Setup module logger
logger = logging.getLogger(__name__)

# Qdrant configuration
QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY', '')
QDRANT_COLLECTION = os.getenv('QDRANT_COLLECTION', 'agentic_rag_kb')

# Embedding configuration
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'models/embedding-001')

class QdrantConfig(BaseModel):
	"""Qdrant configuration."""

	url: str = QDRANT_URL
	api_key: str = QDRANT_API_KEY
	collection_name: str = QDRANT_COLLECTION

	class Config:
		env_prefix = 'QDRANT_'
