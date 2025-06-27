"""
Simple calculation tools for basic workflow
"""

import logging
from typing import List, Dict, Any
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# List of available tools - keeping it empty to focus on enhanced tools
tools = []


def get_tools(config: Dict[str, Any] = None) -> List:
	"""Get tools for the workflow - include enhanced tools if db_session available"""
	basic_tools = tools.copy()
	print(f'📋 [BasicTools] Basic tools count: {len(basic_tools)}')

	# Add enhanced tools if db_session is available in config
	if config and hasattr(config, 'db_session') and config.db_session:
		print(f'💾 [BasicTools] Database session found, adding enhanced tools')
		try:
			# TODO: CV tools have external dependencies - consider if needed
			# from .cv_context_tool import CVContextTool
			# from .cv_rag_enhancement_tool import CVRAGEnhancementTool
			from .rag_tool import RAGTool
			from .question_composer_tool import get_question_composer_tool

			# cv_context_tool = CVContextTool(db_session=config.db_session)
			# cv_rag_tool = CVRAGEnhancementTool(db_session=config.db_session)
			print(f'🔍 [BasicTools] Creating RAG tool')
			rag_tool = RAGTool(db_session=config.db_session)
			print(f'✅ [BasicTools] RAG tool created')

			print(f'❓ [BasicTools] Creating QuestionComposer tool')
			question_composer_tool = get_question_composer_tool(db_session=config.db_session)

			# Set authorization token from config if available
			if hasattr(config, 'authorization_token') and config.authorization_token:
				question_composer_tool.set_authorization_token(config.authorization_token)
				print(f'🔑 [BasicTools] Authorization token set for QuestionComposer tool')

			print(f'✅ [BasicTools] QuestionComposer tool created')

			basic_tools.extend([rag_tool, question_composer_tool])
			print(f'🎉 [BasicTools] Enhanced tools added: RAG Tool, Question Composer Tool')
			logger.info('Enhanced tools added: RAG Tool, Question Composer Tool')
			# logger.info('Enhanced tools added: CV Context, CV RAG Enhancement, and RAG Tool')
		except ImportError as e:
			print(f'⚠️ [BasicTools] Could not import enhanced tools: {e}')
			logger.warning(f'Could not import enhanced tools: {e}')

	print(f'📊 [BasicTools] Total tools count: {len(basic_tools)}')
	return basic_tools


def get_tool_definitions(config: Dict[str, Any] = None) -> List[Dict]:
	"""Get tool definitions for model binding"""
	# Get actual tools instead of empty list
	actual_tools = get_tools(config)
	print(f'🔧 [BasicTools] Tool definitions count: {len(actual_tools)}')
	return actual_tools
