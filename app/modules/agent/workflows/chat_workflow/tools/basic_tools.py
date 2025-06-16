"""
Simple calculation tools for basic workflow
"""

import logging
from typing import List, Dict, Any
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool(return_direct=False)
def add(a: float, b: float) -> float:
	"""Add two numbers together."""
	return a + b


@tool(return_direct=False)
def subtract(a: float, b: float) -> float:
	"""Subtract second number from first number."""
	return a - b


@tool(return_direct=False)
def multiply(a: float, b: float) -> float:
	"""Multiply two numbers together."""
	return a * b


@tool(return_direct=False)
def divide(a: float, b: float) -> float:
	"""Divide first number by second number."""
	if b == 0:
		return float('inf')
	return a / b


# List of available tools
tools = [
	add,
	subtract,
	multiply,
	divide,
]


def get_tools(config: Dict[str, Any] = None) -> List:
	"""Get tools for the workflow - include CV Context Tool if db_session available"""
	basic_tools = tools.copy()

	# Add CV Tools if db_session is available in config
	if config and hasattr(config, 'db_session') and config.db_session:
		try:
			from .cv_context_tool import CVContextTool
			from .cv_rag_enhancement_tool import CVRAGEnhancementTool

			cv_context_tool = CVContextTool(db_session=config.db_session)
			cv_rag_tool = CVRAGEnhancementTool(db_session=config.db_session)

			basic_tools.extend([cv_context_tool, cv_rag_tool])
			logger.info('CV Context Tool and CV RAG Enhancement Tool added to workflow tools')
		except ImportError as e:
			logger.warning(f'Could not import CV Tools: {e}')

	return basic_tools


def get_tool_definitions(config: Dict[str, Any] = None) -> List[Dict]:
	"""Get tool definitions for model binding"""
	# Return tool schema for model binding
	return [tool for tool in tools]
