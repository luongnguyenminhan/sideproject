"""
Tools for the chat workflow
"""

import logging
from typing import List, Dict, Any
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Import the main tools
from .question_composer_tool import generate_survey_questions
from .rag_tool import rag_search
from .jd_matching_tool import trigger_jd_matching_tool

# List of available tools
tools = [generate_survey_questions, rag_search, trigger_jd_matching_tool]


def get_tools(config: Dict[str, Any] = None) -> List:
	"""Get all tools for the workflow"""
	all_tools = tools.copy()
	pass

	# Add CV profile tool if db_session is available in config
	if config and hasattr(config, 'db_session') and config.db_session:
		pass
		try:
			from .cv_profile_tool import get_cv_profile_tool

			cv_tool = get_cv_profile_tool(config.db_session)
			all_tools.append(cv_tool)
			pass
		except ImportError:
			pass

	pass
	return all_tools


def get_tool_definitions(config: Dict[str, Any] = None) -> List:
	"""Get tool definitions for model binding (backward compatibility)"""
	return get_tools(config)
