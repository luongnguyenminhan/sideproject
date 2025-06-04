"""
Configuration for the Agentic RAG module.
"""

import os
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# Color codes for logging
class LogColors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKCYAN = '\033[96m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'


logger.info(f'{LogColors.HEADER}[AgenticRAG-CoreConfig] Loading core configuration{LogColors.ENDC}')

# Check if running in Docker environment
DOCKER_ENVIRONMENT = os.getenv('DOCKER_ENVIRONMENT', 'False').lower() == 'true'
logger.info(f'{LogColors.OKBLUE}[AgenticRAG-CoreConfig] Docker environment detected: {DOCKER_ENVIRONMENT}{LogColors.ENDC}')

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

logger.info(f'{LogColors.OKCYAN}[AgenticRAG-CoreConfig] Qdrant configuration - Host: {QDRANT_HOST}, Port: {QDRANT_PORT}, URL: {QDRANT_URL}{LogColors.ENDC}')
logger.info(f'{LogColors.OKBLUE}[AgenticRAG-CoreConfig] Default collection: {QDRANT_COLLECTION}{LogColors.ENDC}')

# Embedding configuration
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'models/embedding-001')
logger.info(f'{LogColors.OKCYAN}[AgenticRAG-CoreConfig] Embedding model: {EMBEDDING_MODEL}{LogColors.ENDC}')


class QdrantConfig(BaseModel):
	"""Qdrant configuration."""

	QdrantUrl: str = QDRANT_URL
	QdrantApiKey: str = QDRANT_API_KEY
	QdrantCollection: str = QDRANT_COLLECTION

	class Config:
		env_prefix = 'QDRANT_'


settings = QdrantConfig()
logger.info(f'{LogColors.OKGREEN}[AgenticRAG-CoreConfig] Configuration settings initialized successfully{LogColors.ENDC}')
