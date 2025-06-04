"""
Chat Workflow Module - Agentic RAG Implementation with LangChain Qdrant
Enhanced workflow with intelligent query analysis, routing, and self-correction using LangChain Qdrant
"""

from datetime import datetime, timezone
import time
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.errors import NodeInterrupt
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver

from .tools.basic_tools import tools
from .state.workflow_state import AgentState
from .config.workflow_config import WorkflowConfig
from app.modules.agentic_rag.services.langchain_qdrant_service import (
	LangChainQdrantService,
)
from .utils.color_logger import get_color_logger, Colors
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

load_dotenv()

# Initialize colorful logger
color_logger = get_color_logger(__name__)


class ChatWorkflow:
	"""
	Enhanced Chat Workflow with LangChain Qdrant integration for Agentic RAG

	Features:
	- LangChain QdrantVectorStore integration
	- Always-on RAG with intelligent routing
	- Query analysis and optimization
	- Document grading and self-correction
	- Conversation file indexing and retrieval
	- Production-ready error handling
	"""

	def __init__(self, db_session: Session, config: Optional[WorkflowConfig] = None):
		"""Initialize ChatWorkflow with LangChain Qdrant services"""
		self.start_time = time.time()
		color_logger.workflow_start(
			'ChatWorkflow Initialization',
			db_session_type=type(db_session).__name__,
			config_provided=config is not None,
		)

		self.db_session = db_session
		self.config = config or WorkflowConfig.from_env()
		print('^^' * 100, f'Config: {self.config.to_dict()}')

		color_logger.info(
			f'⚙️ {Colors.BOLD}CONFIG:{Colors.RESET}{Colors.CYAN} Workflow configuration loaded',
			Colors.CYAN,
			model_name=self.config.model_name,
			collection_name=self.config.collection_name,
		)

		# Initialize services for RAG functionality
		self.langchain_qdrant_service = None

		self.compiled_graph = None

		try:
			# Initialize LangChain Qdrant services
			color_logger.info(
				f'🔧 {Colors.BOLD}INITIALIZING:{Colors.RESET}{Colors.YELLOW} LangChain Qdrant RAG services...',
				Colors.YELLOW,
			)

			self.langchain_qdrant_service = LangChainQdrantService(db_session)
			color_logger.success(
				'LangChainQdrantService initialized successfully',
				service='LangChainQdrantService',
				status='ready',
			)

			# Create workflow with LangChain Qdrant
			from .basic_workflow import create_agentic_rag_workflow

			self.compiled_graph = create_agentic_rag_workflow(db_session, self.config)

			color_logger.success(
				'🚀 ChatWorkflow initialized with LangChain Qdrant RAG functionality',
				initialization_time=time.time() - self.start_time,
				workflow_type='LangChain-Qdrant-RAG-enabled',
				services_count=3,
			)

		except Exception as e:
			color_logger.error(
				f'LangChain Qdrant RAG initialization failed: {str(e)}, using basic workflow',
				error_type=type(e).__name__,
				fallback_mode=True,
			)

			color_logger.warning(
				'🔄 Fallback to basic workflow activated',
				workflow_type='basic',
				rag_available=False,
			)
			raise NodeInterrupt(
				'LangChain Qdrant RAG initialization failed, falling back to basic workflow',
				error_type=type(e).__name__,
			)

		initialization_time = time.time() - self.start_time
		color_logger.workflow_complete(
			'ChatWorkflow Initialization',
			initialization_time,
			workflow_ready=True,
			rag_services_available=all([
				self.langchain_qdrant_service,
			]),
		)

	async def process_message(
		self,
		user_message: str,
		user_id: Optional[str] = None,
		session_id: Optional[str] = None,
		config_override: Optional[Dict[str, Any]] = None,
	) -> Dict[str, Any]:
		"""
		Process user message with LangChain Qdrant Agentic RAG
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
				f'🚀 {Colors.BOLD}EXECUTING:{Colors.RESET}{Colors.BRIGHT_YELLOW} LangChain Qdrant workflow invocation',
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
					'langchain_qdrant_used': final_state.get('langchain_qdrant_used', False),
				},
			}

			color_logger.workflow_complete(
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

	async def search_knowledge(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
		"""Search knowledge base directly using LangChain Qdrant"""
		start_time = time.time()
		color_logger.workflow_start(
			'Direct LangChain Qdrant Knowledge Search',
			query_length=len(query),
			top_k=top_k,
		)

		color_logger.info(
			f"🔍 {Colors.BOLD}LANGCHAIN SEARCH:{Colors.RESET}{Colors.BRIGHT_CYAN} '{query[:50]}...'",
			Colors.BRIGHT_CYAN,
		)

		try:
			if not self.langchain_qdrant_service:
				color_logger.error(
					'LangChain Qdrant service not available for knowledge search',
					service_available=bool(self.langchain_qdrant_service),
				)
				return []

			# Search using LangChain Qdrant
			documents = self.langchain_qdrant_service.similarity_search(
				query=query,
				collection_name=self.config.collection_name,
				top_k=top_k,
				score_threshold=0.6,
			)

			# Format results
			results = []
			for i, doc in enumerate(documents):
				result = {
					'content': doc.page_content,
					'metadata': doc.metadata,
					'score': doc.metadata.get('similarity_score', 0),
				}
				results.append(result)

				color_logger.debug(
					f'Search result #{i + 1}',
					score=result['score'],
					content_length=len(result['content']),
				)

			search_time = time.time() - start_time
			color_logger.workflow_complete(
				'Direct LangChain Qdrant Knowledge Search',
				search_time,
				results_count=len(results),
				avg_score=(sum(r['score'] for r in results) / len(results) if results else 0),
			)

			return results

		except Exception as e:
			color_logger.error(
				f'Error searching LangChain Qdrant knowledge: {str(e)}',
				error_type=type(e).__name__,
				query_preview=query[:50],
			)
			return []

	async def index_documents(self, documents: List[Dict[str, Any]], collection_name: Optional[str] = None) -> Dict[str, Any]:
		"""Index documents to knowledge base using LangChain Qdrant"""
		start_time = time.time()
		color_logger.workflow_start(
			'LangChain Qdrant Document Indexing',
			document_count=len(documents),
			target_collection=collection_name or self.config.collection_name,
		)

		try:
			if not self.langchain_qdrant_service:
				color_logger.error('LangChain Qdrant service not available for indexing')
				return {'error': 'LangChain Qdrant service not available'}

			from langchain_core.documents import Document

			# Convert to Document objects
			doc_objects = []
			total_content_length = 0
			for i, doc in enumerate(documents):
				content = doc.get('content', '')
				metadata = doc.get('metadata', {})
				doc_objects.append(Document(page_content=content, metadata=metadata))
				total_content_length += len(content)

				color_logger.debug(
					f'Document #{i + 1} prepared for LangChain indexing',
					content_length=len(content),
					metadata_keys=list(metadata.keys()),
				)

			color_logger.info(
				f'📊 {Colors.BOLD}LANGCHAIN INDEXING_PREP:{Colors.RESET}{Colors.MAGENTA} Documents prepared',
				Colors.MAGENTA,
				total_docs=len(doc_objects),
				total_content_length=total_content_length,
			)

			# Index using LangChain Qdrant
			collection = collection_name or self.config.collection_name
			result = self.langchain_qdrant_service.index_documents(doc_objects, collection)

			indexing_time = time.time() - start_time
			indexed_count = result.get('total_indexed', 0)

			color_logger.success(
				f'Documents indexed successfully with LangChain Qdrant',
				indexed_count=indexed_count,
				collection=collection,
				indexing_time=indexing_time,
			)

			color_logger.workflow_complete(
				'LangChain Qdrant Document Indexing',
				indexing_time,
				success=True,
				indexed_count=indexed_count,
			)

			return result

		except Exception as e:
			color_logger.error(
				f'Error indexing documents with LangChain Qdrant: {str(e)}',
				error_type=type(e).__name__,
				document_count=len(documents),
			)
			return {'error': str(e)}

	async def get_knowledge_stats(self) -> Dict[str, Any]:
		"""Get knowledge base statistics using LangChain Qdrant"""
		color_logger.info(
			f'📊 {Colors.BOLD}LANGCHAIN STATS_REQUEST:{Colors.RESET}{Colors.CYAN} Getting knowledge base stats',
			Colors.CYAN,
		)

		try:
			if not self.langchain_qdrant_service:
				color_logger.warning('LangChain Qdrant service not available for stats')
				return {'error': 'LangChain Qdrant service not available'}

			stats = self.langchain_qdrant_service.get_collection_stats(self.config.collection_name)

			color_logger.info(
				f'📈 {Colors.BOLD}LANGCHAIN STATS_RETRIEVED:{Colors.RESET}{Colors.BRIGHT_GREEN} Collection statistics',
				Colors.BRIGHT_GREEN,
				collection=self.config.collection_name,
				vectors_count=stats.get('vectors_count', 0),
			)

			return stats

		except Exception as e:
			color_logger.error(
				f'Error getting LangChain Qdrant knowledge stats: {str(e)}',
				error_type=type(e).__name__,
			)
			return {'error': str(e)}

	async def health_check(self) -> Dict[str, Any]:
		"""Comprehensive health check for LangChain Qdrant"""
		start_time = time.time()
		color_logger.workflow_start('LangChain Qdrant Health Check', comprehensive=True)

		try:
			health_data = {
				'status': 'healthy',
				'components': {},
				'timestamp': time.time(),
			}

			# Check LangChain Qdrant Service
			color_logger.info(
				f'🔍 {Colors.BOLD}CHECKING:{Colors.RESET}{Colors.YELLOW} LangChain Qdrant Service health',
				Colors.YELLOW,
			)
			if self.langchain_qdrant_service:
				try:
					collections = self.langchain_qdrant_service.list_collections()
					health_data['components']['langchain_qdrant'] = {
						'status': 'healthy',
						'collections': collections,
					}
					color_logger.health_check(
						'LangChainQdrantService',
						'healthy',
						collections_count=len(collections),
					)
				except Exception as e:
					health_data['components']['langchain_qdrant'] = {
						'status': 'unhealthy',
						'error': str(e),
					}
					color_logger.health_check('LangChainQdrantService', 'unhealthy', error=str(e))
			else:
				health_data['components']['langchain_qdrant'] = {'status': 'not_initialized'}
				color_logger.health_check('LangChainQdrantService', 'not_initialized')

			# Check Knowledge Retriever
			color_logger.info(
				f'🔍 {Colors.BOLD}CHECKING:{Colors.RESET}{Colors.YELLOW} KnowledgeRetriever health',
				Colors.YELLOW,
			)

			# Check workflow
			workflow_status = 'healthy' if self.compiled_graph else 'unhealthy'
			health_data['components']['workflow'] = {
				'status': workflow_status,
				'compiled': self.compiled_graph is not None,
			}
			color_logger.health_check('Workflow', workflow_status, compiled=bool(self.compiled_graph))

			# Determine overall status
			component_statuses = [comp.get('status') for comp in health_data['components'].values()]
			if any(status == 'unhealthy' for status in component_statuses):
				health_data['status'] = 'degraded'
			elif any(status == 'not_initialized' for status in component_statuses):
				health_data['status'] = 'partial'

			check_time = time.time() - start_time
			color_logger.workflow_complete(
				'LangChain Qdrant Health Check',
				check_time,
				overall_status=health_data['status'],
				components_checked=len(health_data['components']),
			)

			return health_data

		except Exception as e:
			color_logger.error(
				f'LangChain Qdrant health check failed: {str(e)}',
				error_type=type(e).__name__,
			)
			return {'status': 'unhealthy', 'error': str(e), 'timestamp': time.time()}

	def get_workflow_info(self) -> Dict[str, Any]:
		"""Get workflow information"""
		color_logger.info(
			f'ℹ️ {Colors.BOLD}INFO_REQUEST:{Colors.RESET}{Colors.BRIGHT_WHITE} Getting LangChain Qdrant workflow information',
			Colors.BRIGHT_WHITE,
		)

		# Check which services are available
		services_status = {
			'langchain_qdrant_service': self.langchain_qdrant_service is not None,
		}

		workflow_info = {
			'name': 'MoneyEZ Enhanced Chat Workflow with LangChain Qdrant',
			'version': '3.0.0',
			'description': 'Enhanced LangGraph workflow with LangChain QdrantVectorStore integration',
			'features': [
				'LangChain QdrantVectorStore integration',
				'Always-on Agentic RAG',
				'Query optimization and analysis',
				'Document grading and self-correction',
				'Conversation file indexing',
				'Basic calculation tools (+, -, *, /)',
				'Vietnamese financial expertise',
				'Production error handling',
				'Performance monitoring',
			],
			'nodes': (
				[
					'query_analysis',
					'agentic_retrieve',
					'grade_documents',
					'agent',
					'tools',
				]
				if any(services_status.values())
				else ['agent', 'tools']
			),
			'services': services_status,
			'config': self.config.to_dict() if hasattr(self.config, 'to_dict') else {},
			'compiled': self.compiled_graph is not None,
			'langchain_qdrant_enabled': True,
		}

		color_logger.info(
			f'📋 {Colors.BOLD}LANGCHAIN WORKFLOW_INFO:{Colors.RESET}{Colors.BRIGHT_CYAN} Information compiled',
			Colors.BRIGHT_CYAN,
			version=workflow_info['version'],
			features_count=len(workflow_info['features']),
			nodes_count=len(workflow_info['nodes']),
			services_available=sum(services_status.values()),
		)

		return workflow_info


# Factory function cho easy initialization với LangChain Qdrant
def create_chat_workflow(db_session: Session, config: Optional[WorkflowConfig] = None) -> ChatWorkflow:
	"""
	Factory function để create ChatWorkflow instance với LangChain Qdrant

	Args:
	        db_session: Database session
	        config: Optional workflow configuration

	Returns:
	        ChatWorkflow instance with LangChain Qdrant integration
	"""
	return ChatWorkflow(db_session, config)


def get_compiled_workflow(db_session: Session, config: Optional[WorkflowConfig] = None):
	"""
	Get compiled workflow instance cho direct use
	"""
	workflow = create_chat_workflow(db_session, config)
	return workflow.compiled_graph


color_logger.success('🚀 MoneyEZ Enhanced Chat Workflow with LangChain Qdrant module loaded!')
color_logger.info(
	f'📊 {Colors.BOLD}FEATURES:{Colors.RESET}{Colors.BRIGHT_MAGENTA} LangChain QdrantVectorStore, Agentic RAG, Query Optimization, Knowledge Retrieval, Basic Tools',
	Colors.BRIGHT_MAGENTA,
)
color_logger.info(
	f'🔧 {Colors.BOLD}STATUS:{Colors.RESET}{Colors.BRIGHT_GREEN} Production-ready với comprehensive LangChain Qdrant RAG functionality',
	Colors.BRIGHT_GREEN,
)
