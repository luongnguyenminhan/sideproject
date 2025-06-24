"""
Tools manager for chat workflow - Focus on enhanced tools only
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# List of basic tools - empty as requested, focus on enhanced tools only
tools = []


def get_tools(config: Dict[str, Any] = None) -> List:
	"""Get tools for the workflow - include enhanced tools if db_session available"""
	basic_tools = tools.copy()
	print(f'📋 [BasicTools] Basic tools count: {len(basic_tools)}')

	# Add enhanced tools if db_session is available in config
	if config and hasattr(config, 'db_session') and config.db_session:
		print(f'💾 [BasicTools] Database session found, adding enhanced tools')
		try:
			# Import function-based tools
			from .rag_tool import get_rag_tool
			from .question_composer_tool import get_question_composer_tool

			print(f'🔍 [BasicTools] Creating function-based RAG tool')
			rag_tool = get_rag_tool(db_session=config.db_session)
			print(f'✅ [BasicTools] Function-based RAG tool created')

			print(f'❓ [BasicTools] Creating function-based QuestionComposer tool')
			question_composer_tool = get_question_composer_tool(db_session=config.db_session)
			print(f'✅ [BasicTools] Function-based QuestionComposer tool created')

			basic_tools.extend([rag_tool, question_composer_tool])
			print(f'🎉 [BasicTools] Function-based tools added: RAG Tool, Question Composer Tool')
			logger.info('Function-based tools added: RAG Tool, Question Composer Tool')
			# logger.info('Enhanced tools added: CV Context, CV RAG Enhancement, and RAG Tool')
		except ImportError as e:
			print(f'⚠️ [BasicTools] Could not import enhanced tools: {e}')
			logger.warning(f'Could not import enhanced tools: {e}')

	print(f'📊 [BasicTools] Total tools count: {len(basic_tools)}')
	return basic_tools


def get_tool_definitions(config: Dict[str, Any] = None) -> List[Dict[str, Any]]:
	"""Get tool definitions with prioritization logging"""
	print(f'📋 [Tools] Getting tool definitions with prioritization guidance')

	tools_list = get_tools(config)
	tool_definitions = []

	for tool in tools_list:
		if hasattr(tool, 'name') and hasattr(tool, 'description'):
			tool_definitions.append({
				'name': tool.name,
				'description': tool.description,
				'priority': ('HIGH' if tool.name in ['rag_retrieval', 'question_composer'] else 'MEDIUM'),
			})

	# Log tool prioritization
	high_priority_tools = [t for t in tool_definitions if t['priority'] == 'HIGH']
	print(f'🔥 [Tools] HIGH PRIORITY TOOLS ({len(high_priority_tools)}): {[t["name"] for t in high_priority_tools]}')
	print(f'💡 [Tools] Agent should ALWAYS consider these tools first!')
	print(f'🎯 [Tools] Tool usage guidance: Use RAG for any information queries, Question Composer for CV/profile topics')

	logger.info(f'Tool definitions provided: {len(tool_definitions)} tools available')
	return tool_definitions
