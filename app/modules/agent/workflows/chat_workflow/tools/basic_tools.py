"""
Simple calculation tools for basic workflow
"""

import logging
from typing import List, Dict, Any
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Import the question composer tool function
from .question_composer_tool import generate_survey_questions

# List of available tools - including question composer tool
tools = [generate_survey_questions]


def get_tools(config: Dict[str, Any] = None) -> List:
	"""Get all tools for the workflow"""
	all_tools = tools.copy()
	print(f'📋 [BasicTools] Tools count: {len(all_tools)}')

	# Add CV profile tool if db_session is available in config
	if config and hasattr(config, 'db_session') and config.db_session:
		print(f'💾 [BasicTools] Database session found, adding CV profile tool')
		try:
			from .cv_profile_tool import get_cv_profile_tool
			
			print(f'👤 [BasicTools] Creating CV profile tool')
			cv_tool = get_cv_profile_tool(config.db_session)
			print(f'✅ [BasicTools] CV profile tool created')
			
			all_tools.append(cv_tool)
			print(f'🎉 [BasicTools] CV profile tool added')
			logger.info('CV profile tool added')
		except ImportError as e:
			print(f'⚠️ [BasicTools] Could not import CV profile tool: {e}')
			logger.warning(f'Could not import CV profile tool: {e}')

	# Add RAG tool if db_session is available in config
	if config and hasattr(config, 'db_session') and config.db_session:
		print(f'💾 [BasicTools] Database session found, adding RAG tool')
		try:
			from .rag_tool import RAGTool

			print(f'🔍 [BasicTools] Creating RAG tool')
			rag_tool = RAGTool(db_session=config.db_session)
			print(f'✅ [BasicTools] RAG tool created')

			all_tools.append(rag_tool)
			print(f'🎉 [BasicTools] RAG tool added')
			logger.info('RAG tool added')
		except ImportError as e:
			print(f'⚠️ [BasicTools] Could not import RAG tool: {e}')
			logger.warning(f'Could not import RAG tool: {e}')

	print(f'📊 [BasicTools] Total tools count: {len(all_tools)}')
	return all_tools


def get_tool_definitions(config: Dict[str, Any] = None) -> List[Dict]:
	"""Get tool definitions for model binding"""
	# Get all tools
	actual_tools = get_tools(config)
	print(f'🔧 [BasicTools] Tool definitions count: {len(actual_tools)}')
	return actual_tools
