"""
Configuration for the Agentic RAG module.
"""

import os
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# Check if running in Docker environment
DOCKER_ENVIRONMENT = os.getenv('DOCKER_ENVIRONMENT', 'False').lower() == 'true'

# Qdrant configuration - sử dụng local Qdrant từ docker-compose.yml
# Sử dụng cùng cấu hình như main app
QDRANT_HOST = os.getenv('QDRANT_HOST', 'qdrant' if DOCKER_ENVIRONMENT else 'localhost')
QDRANT_PORT = os.getenv('QDRANT_PORT', '6333')
QDRANT_URL = os.getenv(
	'QDRANT_URL',
	f'http://{QDRANT_HOST}:{QDRANT_PORT}',  # Sử dụng local Qdrant từ docker-compose
)
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY', '')  # Không cần API key cho local Qdrant
QDRANT_COLLECTION = os.getenv('QDRANT_COLLECTION', 'agentic_rag_kb')


# Embedding configuration
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'models/embedding-001')

# File extraction configuration
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '10485760'))  # 10MB default
SUPPORTED_FILE_TYPES = {
	'application/pdf': '.pdf',
	'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
	'text/plain': '.txt',
	'text/markdown': '.md',
	'application/msword': '.doc',
}

# Collection management
DEFAULT_COLLECTION = 'global'
COLLECTION_PREFIX = 'rag_'


class QdrantConfig(BaseModel):
	"""Qdrant configuration."""

	QdrantUrl: str = QDRANT_URL
	QdrantApiKey: str = QDRANT_API_KEY
	QdrantCollection: str = QDRANT_COLLECTION

	class Config:
		env_prefix = 'QDRANT_'


settings = QdrantConfig()
