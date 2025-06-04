"""
Agentic RAG Module.
This module provides components for creating a knowledge base for RAG applications.
"""

import logging

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


logger.info(f'{LogColors.HEADER}[AgenticRAG-Module] Agentic RAG module initialized{LogColors.ENDC}')
