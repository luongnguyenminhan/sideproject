"""
Enhanced Chat Workflow Module with Agentic RAG via KBRepository
Production-ready LangGraph workflow with file indexing and conversation memory
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.errors import NodeInterrupt
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver

from .tools.basic_tools import tools
from .state.workflow_state import AgentState
from .config.workflow_config import WorkflowConfig

# Note: LangChainQdrantService removed - now using Agentic RAG KBRepository
from .utils.color_logger import get_color_logger, Colors
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

load_dotenv()

# Initialize colorful logger
color_logger = get_color_logger(__name__)


class ChatWorkflow:
	"""
	Enhanced Chat Workflow with Agentic RAG integration via KBRepository

	Features:
	- Agentic RAG via KBRepository integration
	- Always-on RAG with intelligent routing
	- Query analysis and optimization
	- Document grading and self-correction
	- Conversation file indexing and retrieval
	- Production-ready error handling
	"""

	def __init__(self, db_session: Session, config: Optional[WorkflowConfig] = None):
		"""Initialize ChatWorkflow with Agentic RAG"""
		self.start_time = time.time()
		color_logger.workflow_start(
			'ChatWorkflow Initialization with Agentic RAG',
			db_session_type=type(db_session).__name__,
			config_provided=config is not None,
		)

		self.db_session = db_session
		self.config = config or WorkflowConfig.from_env()
		# Pass db_session to config for CV Context Tool
		self.config.db_session = db_session
		print('^^' * 100, f'Config: {self.config.to_dict()}')

		color_logger.info(
			f'⚙️ {Colors.BOLD}CONFIG:{Colors.RESET}{Colors.CYAN} Agentic RAG workflow configuration loaded',
			Colors.CYAN,
			model_name=self.config.model_name,
			collection_name=self.config.collection_name,
		)

		self.compiled_graph = None

		try:
			# Initialize Agentic RAG workflow
			color_logger.info(
				f'🔧 {Colors.BOLD}INITIALIZING:{Colors.RESET}{Colors.YELLOW} Agentic RAG workflow services...',
				Colors.YELLOW,
			)

			# Create workflow with Unified features
			from .workflow import create_workflow

			workflow_instance = create_workflow(db_session, self.config)
			self.compiled_graph = workflow_instance.compiled_graph

			color_logger.success(
				'🚀 ChatWorkflow initialized with Agentic RAG functionality',
				initialization_time=time.time() - self.start_time,
				workflow_type='Agentic-RAG-KBRepository-enabled',
				services_count=1,
			)

		except Exception as e:
			color_logger.error(
				f'Agentic RAG workflow initialization failed: {str(e)}',
				error_type=type(e).__name__,
				fallback_mode=False,
			)

			raise NodeInterrupt(
				'Agentic RAG workflow initialization failed',
			)

		initialization_time = time.time() - self.start_time
		color_logger.info(
			'ChatWorkflow Initialization with Agentic RAG',
			initialization_time,
			workflow_ready=True,
			agentic_rag_enabled=True,
		)

	async def process_message(
		self,
		user_message: str,
		user_id: Optional[str] = None,
		session_id: Optional[str] = None,
		config_override: Optional[Dict[str, Any]] = None,
	) -> Dict[str, Any]:
		"""
		Process user message with Agentic RAG
		"""
		start_time = time.time()
		processing_session = session_id or 'default'

		color_logger.workflow_start(
			'Message Processing',
			user_id=user_id,
			session_id=processing_session,
			message_length=len(user_message),
		)

		try:
			from langchain_core.messages import HumanMessage

			initial_state = {'messages': [HumanMessage(content=user_message)]}
			color_logger.info(
				f'🏗️ {Colors.BOLD}STATE:{Colors.RESET}{Colors.MAGENTA} Initial state created',
				Colors.MAGENTA,
				message_type='HumanMessage',
			)

			# Prepare config
			runtime_config = {
				'configurable': {
					'thread_id': processing_session,
					'system_prompt': getattr(self.config, 'system_prompt', None),
					'use_rag': (self.config.rag_enabled if hasattr(self.config, 'rag_enabled') else True),
					**self.config.to_dict(),
				}
			}

			if config_override:
				runtime_config['configurable'].update(config_override)
				color_logger.info(
					f'🔧 {Colors.BOLD}CONFIG_OVERRIDE:{Colors.RESET}{Colors.YELLOW} Applied',
					Colors.YELLOW,
					overrides_count=len(config_override),
				)

			color_logger.info(
				f'⚙️ {Colors.BOLD}RUNTIME_CONFIG:{Colors.RESET}{Colors.DIM} Prepared',
				Colors.DIM,
				thread_id=processing_session,
				rag_enabled=runtime_config['configurable'].get('use_rag', False),
			)

			# Execute workflow
			color_logger.info(
				f'🚀 {Colors.BOLD}EXECUTING:{Colors.RESET}{Colors.BRIGHT_YELLOW} Agentic RAG workflow invocation',
				Colors.BRIGHT_YELLOW,
			)
			final_state = await self.compiled_graph.ainvoke(initial_state, config=runtime_config)

			# Extract response
			response = self._extract_response(final_state)

			color_logger.info(
				f'📤 {Colors.BOLD}RESPONSE:{Colors.RESET}{Colors.BRIGHT_GREEN} Generated',
				Colors.BRIGHT_GREEN,
				response_length=len(response),
				response_preview=(response[:100] + '...' if len(response) > 100 else response),
			)

			# Calculate processing metrics
			processing_time = time.time() - start_time
			rag_sources_count = len(final_state.get('rag_context', []))

			color_logger.performance_metric(
				'processing_time',
				f'{processing_time:.3f}',
				's',
				session_id=processing_session,
			)
			color_logger.performance_metric('rag_sources', rag_sources_count, '', session_id=processing_session)

			result = {
				'response': response,
				'state': final_state,
				'metadata': {
					'processing_time': processing_time,
					'rag_used': bool(final_state.get('rag_context')),
					'rag_sources': rag_sources_count,
					'user_id': user_id,
					'session_id': processing_session,
					'agentic_rag_used': final_state.get('agentic_rag_used', True),
				},
			}

			color_logger.info(
				'Message Processing',
				processing_time,
				success=True,
				rag_used=result['metadata']['rag_used'],
				response_generated=True,
				session_id=processing_session,
			)

			return result

		except Exception as e:
			processing_time = time.time() - start_time
			color_logger.error(
				f'Message processing failed: {str(e)}',
				error_type=type(e).__name__,
				processing_time=processing_time,
				session_id=processing_session,
			)

			# Create fallback response
			fallback_response = 'Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi của bạn. Vui lòng thử lại sau hoặc đặt câu hỏi khác.'

			color_logger.warning(
				f'🔄 {Colors.BOLD}FALLBACK:{Colors.RESET}{Colors.BRIGHT_YELLOW} Using fallback response',
				Colors.BRIGHT_YELLOW,
				fallback_length=len(fallback_response),
			)

			return {
				'response': fallback_response,
				'error': str(e),
				'metadata': {
					'processing_time': processing_time,
					'error_occurred': True,
				},
			}

	def _extract_response(self, final_state: Dict[str, Any]) -> str:
		"""Extract response từ final state"""
		color_logger.debug(
			'🔍 Extracting response from final state',
			state_keys=list(final_state.keys()),
			messages_count=len(final_state.get('messages', [])),
		)

		messages = final_state.get('messages', [])
		if not messages:
			color_logger.warning('No messages in final state')
			return 'Không thể tạo phản hồi.'

		# Get last AI message
		for i, message in enumerate(reversed(messages)):
			if hasattr(message, 'content') and message.content:
				content = message.content
				if content and content.strip():
					color_logger.debug(
						f'Response extracted from message #{len(messages) - i}',
						content_length=len(content),
						message_type=type(message).__name__,
					)
					return content

		color_logger.warning('No valid response content found in messages')
		return 'Phản hồi không khả dụng.'

	def get_workflow_info(self) -> Dict[str, Any]:
		"""Get workflow information"""
		color_logger.info(
			f'ℹ️ {Colors.BOLD}INFO_REQUEST:{Colors.RESET}{Colors.BRIGHT_WHITE} Getting Agentic RAG workflow information',
			Colors.BRIGHT_WHITE,
		)

		workflow_info = {
			'name': 'MoneyEZ Enhanced Chat Workflow with Agentic RAG',
			'version': '4.0.0',
			'description': 'Enhanced LangGraph workflow with Agentic RAG KBRepository integration',
			'features': [
				'Agentic RAG via KBRepository integration',
				'Always-on RAG with intelligent routing',
				'Query optimization and analysis',
				'Document grading and self-correction',
				'Conversation file indexing',
				'Basic calculation tools (+, -, *, /)',
				'Vietnamese financial expertise',
				'Production error handling',
				'Performance monitoring',
			],
			'nodes': ['agent', 'tools'],
			'config': self.config.to_dict() if hasattr(self.config, 'to_dict') else {},
			'compiled': self.compiled_graph is not None,
			'agentic_rag_enabled': True,
		}

		color_logger.info(
			f'📋 {Colors.BOLD}AGENTIC RAG WORKFLOW_INFO:{Colors.RESET}{Colors.BRIGHT_CYAN} Information compiled',
			Colors.BRIGHT_CYAN,
			version=workflow_info['version'],
			features_count=len(workflow_info['features']),
			nodes_count=len(workflow_info['nodes']),
		)

		return workflow_info


# Factory function cho easy initialization với Agentic RAG
def create_chat_workflow(db_session: Session, config: Optional[WorkflowConfig] = None) -> ChatWorkflow:
	"""
	Factory function để create ChatWorkflow instance với Agentic RAG
	"""
	color_logger.info('🏗️ Creating ChatWorkflow with Agentic RAG')
	return ChatWorkflow(db_session, config)


def get_compiled_workflow(db_session: Session, config: Optional[WorkflowConfig] = None):
	"""Get compiled workflow cho compatibility"""
	workflow = create_chat_workflow(db_session, config)
	return workflow.compiled_graph


color_logger.success('🚀 MoneyEZ Enhanced Chat Workflow with Agentic RAG module loaded!')
color_logger.info(
	f'📊 {Colors.BOLD}FEATURES:{Colors.RESET}{Colors.BRIGHT_MAGENTA} Agentic RAG KBRepository, Query Optimization, Knowledge Retrieval, Basic Tools',
	Colors.BRIGHT_MAGENTA,
)
color_logger.info(
	f'🔧 {Colors.BOLD}STATUS:{Colors.RESET}{Colors.BRIGHT_GREEN} Production-ready với comprehensive Agentic RAG functionality',
	Colors.BRIGHT_GREEN,
)
